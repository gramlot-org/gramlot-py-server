"""Django delivery of packaged runtime files, without FastAPI or static discovery."""
from pathlib import Path
from django.http import FileResponse, Http404
from django.urls import path
from django.views.decorators.http import require_safe
from gramlot.hosting import RuntimeAssets as SharedRuntimeAssets


class RuntimeAssets(SharedRuntimeAssets):
    @property
    def urls(self):
        # Django's collection URLconf is already mounted at self.prefix.
        return [
            path(mount.url_prefix[len(self.prefix) + 1:] + '<path:asset>',
                 self.asset_view(mount.directory, immutable=mount.immutable),
                 name=f'runtime-{mount.name}')
            for mount in self.asset_mounts()
        ]

    def asset_view(self, directory, *, immutable=False):
        directory = Path(directory).resolve()
        @require_safe
        def serve(request, asset):
            target = (directory / asset).resolve()
            if not target.is_relative_to(directory) or not target.is_file():
                raise Http404
            response = FileResponse(target.open('rb'))
            if target.suffix in ('.js', '.mjs'):
                response['Content-Type'] = 'text/javascript'
            if immutable:
                response['Cache-Control'] = 'public, max-age=31536000, immutable'
            else:
                response['Cache-Control'] = 'no-cache'
            return response
        return serve
