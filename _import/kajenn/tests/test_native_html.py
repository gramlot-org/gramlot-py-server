import re

import httpx
import pytest
from genro_tytx import from_tytx
from kajenn import AsgiServer
from kajenn.config.templates import DefaultConfiguration

from gramlot_kajenn import KajennNativeHtmlApplication


def test_native_public_api_excludes_generic_asgi():
    import gramlot_kajenn

    assert gramlot_kajenn.__all__ == ["KajennNativeHtmlApplication"]
    assert not hasattr(gramlot_kajenn, "NativeHtmlASGI")
    assert not hasattr(gramlot_kajenn, "create_asgi_application")


PAGE = """from gramlot import Page as BasePage, source
class Page(BasePage):
    title = 'Native test'
    def main(self, root): root.h1('Hello')
    @source
    def details(self, root, name='Ada'): root.p(name)
    @source
    def kind(self, root, value): root.p(type(value).__name__)
    @source
    def fail_lookup(self, root): raise LookupError('application lookup')
    @source
    def fail_runtime(self, root): raise RuntimeError('application runtime')
"""

NESTED_PAGE = """from gramlot import Page as BasePage
class Page(BasePage):
    title = 'Nested'
    def main(self, root): root.h1('Nested')
"""


def site(pages, *, raw=True):
    class Site(DefaultConfiguration):
        def applications_section(self, cfg):
            application = cfg.applications().application(
                code="native", mount="page", app_class=KajennNativeHtmlApplication, pages=pages
            )
            if raw:
                application.request(body="raw")

    return AsgiServer(config=Site)


def client_for(server, **options):
    transport = httpx.ASGITransport(app=server, raise_app_exceptions=False)
    return httpx.AsyncClient(transport=transport, base_url="http://test/page", **options)


def page_id_of(document):
    return re.search(r'"pageId": "([^"]+)"', document.text).group(1)


@pytest.mark.asyncio
async def test_native_html_protocol_owner_limits_asset_and_close(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    server = site(tmp_path)
    async with client_for(server) as client:
        document = await client.get("/")
        assert document.status_code == 200
        assert document.headers["content-type"].startswith("text/html")
        assert document.headers["cache-control"] == "no-store"
        assert "httponly" in document.headers["set-cookie"].lower()
        page_id = page_id_of(document)
        expected_close = "/page/gramlot/close"
        assert f'"closeUrl": "{expected_close}"' in document.text
        asset = await client.get("/assets/gramlot.js")
        assert asset.status_code == 200
        assert asset.headers["content-type"].startswith("text/javascript")
        main = await client.post("/gramlot/main", json={"pageId": page_id})
        assert main.headers["content-type"].startswith("application/json")
        assert from_tytx(main.text).nodes[0].value == "Hello"
        remote = await client.post(
            "/gramlot/source",
            json={"pageId": page_id, "method": "details", "params": {"name": "Grace"}},
        )
        assert from_tytx(remote.text).nodes[0].value == "Grace"
        typed = await client.post(
            "/gramlot/source",
            json={"pageId": page_id, "method": "kind", "params": {"value": "10::L"}},
        )
        assert from_tytx(typed.text).nodes[0].value == "str"
        assert (await client.post("/gramlot/source", json={"pageId": page_id, "method": "missing"})).status_code == 404
        for method in ("fail_lookup", "fail_runtime"):
            response = await client.post(
                "/gramlot/source", json={"pageId": page_id, "method": method}
            )
            assert response.status_code == 500
        assert (await client.post("/gramlot/main", content="{}",
                                  headers={"content-type": "text/plain"})).status_code == 415
        assert (await client.post("/gramlot/main", content="broken",
                                  headers={"content-type": "application/json"})).status_code == 400
        assert (await client.post("/gramlot/main", content=b"x" * 4097,
                                  headers={"content-type": "application/json"})).status_code == 413
        outsider = client_for(server)
        assert (await outsider.post("/gramlot/main", json={"pageId": page_id})).status_code == 404
        assert (await outsider.post("/gramlot/close", json={"pageId": page_id})).status_code == 200
        assert (await client.post("/gramlot/main", json={"pageId": page_id})).status_code == 200
        await outsider.aclose()
        assert (await client.post("/gramlot/close", json={"pageId": page_id})).json() == {"ok": True}
        assert (await client.post("/gramlot/main", json={"pageId": page_id})).status_code == 404


@pytest.mark.asyncio
async def test_native_html_multi_segment_page_paths(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    (tmp_path / "admin" / "users").mkdir(parents=True)
    (tmp_path / "admin" / "users" / "detail.py").write_text(NESTED_PAGE)
    async with client_for(site(tmp_path)) as client:
        nested = await client.get("/admin/users/detail")
        assert nested.status_code == 200
        assert "<title>Nested</title>" in nested.text
        main = await client.post("/gramlot/main", json={"pageId": page_id_of(nested)})
        assert from_tytx(main.text).nodes[0].value == "Nested"
        assert (await client.get("/admin/users/missing")).status_code == 404
        assert (await client.get("/admin/_private")).status_code == 404


@pytest.mark.asyncio
async def test_native_html_http_method_filter(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    async with client_for(site(tmp_path)) as client:
        assert (await client.post("/", json={})).status_code == 405
        assert (await client.get("/gramlot/main")).status_code == 405
        assert (await client.put("/assets/gramlot.js")).status_code == 405
        head = await client.head("/assets/gramlot.js")
        assert head.status_code == 200
        assert head.content == b""


@pytest.mark.asyncio
async def test_native_html_requires_raw_body(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    async with client_for(site(tmp_path, raw=False)) as client:
        page_id = page_id_of(await client.get("/"))
        assert (await client.post("/gramlot/main", json={"pageId": page_id})).status_code == 500
