"""FastAPI delivery of the shared packaged browser runtime."""
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from gramlot.hosting import RuntimeAssets as SharedRuntimeAssets

class BrowserStaticFiles(StaticFiles):
    """Only successful responses from an immutable build receive long caching."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code in (200, 206, 304):
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        return response


class SourceStaticFiles(StaticFiles):
    """Development assets must be revalidated even within one host session."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers['Cache-Control'] = 'no-cache'
        return response


class RuntimeAssets(SharedRuntimeAssets):
    def mount(self, app: FastAPI) -> None:
        for mount in self.asset_mounts():
            if mount.immutable:
                application = GZipMiddleware(
                    BrowserStaticFiles(directory=mount.directory), minimum_size=500,
                )
            else:
                application = SourceStaticFiles(directory=mount.directory)
            app.mount(
                mount.url_prefix.rstrip('/'), application,
                name=f'{self.prefix}-{mount.name}',
            )
