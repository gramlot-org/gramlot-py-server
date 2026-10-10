import json
import re
from importlib.resources import files

from flask import Flask
from genro_tytx import from_tytx

from gallery_checks import check_index_main, expected, page_id, staged
from index_html_checks import INDEX_HTML_MISSING, INDEX_HTML_PATHS, title_of, titled_pages
from gramlot_py_server.flask import mount_pages
from rpc_checks import envelope, rpc_outcome, rpc_source

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


def test_protocol_owner_limits_asset_and_close(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    app = Flask(__name__)
    mount_pages(app, tmp_path)
    client = app.test_client()
    document = client.get("/")
    page_id = re.search(r'"pageId":"([^"]+)"', document.text).group(1)
    assert '"closeUrl":"/gramlot/close"' in document.text
    assert '"rpcUrl":"/gramlot/rpc"' in document.text
    assert client.get("/assets/gramlot.js").status_code == 200

    def rpc(sender, *args, **kwargs):
        return sender.post("/gramlot/rpc", data=envelope(page_id, *args, **kwargs),
                           content_type="application/json")

    main = rpc(client)
    assert main.status_code == 200
    assert main.mimetype == "application/json"
    assert from_tytx(rpc_source(main.text)).nodes[0].value == "Hello"
    remote = rpc(client, "details", {"name": "Grace"})
    assert from_tytx(rpc_source(remote.text)).nodes[0].value == "Grace"
    assert rpc_outcome(rpc(client, "missing").text) == "not_found"
    for method in ("fail_lookup", "fail_runtime"):
        response = rpc(client, method)
        assert response.status_code == 200
        assert rpc_outcome(response.text) == "application_error"
    assert client.post("/gramlot/rpc", data="{}", content_type="text/plain").status_code == 415
    assert client.post("/gramlot/rpc", data=b"\xff", content_type="application/json").status_code == 400
    assert client.post("/gramlot/rpc", data="{}", content_type="application/json").status_code == 400
    assert client.post("/gramlot/close", data="{}", content_type="application/json").status_code == 400
    outsider = app.test_client()
    assert rpc_outcome(rpc(outsider).text) == "page_expired"
    assert outsider.post("/gramlot/close", json={"pageId": page_id}).status_code == 200
    assert rpc(client).status_code == 200
    assert client.post("/gramlot/close", json={"pageId": page_id}).json == {"ok": True}
    assert rpc_outcome(rpc(client).text) == "page_expired"


def test_capacity_is_service_unavailable(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    app = Flask(__name__)
    mount_pages(app, tmp_path, max_pages=1)
    client = app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/").status_code == 503


def test_prefixed_close_url_matches_route(tmp_path):
    (tmp_path / "index.py").write_text(PAGE)
    app = Flask(__name__)
    mount_pages(app, tmp_path, mount_path="/nested")
    client = app.test_client()
    document = client.get("/nested/")
    assert document.status_code == 200
    assert '"closeUrl":"/nested/gramlot/close"' in document.text
    page_id = re.search(r'"pageId":"([^"]+)"', document.text).group(1)
    assert client.post("/nested/gramlot/close", json={"pageId": page_id}).status_code == 200
    closed = client.post("/nested/gramlot/rpc", data=envelope(page_id), content_type="application/json")
    assert rpc_outcome(closed.text) == "page_expired"


STRICT_CSP = "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"
BOOTSTRAP = re.compile(
    r'<script type="module" nonce="([^"]+)">import \{PageBootstrap\} from ("[^"]+");'
    r"await new PageBootstrap\((.+)\)\.run\(\);</script>"
)


def test_mount_path_companions_and_content_security_policy(tmp_path):
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
    app = Flask(__name__)
    mount_pages(app, pages, mount_path="/nested", content_security_policy=STRICT_CSP)
    client = app.test_client()
    document = client.get("/nested/")
    nonce, runtime, argument = BOOTSTRAP.search(document.text).groups()
    assert document.headers["Content-Security-Policy"] == STRICT_CSP.replace("{nonce}", nonce)
    assert json.loads(runtime) == "/nested/assets/gramlot.js"
    resources = json.loads(argument)["resources"]
    assert resources["css"] == ["/nested/themes/theme.css", "local.css", "/nested/index.css"]
    assert resources["js"] == [{"url": "/nested/index_aux.js", "group": None}]
    for url, media_type in (("/nested/themes/theme.css", "text/css"),
                            ("/nested/index.css", "text/css"),
                            ("/nested/index_aux.js", "text/javascript")):
        response = client.get(url)
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith(media_type)
        head = client.head(url)
        assert head.status_code == 200 and head.data == b""
    for url in ("/nested/index.py", "/nested/index.md", "/nested/missing.css", "/nested/escape.css"):
        assert client.get(url).status_code == 404
    assert client.post("/nested/index.css").status_code == 405


PAGE_MODULE = """import {Page as BasePage} from '@gramlot/gramlot/page';
export class Page extends BasePage { main(root) { root.h1('JavaScript version'); } }
export class Logic { greet() { return 'Hello'; } }
"""


def test_page_module_is_served_for_its_logic(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "foo.py").write_text(
        "from gramlot import Page as Base\n"
        "class Page(Base):\n"
        "    def main(self, root): root.h1('Module')\n"
    )
    (pages / "foo.js").write_text(PAGE_MODULE)
    app = Flask(__name__)
    mount_pages(app, pages, mount_path="/nested")
    client = app.test_client()
    argument = json.loads(BOOTSTRAP.search(client.get("/nested/foo").text).group(3))
    assert argument["resources"]["js"] == [{"url": "/nested/foo.js", "group": None}]
    response = client.get("/nested/foo.js")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/javascript; charset=utf-8"
    assert response.text == PAGE_MODULE
    head = client.head("/nested/foo.js")
    assert head.status_code == 200 and head.data == b""
    assert client.get("/nested/foo.py").status_code == 404


def test_assets_and_redirect_of_the_bare_mount_path(tmp_path):
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
    app = Flask(__name__)
    mount_pages(app, pages, mount_path="/nested", assets=assets)
    client = app.test_client()
    for url, media_type, body in (("/nested/assets/branding/logo.svg", "image/svg+xml", b"<svg/>"),
                                  ("/nested/gallery/dist/notices.json", "application/json", b"[]")):
        response = client.get(url)
        assert response.status_code == 200
        assert response.headers["Content-Type"] == media_type
        assert response.data == body
        head = client.head(url)
        assert head.status_code == 200 and head.data == b""
    assert client.post("/nested/assets/branding/logo.svg").status_code == 405
    for url in ("/nested/assets/branding/other.svg", "/assets/branding/logo.svg"):
        assert client.get(url).status_code == 404
    response = client.get("/nested")
    assert response.status_code == 301 and response.headers["Location"].endswith("/nested/")
    response = client.get("/nested?a=1")
    assert response.status_code == 301 and response.headers["Location"].endswith("/nested/?a=1")
    assert client.get("/nested/").status_code == 200


CORE_THEME = files("gramlot").joinpath("resources", "themes", "gramlot-base", "theme.css").read_bytes()


def test_core_themes_below_the_mount_path(tmp_path):
    pages = tmp_path / "pages"
    (pages / "themes").mkdir(parents=True)
    (pages / "index.py").write_text(
        "from gramlot import Page as Base\n"
        "class Page(Base):\n"
        "    css = ['/themes/gramlot-base/theme.css']\n"
        "    def main(self, root): root.h1('Themed')\n"
    )
    (pages / "themes" / "own.css").write_text("h1 { color: red; }")
    app = Flask(__name__)
    mount_pages(app, pages, mount_path="/nested")
    client = app.test_client()
    response = client.get("/nested/themes/gramlot-base/theme.css")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/css; charset=utf-8"
    assert response.data == CORE_THEME
    head = client.head("/nested/themes/gramlot-base/theme.css")
    assert head.status_code == 200 and head.data == b""
    assert client.get("/nested/themes/gramlot-base/README.md").headers["Content-Type"] == "text/markdown; charset=utf-8"
    assert client.post("/nested/themes/gramlot-base/theme.css").status_code == 405
    assert client.get("/nested/themes/gramlot-base/missing.css").status_code == 404
    assert client.get("/nested/themes/own.css").data == b"h1 { color: red; }"


def test_gallery_under_the_mount_path(tmp_path):
    folder, assets = staged(tmp_path, "flask")
    app = Flask(__name__)
    mount_pages(app, folder, mount_path="/py", assets=assets)
    client = app.test_client()
    for url, kind in expected("flask"):
        response = client.get(url)
        assert response.status_code == 200, url
        assert response.headers["Content-Type"].startswith(kind), url
    document = client.get("/py/").text
    main = client.post("/py/gramlot/rpc", data=envelope(page_id(document)), content_type="application/json")
    check_index_main(rpc_source(main.text))


def test_index_html_opens_the_page_of_its_folder(tmp_path):
    app = Flask(__name__)
    mount_pages(app, titled_pages(tmp_path), mount_path="/nested")
    client = app.test_client()
    for path, title in INDEX_HTML_PATHS:
        response = client.get("/nested" + path)
        assert response.status_code == 200, path
        assert title_of(response.get_data(as_text=True)) == title, path
    for path in INDEX_HTML_MISSING:
        assert client.get("/nested" + path).status_code == 404, path
