"""The same Gramlot channel contract through Kajenn's native WebSocket."""
import asyncio
import base64
from contextlib import AsyncExitStack
from functools import partial
import httpx
import pytest
import pytest_asyncio
from genro_tytx import from_tytx
from kajenn import AsgiServer
from kajenn_support import auth_site, running_kajenn
from kajenn.config.templates import DefaultConfiguration
from gramlot_py_server.kajenn import Application
from page_store_checks import PageStoreChecks, PAGES, channel, open_page, rpc


class _Site:
    def __init__(self, pages, *, lifespans, mount_path="", **options):
        class Configuration(DefaultConfiguration):
            def applications_section(self, cfg):
                applications = cfg.applications()
                applications.application(
                    code="pages", mount=mount_path.strip("/"),
                    app_class=Application, pages=pages, **options,
                ).request(body="raw")
        self._lifespans = lifespans
        self._startup = asyncio.Lock()
        self.server = AsgiServer(config=Configuration)
        self.application = self.server.applications["pages"]
        self.gramlot_server = self.application.gramlot_server
        self._store_channel = self.application._store_channel

    async def __call__(self, scope, receive, send):
        # The shared adapter checks construct sites synchronously.
        async with self._startup:
            if not self.server.lifespan.started:
                await self._lifespans.enter_async_context(running_kajenn(self.server))
        await self.server(scope, receive, send)


class KajennChannelSites:
    @pytest_asyncio.fixture(autouse=True)
    async def channel_sites(self):
        async with AsyncExitStack() as lifespans:
            self.create_application = partial(_Site, lifespans=lifespans)
            yield


class TestPageStore(KajennChannelSites, PageStoreChecks):
    pass


@pytest.mark.asyncio
@pytest.mark.parametrize("credentials,outcome", [
    (None, "not_authenticated"), ("bob:bob-secret", "not_authorized"),
    ("ada:ada-secret", "allowed"),
])
async def test_native_authentication_and_socket_registry(tmp_path, tmp_path_factory, credentials, outcome):
    (tmp_path / "index.py").write_text("""from gramlot import Page as BasePage, endpoint
class Page(BasePage):
    def main(self, root): root.h1('Auth')
    @endpoint(auth='admin')
    def restricted(self): return 'allowed'
""")
    app = auth_site(tmp_path, tmp_path_factory.mktemp("auth"), mount="", websocket=True)
    headers = () if credentials is None else (
        (b"authorization", b"Basic " + base64.b64encode(credentials.encode())),
    )
    async with running_kajenn(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        page_id, cookie = await open_page(client)
        async with channel(app, cookie, page_id, headers=headers) as (opened, send, receive):
            assert opened["type"] == "websocket.accept"
            assert len(app.websockets.snapshot()) == 1
            await send(rpc("restricted", "restricted"))
            result = from_tytx((await receive())["text"])
            assert (result["value"] if "value" in result else result["error"]["code"]) == outcome
        assert app.websockets.snapshot() == []


@pytest.mark.asyncio
async def test_native_channel_disabled_by_default():
    async with AsyncExitStack() as lifespans:
        app = _Site(PAGES, lifespans=lifespans)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await open_page(client)
            async with channel(app, cookie, page_id) as (opened, _, _):
                assert opened["type"] == "websocket.close" and opened["code"] == 1008
            assert app.server.websockets.snapshot() == []
