"""The same Gramlot channel contract through Kajenn's native WebSocket."""
import base64
import httpx
import pytest
from genro_tytx import from_tytx
from kajenn import AsgiServer
from kajenn.server_app import ServerApplication
from kajenn.config.templates import DefaultConfiguration
from gramlot_py_server.kajenn import Application
from page_store_checks import PageStoreChecks, PAGES, channel, open_page, rpc


class _Site:
    def __init__(self, pages, *, mount_path="", auth=False, **options):
        class Configuration(DefaultConfiguration):
            def applications_section(self, cfg):
                applications = cfg.applications()
                if auth:
                    credentials = cfg.authentication().credentials()
                    credentials.basic_user(username="ada", password="ada-secret", tags="admin,staff")
                    credentials.basic_user(username="bob", password="bob-secret", tags="staff")
                    applications.application(code="_server", app_class=ServerApplication)
                applications.application(
                    code="pages", mount=mount_path.strip("/"),
                    app_class=Application, pages=pages, **options,
                ).request(body="raw")
        self.server = AsgiServer(config=Configuration)
        self.application = self.server.applications["pages"]
        self.gramlot_server = self.application.gramlot_server
        self._store_channel = self.application._store_channel

    async def __call__(self, scope, receive, send):
        await self.server(scope, receive, send)


class TestPageStore(PageStoreChecks):
    create_application = staticmethod(_Site)


@pytest.mark.asyncio
@pytest.mark.parametrize("credentials,outcome", [
    (None, "not_authenticated"), ("bob:bob-secret", "not_authorized"),
    ("ada:ada-secret", "allowed"),
])
async def test_native_authentication_and_socket_registry(tmp_path, credentials, outcome):
    (tmp_path / "index.py").write_text("""from gramlot import Page as BasePage, endpoint
class Page(BasePage):
    def main(self, root): root.h1('Auth')
    @endpoint(auth='admin')
    def restricted(self): return 'allowed'
""")
    app = _Site(tmp_path, websocket=True, auth=True)
    headers = () if credentials is None else (
        (b"authorization", b"Basic " + base64.b64encode(credentials.encode())),
    )
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        page_id, cookie = await open_page(client)
        async with channel(app, cookie, page_id, headers=headers) as (opened, send, receive):
            assert opened["type"] == "websocket.accept"
            assert len(app.server.websockets.snapshot()) == 1
            await send(rpc("restricted", "restricted"))
            result = from_tytx((await receive())["text"])
            assert (result["value"] if "value" in result else result["error"]["code"]) == outcome
        assert app.server.websockets.snapshot() == []
    app.server.pool.shutdown(wait=True)


@pytest.mark.asyncio
async def test_native_channel_disabled_by_default():
    app = _Site(PAGES)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        page_id, cookie = await open_page(client)
        async with channel(app, cookie, page_id) as (opened, _, _):
            assert opened["type"] == "websocket.close" and opened["code"] == 1008
        assert app.server.websockets.snapshot() == []
    app.gramlot_server.close_all()
