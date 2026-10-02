import json
import re

import httpx
import pytest
from genro_tytx import from_tytx

from gramlot_uvicorn import NativeHtmlASGI, create_asgi_application


STRICT_CSP = "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"
PERMISSIVE_CSP = "script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'"
BOOTSTRAP = re.compile(
    r'<script type="module" nonce="([^"]+)">import \{PageBootstrap\} from ("[^"]+");'
    r"await new PageBootstrap\((.+)\)\.run\(\);</script>"
)


def bootstrap(document):
    """Return the script nonce, the runtime URL and the PageBootstrap argument."""
    nonce, runtime, argument = BOOTSTRAP.search(document).groups()
    return nonce, json.loads(runtime), json.loads(argument)


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
async def test_native_html_protocol_owner_limits_asset_and_close(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    app = create_asgi_application(tmp_path)
    assert isinstance(app, NativeHtmlASGI)
    base_url = "http://test"
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url=base_url) as client:
        document = await client.get("/")
        assert document.status_code == 200
        assert "content-security-policy" not in document.headers
        _, runtime, argument = bootstrap(document.text)
        assert runtime == "/assets/gramlot.js"
        page_id = argument["config"]["pageId"]
        assert argument["config"]["closeUrl"] == "/gramlot/close"
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


MOUNTED_PAGE = """from gramlot import Page as BasePage
class Page(BasePage):
    title = 'Mounted test'
    css = ['/theme.css', 'local.css', 'https://cdn.example/remote.css']
    def main(self, root): root.h1('Mounted')
"""


@pytest.mark.asyncio
async def test_mount_path_prefixes_root_relative_urls_once(tmp_path):
    (tmp_path / "index.py").write_text(MOUNTED_PAGE)
    app = create_asgi_application(tmp_path, mount_path="/py")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        document = (await client.get("/")).text
    _, runtime, argument = bootstrap(document)
    assert runtime == "/py/assets/gramlot.js"
    config = argument["config"]
    assert config["mainUrl"] == "/py/gramlot/main"
    assert config["sourceUrl"] == "/py/gramlot/source"
    assert config["closeUrl"] == "/py/gramlot/close"
    assert argument["resources"]["css"] == [
        "/py/theme.css", "local.css", "https://cdn.example/remote.css"
    ]
    assert "<link" not in document
    assert "/py/py/" not in document


@pytest.mark.asyncio
@pytest.mark.parametrize("policy", [STRICT_CSP, PERMISSIVE_CSP])
async def test_content_security_policy_carries_the_bootstrap_nonce(tmp_path, policy):
    (tmp_path / "index.py").write_text(PAGE)
    app = create_asgi_application(tmp_path, content_security_policy=policy)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        first = await client.get("/")
        second = await client.get("/")
        runtime = await client.get("/assets/gramlot.js")
    for response in (first, second):
        nonce, _, _ = bootstrap(response.text)
        assert response.headers["content-security-policy"] == policy.replace("{nonce}", nonce)
    assert bootstrap(first.text)[0] != bootstrap(second.text)[0]
    assert "content-security-policy" not in runtime.headers


async def raw_get(app, path):
    """Call the ASGI application with ``path`` as sent, without client normalisation."""
    messages = []

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(message):
        messages.append(message)

    await app({"type": "http", "method": "GET", "path": path, "headers": []}, receive, send)
    return messages[0]["status"]


@pytest.mark.asyncio
async def test_companions_and_page_css_below_the_pages_folder(tmp_path):
    pages = tmp_path / "pages"
    (pages / "themes").mkdir(parents=True)
    (pages / "index.py").write_text(MOUNTED_PAGE.replace("'/theme.css'", "'/themes/theme.css'"))
    (pages / "index.css").write_text("h1 { color: red; }")
    (pages / "index_aux.js").write_text("export class Logic {}")
    (pages / "index.md").write_text("# Readme")
    (pages / "themes" / "theme.css").write_text("body { margin: 0; }")
    (tmp_path / "outside.css").write_text("secret")
    (pages / "escape.css").symlink_to(tmp_path / "outside.css")
    app = create_asgi_application(pages, mount_path="/py")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        _, _, argument = bootstrap((await client.get("/")).text)
        resources = argument["resources"]
        assert resources["css"] == [
            "/py/themes/theme.css", "local.css", "https://cdn.example/remote.css", "/py/index.css"
        ]
        assert resources["js"] == [{"url": "/py/index_aux.js", "group": None}]
        for url, media_type in (("/py/themes/theme.css", "text/css"),
                                ("/py/index.css", "text/css"),
                                ("/py/index_aux.js", "text/javascript")):
            response = await client.get(url.removeprefix("/py"))
            assert response.status_code == 200
            assert response.headers["content-type"].startswith(media_type)
            head = await client.head(url.removeprefix("/py"))
            assert head.status_code == 200 and head.content == b""
        assert (await client.get("/index_aux.js")).text == "export class Logic {}"
        for path in ("/index.py", "/index.md", "/missing.css", "/escape.css"):
            assert (await client.get(path)).status_code == 404
        assert (await client.post("/index.css")).status_code == 405
    assert await raw_get(app, "/../outside.css") == 404
