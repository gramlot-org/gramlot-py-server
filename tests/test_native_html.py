import re

import httpx
import pytest
from genro_asgi import BaseServer
from genro_tytx import from_tytx

from gramlot_genro_asgi import KajennNativeHtmlApplication, NativeHtmlASGI


PAGE = """from gramlot import Page as BasePage, source
class Page(BasePage):
    title = 'Native test'
    def main(self, root): root.h1('Hello')
    @source
    def details(self, root, name='Ada'): root.p(name)
    @source
    def fail_lookup(self, root): raise LookupError('application lookup')
    @source
    def fail_runtime(self, root): raise RuntimeError('application runtime')
"""


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["generic", "kajenn"])
async def test_native_html_protocol_owner_limits_asset_and_close(tmp_path, kind):
    (tmp_path / "index.py").write_text(PAGE)
    if kind == "generic":
        app = NativeHtmlASGI(tmp_path)
        base_url = "http://test"
    else:
        app = BaseServer(applications=[KajennNativeHtmlApplication(tmp_path, mount="page")])
        base_url = "http://test/page"
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
        document = await client.get("/")
        assert document.status_code == 200
        page_id = re.search(r'"pageId": "([^"]+)"', document.text).group(1)
        expected_close = "/page/gramlot/close" if kind == "kajenn" else "/gramlot/close"
        assert f'"closeUrl": "{expected_close}"' in document.text
        assert (await client.get("/assets/gramlot.js")).status_code == 200
        main = await client.post("/gramlot/main", json={"pageId": page_id})
        assert from_tytx(main.text).nodes[0].value == "Hello"
        remote = await client.post(
            "/gramlot/source",
            json={"pageId": page_id, "method": "details", "params": {"name": "Grace"}},
        )
        assert from_tytx(remote.text).nodes[0].value == "Grace"
        assert (await client.post("/gramlot/source", json={"pageId": page_id, "method": "missing"})).status_code == 404
        for method in ("fail_lookup", "fail_runtime"):
            response = await client.post(
                "/gramlot/source", json={"pageId": page_id, "method": method}
            )
            assert response.status_code == 500
        assert (await client.post("/gramlot/main", content="{}",
                                  headers={"content-type": "text/plain"})).status_code == 415
        assert (await client.post("/gramlot/main", content=b"x" * 4097,
                                  headers={"content-type": "application/json"})).status_code == 413
        outsider = httpx.AsyncClient(transport=transport, base_url=base_url)
        assert (await outsider.post("/gramlot/main", json={"pageId": page_id})).status_code == 404
        assert (await outsider.post("/gramlot/close", json={"pageId": page_id})).status_code == 200
        assert (await client.post("/gramlot/main", json={"pageId": page_id})).status_code == 200
        await outsider.aclose()
        assert (await client.post("/gramlot/close", json={"pageId": page_id})).json() == {"ok": True}
        assert (await client.post("/gramlot/main", json={"pageId": page_id})).status_code == 404
