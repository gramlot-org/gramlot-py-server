import json
import re
from importlib.resources import files

import httpx
import pytest
from genro_tytx import from_tytx

from gallery_checks import check_index_main, expected, gallery_collections, page_id, staged
from http_rules import (NO_STORE_URLS, REFUSED_ON_A_PAGE, RUNTIME_URL, check_no_cache, check_no_store,
                        check_owner_cookie, check_refusal, rules_pages)
from index_html_checks import INDEX_HTML_MISSING, INDEX_HTML_PATHS, title_of, titled_pages
from rpc_checks import RPC_HEADERS, envelope, rpc_outcome, rpc_source
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
        assert argument["config"]["rpcUrl"] == "/gramlot/rpc"
        assert argument["config"]["capabilities"] == []
        assert (await client.get("/assets/gramlot.js")).status_code == 200

        async def rpc(sender, *args, **kwargs):
            return await sender.post("/gramlot/rpc", content=envelope(page_id, *args, **kwargs),
                                     headers=RPC_HEADERS)

        main = await rpc(client)
        assert main.status_code == 200
        assert main.headers["content-type"] == "application/json"
        assert from_tytx(rpc_source(main.text)).nodes[0].value == "Hello"
        remote = await rpc(client, "details", {"name": "Grace"})
        assert from_tytx(rpc_source(remote.text)).nodes[0].value == "Grace"
        assert rpc_outcome((await rpc(client, "missing")).text) == "not_found"
        for method in ("fail_lookup", "fail_runtime"):
            response = await rpc(client, method)
            assert response.status_code == 200
            assert rpc_outcome(response.text) == "application_error"
        assert (await client.post("/gramlot/rpc", content="{}",
                                  headers={"content-type": "text/plain"})).status_code == 415
        assert (await client.post("/gramlot/rpc", content=b"\xff",
                                  headers=RPC_HEADERS)).status_code == 400
        assert (await client.post("/gramlot/rpc", content="{}", headers=RPC_HEADERS)).status_code == 400
        assert (await client.post("/gramlot/close", content="{}", headers=RPC_HEADERS)).status_code == 400
        outsider = httpx.AsyncClient(transport=transport, base_url=base_url)
        assert rpc_outcome((await rpc(outsider)).text) == "page_expired"
        assert (await outsider.post("/gramlot/close", json={"pageId": page_id})).status_code == 200
        assert (await rpc(client)).status_code == 200
        await outsider.aclose()
        assert (await client.post("/gramlot/close", json={"pageId": page_id})).json() == {"ok": True}
        assert rpc_outcome((await rpc(client)).text) == "page_expired"


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
    assert config["rpcUrl"] == "/py/gramlot/rpc"
    assert config["closeUrl"] == "/py/gramlot/close"
    assert argument["resources"]["css"] == [
        "/py/themes/gramlot-base/theme.css", "/py/theme.css", "local.css", "https://cdn.example/remote.css"
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
        main = await client.post("/py/gramlot/rpc", content=envelope(page_id), headers=RPC_HEADERS)
        assert main.status_code == 200
        assert (await client.get("/py/assets/gramlot.js")).status_code == 200
        for path in ("/", "/index", "/assets/gramlot.js", "/pyindex", "/other/index"):
            assert (await client.get(path)).status_code == 404
        assert (await client.post("/gramlot/rpc", content=envelope(page_id),
                                  headers=RPC_HEADERS)).status_code == 404


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
            "/py/themes/gramlot-base/theme.css", "/py/themes/theme.css", "local.css",
            "https://cdn.example/remote.css", "/py/index.css"
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


@pytest.mark.asyncio
async def test_gallery_under_the_mount_path(tmp_path):
    folder, assets = staged(tmp_path, "uvicorn")
    app = create_application(folder, mount_path="/py", assets=assets, collections=gallery_collections())
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for url, kind in expected("uvicorn"):
            response = await client.get(url)
            assert response.status_code == 200, url
            assert response.headers["content-type"].startswith(kind), url
        document = (await client.get("/py/")).text
        main = await client.post("/py/gramlot/rpc", content=envelope(page_id(document)),
                                 headers=RPC_HEADERS)
        check_index_main(rpc_source(main.text))


@pytest.mark.asyncio
async def test_index_html_opens_the_page_of_its_folder(tmp_path):
    app = create_application(titled_pages(tmp_path), mount_path="/py")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for path, title in INDEX_HTML_PATHS:
            response = await client.get("/py" + path)
            assert response.status_code == 200, path
            assert title_of(response.text) == title, path
        for path in INDEX_HTML_MISSING:
            assert (await client.get("/py" + path)).status_code == 404, path


@pytest.mark.asyncio
@pytest.mark.parametrize("mount", ["", "/py"])
async def test_http_rules_of_the_shared_base(tmp_path, mount):
    folder, assets = rules_pages(tmp_path)
    app = create_application(folder, mount_path=mount, assets=assets)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for method in REFUSED_ON_A_PAGE:
            response = await client.request(method, mount + "/")
            check_refusal(method, response.status_code, response.headers)
        for url in NO_STORE_URLS:
            check_no_store(url, (await client.get(mount + url)).headers)
        check_no_cache(RUNTIME_URL, (await client.get(mount + RUNTIME_URL)).headers)
        check_no_cache(RUNTIME_URL, (await client.head(mount + RUNTIME_URL)).headers)
        for url in ("/gramlot/rpc", "/gramlot/close"):
            response = await client.get(mount + url)
            check_refusal("GET", response.status_code, response.headers, "POST")
        for url in ("/assets/gramlot.js", "/themes/gramlot-base/theme.css", "/index.css", "/extra/logo.svg"):
            response = await client.post(mount + url)
            check_refusal("POST", response.status_code, response.headers, "GET, HEAD")
            check_no_store(url, response.headers)
        first = await client.get(mount + "/")
        owner = check_owner_cookie(first.headers["set-cookie"], mount or "/")
        second = await client.get(mount + "/")
        assert check_owner_cookie(second.headers["set-cookie"], mount or "/") == owner
        if mount:
            redirect = await client.get(mount)
            assert redirect.status_code == 301
            check_no_store(mount, redirect.headers)


@pytest.mark.asyncio
async def test_the_path_of_the_scope_is_decoded_once(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    (tmp_path / "a%20b.css").write_text("h1 { color: red; }")
    (tmp_path / "a b.css").write_text("h1 { color: blue; }")
    app = create_application(tmp_path)
    # The server has decoded the request path /a%2520b.css into the scope: a second decoding would serve "a b.css".
    messages = []

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(message):
        messages.append(message)

    await app({"type": "http", "method": "GET", "path": "/a%20b.css", "headers": []}, receive, send)
    assert messages[0]["status"] == 200
    assert messages[1]["body"] == b"h1 { color: red; }"


@pytest.mark.asyncio
async def test_the_lifespan_shutdown_forgets_every_page(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    app = create_application(tmp_path)
    events = [{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}]
    sent = []

    async def receive():
        return events.pop(0)

    async def send(message):
        sent.append(message["type"])
        if message["type"] == "lifespan.startup.complete":
            await client_opens_a_page()

    async def client_opens_a_page():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            assert (await client.get("/")).status_code == 200
        assert len(app.gramlot_server._pages) == 1

    await app({"type": "lifespan"}, receive, send)
    assert sent == ["lifespan.startup.complete", "lifespan.shutdown.complete"]
    assert app.gramlot_server._pages == {}
