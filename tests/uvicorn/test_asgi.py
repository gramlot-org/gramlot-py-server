import json
import re
from importlib.resources import files

import httpx
import pytest
from genro_tytx import from_tytx

from gramlot_py_server import uvicorn as uvicorn_module
from gallery_checks import check_index_main, expected, page_id, staged
from gramlot_py_server.uvicorn import Application, create_application


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
    title = 'Test page'
    def main(self, root): root.h1('Hello')
    @source
    def details(self, root, name='Ada'): root.p(name)
    @source
    def fail_lookup(self, root): raise LookupError('application lookup')
    @source
    def fail_runtime(self, root): raise RuntimeError('application runtime')
"""


@pytest.mark.asyncio
async def test_protocol_owner_limits_asset_and_close(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    app = create_application(tmp_path)
    assert isinstance(app, Application)
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
    app = create_application(tmp_path, mount_path="/py")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        document = (await client.get("/py/")).text
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
async def test_mount_path_is_the_prefix_of_the_request_paths(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    app = create_application(tmp_path, mount_path="/py")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        _, _, argument = bootstrap((await client.get("/py/index")).text)
        page_id = argument["config"]["pageId"]
        main = await client.post("/py/gramlot/main", json={"pageId": page_id})
        assert main.status_code == 200
        assert (await client.get("/py/assets/gramlot.js")).status_code == 200
        for path in ("/", "/index", "/assets/gramlot.js", "/pyindex", "/other/index"):
            assert (await client.get(path)).status_code == 404
        assert (await client.post("/gramlot/main", json={"pageId": page_id})).status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize("policy", [STRICT_CSP, PERMISSIVE_CSP])
async def test_content_security_policy_carries_the_bootstrap_nonce(tmp_path, policy):
    (tmp_path / "index.py").write_text(PAGE)
    app = create_application(tmp_path, content_security_policy=policy)
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
    app = create_application(pages, mount_path="/py")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        _, _, argument = bootstrap((await client.get("/py/")).text)
        resources = argument["resources"]
        assert resources["css"] == [
            "/py/themes/theme.css", "local.css", "https://cdn.example/remote.css", "/py/index.css"
        ]
        assert resources["js"] == [{"url": "/py/index_aux.js", "group": None}]
        for url, media_type in (("/py/themes/theme.css", "text/css"),
                                ("/py/index.css", "text/css"),
                                ("/py/index_aux.js", "text/javascript")):
            response = await client.get(url)
            assert response.status_code == 200
            assert response.headers["content-type"].startswith(media_type)
            head = await client.head(url)
            assert head.status_code == 200 and head.content == b""
        assert (await client.get("/py/index_aux.js")).text == "export class Logic {}"
        for path in ("/py/index.py", "/py/index.md", "/py/missing.css", "/py/escape.css"):
            assert (await client.get(path)).status_code == 404
        assert (await client.post("/py/index.css")).status_code == 405
    assert await raw_get(app, "/py/../outside.css") == 404


PAGE_MODULE = """import {Page as BasePage} from '@gramlot/gramlot/page';
export class Page extends BasePage { main(root) { root.h1('JavaScript version'); } }
export class Logic { greet() { return 'Hello'; } }
"""


@pytest.mark.asyncio
async def test_page_module_is_served_for_its_logic(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "foo.py").write_text(
        "from gramlot import Page as Base\n"
        "class Page(Base):\n"
        "    def main(self, root): root.h1('Module')\n"
    )
    (pages / "foo.js").write_text(PAGE_MODULE)
    app = create_application(pages, mount_path="/py")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        _, _, argument = bootstrap((await client.get("/py/foo")).text)
        assert argument["resources"]["js"] == [{"url": "/py/foo.js", "group": None}]
        response = await client.get("/py/foo.js")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/javascript; charset=utf-8"
        assert response.text == PAGE_MODULE
        head = await client.head("/py/foo.js")
        assert head.status_code == 200 and head.content == b""
        assert (await client.get("/py/foo.py")).status_code == 404


@pytest.mark.asyncio
async def test_assets_and_redirect_of_the_bare_mount_path(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "index.py").write_text(
        "from gramlot import Page as Base\n"
        "class Page(Base):\n"
        "    def main(self, root): root.h1('Index')\n"
    )
    (tmp_path / "logo.svg").write_text("<svg/>")
    (tmp_path / "notices.json").write_text("[]")
    assets = {
        "/assets/branding/logo.svg": {"file": tmp_path / "logo.svg", "type": "image/svg+xml"},
        "/gallery/dist/notices.json": {"file": str(tmp_path / "notices.json"), "type": "application/json"},
    }
    app = create_application(pages, mount_path="/py", assets=assets)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for url, media_type, body in (("/py/assets/branding/logo.svg", "image/svg+xml", b"<svg/>"),
                                      ("/py/gallery/dist/notices.json", "application/json", b"[]")):
            response = await client.get(url)
            assert response.status_code == 200
            assert response.headers["content-type"] == media_type
            assert response.content == body
            head = await client.head(url)
            assert head.status_code == 200 and head.content == b""
        assert (await client.post("/py/assets/branding/logo.svg")).status_code == 405
        for url in ("/py/assets/branding/other.svg", "/assets/branding/logo.svg"):
            assert (await client.get(url)).status_code == 404
        response = await client.get("/py")
        assert response.status_code == 301 and response.headers["location"] == "/py/"
        response = await client.get("/py?a=1")
        assert response.status_code == 301 and response.headers["location"] == "/py/?a=1"
        assert (await client.get("/py/")).status_code == 200


CORE_THEME = files("gramlot").joinpath("resources", "themes", "gramlot-base", "theme.css").read_bytes()


@pytest.mark.asyncio
async def test_core_themes_below_the_mount_path(tmp_path):
    pages = tmp_path / "pages"
    (pages / "themes").mkdir(parents=True)
    (pages / "index.py").write_text(
        "from gramlot import Page as Base\n"
        "class Page(Base):\n"
        "    css = ['/themes/gramlot-base/theme.css']\n"
        "    def main(self, root): root.h1('Themed')\n"
    )
    (pages / "themes" / "own.css").write_text("h1 { color: red; }")
    app = create_application(pages, mount_path="/py")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/py/themes/gramlot-base/theme.css")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/css; charset=utf-8"
        assert response.content == CORE_THEME
        head = await client.head("/py/themes/gramlot-base/theme.css")
        assert head.status_code == 200 and head.content == b""
        readme = await client.get("/py/themes/gramlot-base/README.md")
        assert readme.headers["content-type"] == "text/markdown; charset=utf-8"
        assert (await client.post("/py/themes/gramlot-base/theme.css")).status_code == 405
        assert (await client.get("/py/themes/gramlot-base/missing.css")).status_code == 404
        assert (await client.get("/py/themes/own.css")).content == b"h1 { color: red; }"
    assert await raw_get(app, "/py/themes/../../outside.css") == 404


def test_theme_media_types_and_real_path(tmp_path, monkeypatch):
    themes = tmp_path / "themes"
    (themes / "set").mkdir(parents=True)
    for name in ("font.woff2", "logo.svg", "data.bin", "style.css", "photo.webp", "notes.md"):
        (themes / "set" / name).write_bytes(b"x")
    (tmp_path / "outside.css").write_text("secret")
    (themes / "set" / "escape.css").symlink_to(tmp_path / "outside.css")
    monkeypatch.setattr(uvicorn_module, "THEMES", themes)
    types = {name: uvicorn_module.theme_file(f"/themes/set/{name}")["type"]
             for name in ("font.woff2", "logo.svg", "data.bin", "style.css", "photo.webp", "notes.md")}
    assert types == {"font.woff2": "font/woff2", "logo.svg": "image/svg+xml",
                     "data.bin": "application/octet-stream", "style.css": "text/css; charset=utf-8",
                     "photo.webp": "image/webp", "notes.md": "text/markdown; charset=utf-8"}
    for path in ("/themes/set/escape.css", "/themes/set", "/themes/missing.css", "/other/set/style.css"):
        assert uvicorn_module.theme_file(path) is None


@pytest.mark.asyncio
async def test_gallery_under_the_mount_path(tmp_path):
    folder, assets = staged(tmp_path, "uvicorn")
    app = create_application(folder, mount_path="/py", assets=assets)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for url, kind in expected("uvicorn"):
            response = await client.get(url)
            assert response.status_code == 200, url
            assert response.headers["content-type"].startswith(kind), url
        document = (await client.get("/py/")).text
        main = await client.post("/py/gramlot/main", json={"pageId": page_id(document)})
        check_index_main(main.text)
