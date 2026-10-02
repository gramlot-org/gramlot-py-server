import json
import re

from flask import Flask
from genro_tytx import from_tytx

from gramlot_py_server.flask import mount_pages

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
    assert client.get("/assets/gramlot.js").status_code == 200
    main = client.post("/gramlot/main", json={"pageId": page_id})
    assert from_tytx(main.text).nodes[0].value == "Hello"
    remote = client.post(
        "/gramlot/source",
        json={"pageId": page_id, "method": "details", "params": {"name": "Grace"}},
    )
    assert from_tytx(remote.text).nodes[0].value == "Grace"
    assert client.post("/gramlot/source", json={"pageId": page_id, "method": "missing"}).status_code == 404
    for method in ("fail_lookup", "fail_runtime"):
        assert client.post("/gramlot/source", json={"pageId": page_id, "method": method}).status_code == 500
    assert client.post("/gramlot/main", data="{}", content_type="text/plain").status_code == 415
    assert client.post("/gramlot/main", data=b"x" * 4097,
                       content_type="application/json").status_code == 413
    outsider = app.test_client()
    assert outsider.post("/gramlot/main", json={"pageId": page_id}).status_code == 404
    assert outsider.post("/gramlot/close", json={"pageId": page_id}).status_code == 200
    assert client.post("/gramlot/main", json={"pageId": page_id}).status_code == 200
    assert client.post("/gramlot/close", json={"pageId": page_id}).json == {"ok": True}
    assert client.post("/gramlot/main", json={"pageId": page_id}).status_code == 404


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
    assert client.post("/nested/gramlot/main", json={"pageId": page_id}).status_code == 404


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
