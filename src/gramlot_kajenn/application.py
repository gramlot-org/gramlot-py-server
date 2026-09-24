# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Genro ASGI transport for the experimental Gramlot page contract."""
from mimetypes import guess_type
import logging
import re

from genro_asgi import BaseApplication, Response
from gramlot.builder import GramlotBuilder
from gramlot.contrib._shared.pages import PageRegistry, ServiceParameterError
from gramlot.contrib._shared.runtime import RuntimeAssets, render_document
from gramlot.transport import TYTX_FORMAT, TYTX_MEDIA_TYPE, from_tytx, to_tytx

log = logging.getLogger(__name__)


class PageCollection(PageRegistry):
    """Fresh page invocations on the owning Genro ASGI server's worker pool."""

    def __init__(self, application, directory, **options):
        self.application = application
        super().__init__(directory, **options)

    async def run_sync(self, function, *args):
        if self.application.server is None:
            raise RuntimeError('Mount this application on a Genro ASGI server first')
        return await self.application.server.run_sync(function, *args)


class GramlotApplication(BaseApplication):
    """Mount on BaseServer/AsgiServer; the server strips the mount from scope.path.

    Pages and their decorated RPC services are public unless the owning host adds
    authentication/authorization. This adapter does not infer legacy permissions.
    """

    registry_class = PageCollection

    def __init__(self, directory, *, mount='page', code='gramlot', title='Gramlot',
                 development=False, **registry_options):
        if not re.fullmatch(r'[a-z][a-z0-9_-]*', mount):
            raise ValueError('mount must be a single lowercase URL segment')
        super().__init__(code=code, mount=mount)
        self.title = title
        self.prefix = '/' + mount
        self.pages = self.registry_class(
            self, directory, prefix=self.prefix, title=title, **registry_options,
        )
        self.runtime = RuntimeAssets(self.prefix, development=development)
        self.template = self.runtime.document_template()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            raise ValueError('GramlotApplication supports HTTP only')
        response = await self.dispatch(scope, receive)
        await response(scope, receive, send)

    def document(self, name=None):
        startup = {'recipe': f'{self.prefix}/recipe', 'inspector': False}
        if name is not None:
            page = self.pages.require_page(name)
            startup = {
                'recipe': None, 'rpc': f'{self.prefix}/{name}/rpc', 'main': 'main',
                'inspector': {'launcher': False} if page.example_view else page.source_inspection,
                'exampleView': page.example_view,
            }
        return Response(render_document(self.template, self.runtime, self.title, startup),
                        media_type='text/html')

    @staticmethod
    def typed(value, status=200):
        return Response(to_tytx(value, TYTX_FORMAT), status_code=status, media_type=TYTX_MEDIA_TYPE)

    @classmethod
    def error(cls, kind, message, status):
        return cls.typed({'ok': False, 'error': {'kind': kind, 'message': message}}, status)

    async def dispatch(self, scope, receive):
        path = scope.get('path', '/')
        verb = scope.get('method', 'GET').upper()
        if path.startswith('/_runtime/'):
            if verb not in ('GET', 'HEAD'):
                return Response(status_code=405, headers={'allow': 'GET, HEAD'})
            return await self.asset(path, head=verb == 'HEAD')
        parts = path.strip('/').split('/') if path.strip('/') else []
        is_rpc = len(parts) in (3, 4) and parts[1] == 'rpc'
        if verb != ('POST' if is_rpc else 'GET'):
            return Response(status_code=405, headers={'allow': 'POST' if is_rpc else 'GET'})
        if not parts:
            return self.document()
        if parts == ['recipe']:
            builder = GramlotBuilder('index')
            links = builder.root.nav(aria_label='Pages').ul()
            for name, page in self.pages.pages.items():
                links.li().a(getattr(page, 'title', name), href=f'{self.prefix}/{name}/')
            return self.typed(builder.source)
        name = parts[0]
        if name not in self.pages.pages:
            return self.error('page', 'Page not found', 404)
        if len(parts) == 1:
            return self.document(name)
        if parts[1:] == ['recipe']:
            try:
                return self.typed(await self.pages.invoke(name, 'source', 'main', {}, scope))
            except Exception:
                log.exception('Gramlot Source invocation failed')
                return self.error('application', 'Source invocation failed', 500)
        if not is_rpc:
            return self.error('path', 'Not found', 404)
        role, method = ('data', parts[2]) if len(parts) == 3 else (parts[2], parts[3])
        if role not in ('source', 'data'):
            return self.error('role', 'Unknown service role', 404)
        registered = self.pages.registered_method(name, method)
        if registered is None:
            return self.error('method', 'Service not found', 404)
        if registered.role != role:
            return self.error('role', 'Service role mismatch', 409)
        headers = {key.lower(): value for key, value in scope.get('headers', [])}
        media = headers.get(b'content-type', b'').split(b';')[0].strip().lower()
        if media != TYTX_MEDIA_TYPE.encode():
            return self.error('request', 'Expected TYTX JSON', 415)
        body = bytearray()
        while True:
            event = await receive()
            if event['type'] == 'http.disconnect':
                return self.error('request', 'Disconnected', 400)
            body.extend(event.get('body', b''))
            if len(body) > 1024 * 1024:
                return self.error('request', 'Request too large', 413)
            if not event.get('more_body', False):
                break
        try:
            params = from_tytx(body.decode('utf-8'), transport=TYTX_FORMAT)
            if not isinstance(params, dict):
                raise TypeError('Expected a mapping')
        except Exception:
            return self.error('request', 'Invalid TYTX parameter mapping', 400)
        try:
            result = await self.pages.invoke(name, role, method, params, scope)
            return self.typed({'ok': True, 'result': result})
        except ServiceParameterError as error:
            return self.error('parameters', str(error), 422)
        except Exception:
            log.exception('Gramlot service invocation failed')
            return self.error('application', 'Service invocation failed', 500)

    async def asset(self, path, *, head=False):
        absolute = self.prefix + path
        for mount in self.runtime.asset_mounts():
            if not absolute.startswith(mount.url_prefix):
                continue
            root = mount.directory.resolve()
            target = (root / absolute[len(mount.url_prefix):]).resolve()
            if not target.is_relative_to(root) or not target.is_file():
                break
            content = b'' if head else await self.pages.run_sync(target.read_bytes)
            media = ('text/javascript' if target.suffix in ('.js', '.mjs') else
                     guess_type(target.name)[0] or 'application/octet-stream')
            cache = 'public, max-age=31536000, immutable' if mount.immutable else 'no-cache'
            return Response(content, media_type=media, headers={'cache-control': cache})
        return Response('Not found', status_code=404, media_type='text/plain')
