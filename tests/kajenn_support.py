"""Lifespan and authentication fixtures for in-process Kajenn sites."""
import asyncio
from contextlib import asynccontextmanager

from cryptography.fernet import Fernet
from genro_storage import StorageManager
from kajenn import AsgiServer, AuthApplicationBase
from kajenn.config.templates import DefaultConfiguration

from gramlot_py_server.kajenn import Application


@asynccontextmanager
async def running_kajenn(server):
    """Let one site finish activation before serving any test clients."""
    incoming, outgoing = asyncio.Queue(), asyncio.Queue()
    lifespan = asyncio.create_task(server({"type": "lifespan"}, incoming.get, outgoing.put))
    try:
        await incoming.put({"type": "lifespan.startup"})
        started = await asyncio.wait_for(outgoing.get(), 30)
        assert started["type"] == "lifespan.startup.complete", started
        try:
            async with asyncio.timeout(30):
                while not all(server.is_enabled(code) for code in server.applications):
                    await asyncio.sleep(0.01)
            yield server
        finally:
            await incoming.put({"type": "lifespan.shutdown"})
            await asyncio.wait_for(lifespan, 30)
            assert outgoing.get_nowait()["type"] == "lifespan.shutdown.complete"
    finally:
        if not lifespan.done():
            lifespan.cancel()
        await asyncio.gather(lifespan, return_exceptions=True)


def auth_site(pages, storage_path, *, mount="page", websocket=False):
    """Serve Gramlot pages with two confirmed users in an isolated Kajenn auth store."""
    key = Fernet.generate_key().decode()

    class Site(DefaultConfiguration):
        def storage_section(self, cfg):
            storage = cfg.storage(app=StorageManager, storage_key=key)
            for name in ("site", "home"):
                storage.local(name=name, base_path=str(storage_path))

        def applications_section(self, cfg):
            apps = cfg.applications()
            apps.application(code="_auth", app_class=AuthApplicationBase)
            apps.application(code="pages", mount=mount, app_class=Application,
                             pages=pages, websocket=websocket).request(body="raw")

    server = AsgiServer(config=Site)
    store = server.applications["_auth"].store
    for identity, tags in (("ada", ["admin", "staff"]), ("bob", ["staff"])):
        store.save_user({
            "identity": identity, "password_hash": store.hash_password(f"{identity}-secret"),
            "tags": tags, "groups": [], "status": "confirmed",
        })
    return server
