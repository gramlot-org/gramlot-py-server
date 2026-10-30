"""Kajenn-only local HTTP experiment, separate from ordinary RPC routing."""
import asyncio

from genro_routes import route
from kajenn.streaming import StreamingResponse
from gramlot.server import InvalidRequest
from gramlot.server.gramlot_server import PageExpired, NotAuthenticated, NotAuthorized
from gramlot.server.selection_trial import prepare_selection_trial, selection_trial_lines
from gramlot_py_server.kajenn import Application


class SelectionTrialApplication(Application):
    @route(media_type='text/html')
    async def index(self, *segments, _request, body_raw=None, **query):
        if _request.path != f'{self.mount_path}/gramlot/selection-trial':
            return await super().index(*segments, _request=_request, body_raw=body_raw, **query)
        _request.response.set_header('Cache-Control', 'no-store')
        if _request.method != 'POST':
            _request.response.status_code = 405
            _request.response.set_header('Allow', 'POST')
            return self.result_wrapper('Method not allowed', media_type='text/plain')
        if str(_request.content_type or '').split(';', 1)[0].strip() != 'application/json':
            _request.response.status_code = 415
            return self.result_wrapper('Expected application/json', media_type='text/plain')
        try:
            async with self._operation():
                text = self.gramlot_server.decode_body(await self.read_body(body_raw))
                request_id, result = await prepare_selection_trial(
                    self.gramlot_server, text, owner=_request.cookies.get(self.OWNER_COOKIE),
                    identity=_request.avatar())
        except (InvalidRequest, PageExpired, NotAuthenticated, NotAuthorized):
            _request.response.status_code = 400
            return self.result_wrapper('Invalid or unauthorized selection request', media_type='text/plain')

        async def chunks():
            # Bound writes, not records: avoid one ASGI send/syscall per small line.
            pending = bytearray()
            for line in selection_trial_lines(request_id, result):
                pending.extend(line)
                if len(pending) >= 65536:
                    yield bytes(pending)
                    pending.clear()
                    await asyncio.sleep(0)
            if pending:
                yield bytes(pending)

        return StreamingResponse(chunks(), media_type='application/x-ndjson',
                                 headers={'Cache-Control': 'no-store'})


def serve(pages, *, host='127.0.0.1', port=61401, **options):
    """Serve the local Base pages with their JSONL selection route enabled."""
    from kajenn import AsgiServer
    from kajenn.config.templates import DefaultConfiguration

    class Site(DefaultConfiguration):
        def applications_section(self, cfg):
            cfg.applications().application(code='pages', mount='',
                app_class=SelectionTrialApplication, pages=pages, **options).request(body='raw')

    AsgiServer(config=Site).serve(host=host, port=port)
