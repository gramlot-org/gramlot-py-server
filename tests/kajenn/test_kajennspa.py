"""Gramlot's browser protocol against the opt-in Kajenn SPA server."""

from contextlib import asynccontextmanager

import httpx
import pytest
from cryptography.fernet import Fernet
from genro_tytx import from_tytx, to_tytx
import kajenn
from gramlot.server import GramlotServer
from kajenn import AsgiServer
from kajenn_support import running_kajenn
from page_store_checks import channel, open_page

pytestmark = pytest.mark.skipif(
    not hasattr(kajenn, "SpaApplicationBase") or not hasattr(GramlotServer, "register_page"),
    reason="kajennspa requires Kajenn SPA and Gramlot lifecycle hooks",
)

RECIPE = """
from genro_routes import route
from pathlib import Path
from genro_storage import StorageManager
from kajenn import AuthApplicationBase
from kajenn.config.templates import DefaultConfiguration
from gramlot_py_server.kajennspa import Application

class SiteApp(Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_pages("second", PAGES)

    @route()
    def total(self, n: int):
        return {"answer": n + 1}

class Site(DefaultConfiguration):
    def storage_section(self, cfg):
        storage = cfg.storage(app=StorageManager, storage_key=STORAGE_KEY)
        for mount in ("site", "home"):
            storage.local(name=mount, base_path=str(Path(__file__).parent))
    def applications_section(self, cfg):
        apps = cfg.applications()
        apps.application(code="_auth", app_class=AuthApplicationBase).store(mount="home")
        apps.application(code="demo", app_class=SiteApp, pages=PAGES, **OPTIONS)
"""

PAGE = """
from gramlot import endpoint, PageStore as Shared
from gramlot_py_server.kajennspa import Page as BasePage, PageStore as BaseStore

class PageStore(BaseStore):
    def main(self, root):
        shared = self.shared_store(("test", "room"), Shared)
        self.bind_path("editor", shared, "text", writable=True, authorize=lambda: True)

    def on_user_changed(self, previous, current):
        self.data.set_item("signed_in_as", current.user)

class Page(BasePage):
    calls = 0
    def main(self, root):
        pane = root.div(datapath="view")
        pane.div("Live SPA", id="live-spa")
        pane.dataBinder(".editor", "editor")
        pane.input(id="editor", value="^.editor")
        pane.span("^.editor", id="mirror")

    @endpoint
    def details(self):
        self.calls += 1
        return {"app": self.application.code, "count": self.calls,
                "text": self.store.data.get_item("editor"), "user": self.state.user,
                "rebound": self.store.data.get_item("signed_in_as")}
"""


@asynccontextmanager
async def running(tmp_path, **options):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "index.py").write_text(PAGE)
    config = tmp_path / "config.py"
    config.write_text(
        RECIPE.replace("PAGES", repr(str(pages)))
        .replace("OPTIONS", repr(options))
        .replace("STORAGE_KEY", repr(Fernet.generate_key().decode()))
    )
    server = AsgiServer(config=str(config))
    async with running_kajenn(server):
        yield server


async def details(client, pid, branch="pages"):
    envelope = {"pageId": pid, "id": "test", "name": "details", "contentType": "data", "params": {}}
    response = await client.post(
        f"/demo/{branch}/gramlot/rpc",
        content=to_tytx(envelope),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 200, response.text
    return from_tytx(response.text)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "options",
    [{}, {"persistent": False}, {"spawner": "subprocess"}],
    ids=["local", "per-request", "subprocess"],
)
async def test_pages_and_shared_store(tmp_path, options):
    async with running(tmp_path, **options) as server:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=server), base_url="http://test:8000"
        ) as client:
            assert (await client.post("/demo/total", json={"n": 2})).json() == {"answer": 3}
            prefix = "/demo/pages"
            first, cookie = await open_page(client, prefix)
            second, _ = await open_page(client, prefix)
            assert first != second
            a = (await details(client, first))["value"]
            assert a["count"] == 1 and a["app"] == "demo"
            assert (await details(client, first))["value"]["count"] == (
                1 if options.get("persistent") is False else 2
            )
            assert "error" in await details(client, first, "second")
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=server), base_url="http://test:8000"
            ) as outsider:
                assert "error" in await details(outsider, first)
            async with channel(server, cookie, first, prefix=prefix) as (opened, send, recv):
                assert opened["type"] == "websocket.accept", opened
                await send({"op": "subscribe", "binderId": "a", "path": "editor"})
                assert from_tytx((await recv())["text"])["op"] == "snapshot"
                async with channel(server, cookie, second, prefix=prefix) as (
                    other,
                    send_b,
                    recv_b,
                ):
                    assert other["type"] == "websocket.accept"
                    await send_b({"op": "subscribe", "binderId": "b", "path": "editor"})
                    await recv_b()
                    await send(
                        {
                            "op": "change",
                            "binderId": "a",
                            "path": "",
                            "evt": "upd_value",
                            "value": "saved",
                            "attr": {},
                        }
                    )
                    assert from_tytx((await recv_b())["text"])["value"] == "saved"
                assert (await details(client, second))["value"]["text"] == "saved"
            if "spawner" not in options:
                registry = server.applications["demo"].registry
                registry.release_page_instance(
                    second, connection_id=a["user"].removeprefix("guest_")
                )
                restored = (await details(client, second))["value"]
                assert restored["count"] == 1 and restored["text"] == "saved"
            async with channel(server, cookie, second, prefix=prefix) as (again, send, recv):
                assert again["type"] == "websocket.accept"
                auth = server.applications["_auth"].store
                auth.save_user(
                    {
                        "identity": "mario",
                        "password_hash": auth.hash_password("pw"),
                        "groups": [],
                        "tags": [],
                        "status": "confirmed",
                    }
                )
                login = await client.post(
                    "/_auth/login", json={"identity": "mario", "password": "pw"}
                )
                assert login.status_code == 200, login.text
                for pid in (first, second):
                    result = (await details(client, pid))["value"]
                    assert result["user"] == result["rebound"] == "mario"
                    assert result["text"] is None
                await send({"op": "subscribe", "binderId": "old", "path": "editor"})
                assert (await recv())["code"] == 1008
            cookie = "; ".join(f"{key}={value}" for key, value in client.cookies.items())
            async with channel(server, cookie, second, prefix=prefix) as (fresh, send, recv):
                assert fresh["type"] == "websocket.accept", fresh
                logout = await client.post(
                    "/_auth/logout", params={"session_id": client.cookies["session_id"]}
                )
                assert logout.status_code == 200, logout.text
                await send({"op": "subscribe", "binderId": "x", "path": "editor"})
                assert (await recv())["code"] == 1008
