import json
import re
from importlib.resources import files

import httpx
import pytest
from genro_tytx import from_tytx
from kajenn import AsgiServer
from kajenn.config.templates import DefaultConfiguration

from gallery_checks import check_index_main, expected, page_id, staged
from gramlot_py_server.kajenn import Application


def test_public_api_excludes_the_generic_asgi_factory():
    from gramlot_py_server import kajenn

    assert kajenn.__all__ == ["Application"]
    assert not hasattr(kajenn, "create_application")


PAGE = """from gramlot import Page as BasePage, source
class Page(BasePage):
    title = 'Test page'
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
                code="pages", mount="page", app_class=Application, pages=pages
            )
            if raw:
                application.request(body="raw")

    return AsgiServer(config=Site)


def client_for(server, **options):
    transport = httpx.ASGITransport(app=server, raise_app_exceptions=False)
    return httpx.AsyncClient(transport=transport, base_url="http://test/page", **options)


def page_id_of(document):
    return re.search(r'"pageId":"([^"]+)"', document.text).group(1)


@pytest.mark.asyncio
async def test_protocol_owner_limits_asset_and_close(tmp_path):
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
        assert f'"closeUrl":"{expected_close}"' in document.text
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
async def test_multi_segment_page_paths(tmp_path):
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
async def test_http_method_filter(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    async with client_for(site(tmp_path)) as client:
        assert (await client.post("/", json={})).status_code == 405
        assert (await client.get("/gramlot/main")).status_code == 405
        assert (await client.put("/assets/gramlot.js")).status_code == 405
        head = await client.head("/assets/gramlot.js")
        assert head.status_code == 200
        assert head.content == b""


@pytest.mark.asyncio
async def test_requires_raw_body(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    async with client_for(site(tmp_path, raw=False)) as client:
        page_id = page_id_of(await client.get("/"))
        assert (await client.post("/gramlot/main", json={"pageId": page_id})).status_code == 500


STRICT_CSP = "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"
BOOTSTRAP = re.compile(
    r'<script type="module" nonce="([^"]+)">import \{PageBootstrap\} from ("[^"]+");'
    r"await new PageBootstrap\((.+)\)\.run\(\);</script>"
)


@pytest.mark.asyncio
async def test_mount_companions_and_content_security_policy(tmp_path):
    pages = tmp_path / "pages"
    (pages / "themes").mkdir(parents=True)
    (pages / "index.py").write_text(
        "from gramlot import Page as Base\n"
        "class Page(Base):\n"
        "    css = ['/themes/theme.css', 'local.css']\n"
        "    def main(self, root): root.h1('Styled')\n"
    )
    (pages / "index.css").write_text("h1 { color: red; }")
    (pages / "index_aux.js").write_text("export class Logic {}")
    (pages / "index.md").write_text("# Readme")
    (pages / "themes" / "theme.css").write_text("body { margin: 0; }")
    (tmp_path / "outside.css").write_text("secret")
    (pages / "escape.css").symlink_to(tmp_path / "outside.css")

    class Site(DefaultConfiguration):
        def applications_section(self, cfg):
            cfg.applications().application(
                code="pages", mount="page", app_class=Application, pages=pages,
                content_security_policy=STRICT_CSP,
            ).request(body="raw")

    async with client_for(AsgiServer(config=Site)) as client:
        document = await client.get("/")
        nonce, runtime, argument = BOOTSTRAP.search(document.text).groups()
        assert document.headers["content-security-policy"] == STRICT_CSP.replace("{nonce}", nonce)
        assert json.loads(runtime) == "/page/assets/gramlot.js"
        resources = json.loads(argument)["resources"]
        assert resources["css"] == ["/page/themes/theme.css", "local.css", "/page/index.css"]
        assert resources["js"] == [{"url": "/page/index_aux.js", "group": None}]
        for url, media_type in (("/themes/theme.css", "text/css"),
                                ("/index.css", "text/css"),
                                ("/index_aux.js", "text/javascript")):
            response = await client.get(url)
            assert response.status_code == 200
            assert response.headers["content-type"].startswith(media_type)
            head = await client.head(url)
            assert head.status_code == 200 and head.content == b""
        for url in ("/index.py", "/index.md", "/missing.css", "/escape.css"):
            assert (await client.get(url)).status_code == 404
        assert (await client.post("/index.css")).status_code == 405


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
    async with client_for(site(pages)) as client:
        argument = json.loads(BOOTSTRAP.search((await client.get("/foo")).text).group(3))
        assert argument["resources"]["js"] == [{"url": "/page/foo.js", "group": None}]
        response = await client.get("/foo.js")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/javascript; charset=utf-8"
        assert response.text == PAGE_MODULE
        head = await client.head("/foo.js")
        assert head.status_code == 200 and head.content == b""
        assert (await client.get("/foo.py")).status_code == 404


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

    class Site(DefaultConfiguration):
        def applications_section(self, cfg):
            cfg.applications().application(
                code="pages", mount="page", app_class=Application, pages=pages, assets=assets,
            ).request(body="raw")

    transport = httpx.ASGITransport(app=AsgiServer(config=Site), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for url, media_type, body in (("/page/assets/branding/logo.svg", "image/svg+xml", b"<svg/>"),
                                      ("/page/gallery/dist/notices.json", "application/json", b"[]")):
            response = await client.get(url)
            assert response.status_code == 200
            assert response.headers["content-type"] == media_type
            assert response.content == body
            head = await client.head(url)
            assert head.status_code == 200 and head.content == b""
        assert (await client.post("/page/assets/branding/logo.svg")).status_code == 405
        for url in ("/page/assets/branding/other.svg", "/assets/branding/logo.svg"):
            assert (await client.get(url)).status_code == 404
        response = await client.get("/page")
        assert response.status_code == 301 and response.headers["location"] == "/page/"
        response = await client.get("/page?a=1")
        assert response.status_code == 301 and response.headers["location"] == "/page/?a=1"
        assert (await client.get("/page/")).status_code == 200


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
    transport = httpx.ASGITransport(app=site(pages), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/page/themes/gramlot-base/theme.css")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/css; charset=utf-8"
        assert response.content == CORE_THEME
        head = await client.head("/page/themes/gramlot-base/theme.css")
        assert head.status_code == 200 and head.content == b""
        readme = await client.get("/page/themes/gramlot-base/README.md")
        assert readme.headers["content-type"] == "text/markdown; charset=utf-8"
        assert (await client.post("/page/themes/gramlot-base/theme.css")).status_code == 405
        assert (await client.get("/page/themes/gramlot-base/missing.css")).status_code == 404
        assert (await client.get("/page/themes/own.css")).content == b"h1 { color: red; }"


@pytest.mark.asyncio
async def test_gallery_under_the_mount_path(tmp_path):
    folder, assets = staged(tmp_path, "kajenn")

    class Site(DefaultConfiguration):
        def applications_section(self, cfg):
            cfg.applications().application(
                code="gallery", mount="py", app_class=Application, pages=folder, assets=assets,
            ).request(body="raw")

    transport = httpx.ASGITransport(app=AsgiServer(config=Site), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for url, kind in expected("kajenn"):
            response = await client.get(url)
            assert response.status_code == 200, url
            assert response.headers["content-type"].startswith(kind), url
        document = (await client.get("/py/")).text
        main = await client.post("/py/gramlot/main", json={"pageId": page_id(document)})
        check_index_main(main.text)


@pytest.mark.asyncio
async def test_empty_mount_serves_the_pages_at_the_site_root(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)

    class Site(DefaultConfiguration):
        def applications_section(self, cfg):
            cfg.applications().application(
                code="pages", mount="", app_class=Application, pages=tmp_path,
            ).request(body="raw")

    transport = httpx.ASGITransport(app=AsgiServer(config=Site), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        document = await client.get("/")
        assert document.status_code == 200
        assert '"mainUrl":"/gramlot/main"' in document.text
        assert "Path=/;" in document.headers["set-cookie"]
        main = await client.post("/gramlot/main", json={"pageId": page_id_of(document)})
        assert main.status_code == 200
        assert (await client.get("/assets/gramlot.js")).status_code == 200
