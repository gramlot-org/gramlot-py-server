"""The Django adapter serves the Gramlot browser protocol."""
import json
import re
from importlib.resources import files

import django
from django.conf import settings
from django.test import Client
from django.urls import clear_url_caches, include, path
from genro_tytx import from_tytx

from gallery_checks import check_index_main, expected, page_id, staged
from index_html_checks import INDEX_HTML_MISSING, INDEX_HTML_PATHS, title_of, titled_pages
from gramlot_py_server.django import Pages
from rpc_checks import envelope, rpc_outcome, rpc_source

if not settings.configured:
    settings.configure(
        SECRET_KEY="test-only",
        ALLOWED_HOSTS=["testserver"],
        ROOT_URLCONF=__name__,
        MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
    )
django.setup()

urlpatterns = []


def test_page_source_lifecycle_and_owner(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "index.py").write_text(
        "from gramlot import Page as Base, source\n"
        "class Page(Base):\n"
        "    title = 'Django page'\n"
        "    def main(self, root): root.h1('Hello Django')\n"
        "    @source\n"
        "    def detail(self, root, name): root.p(name)\n"
    )
    integration = Pages(pages, mount_path="/hello")
    global urlpatterns
    urlpatterns = [path("hello/", include(integration.urls))]
    clear_url_caches()
    client = Client(enforce_csrf_checks=True)
    response = client.get("/hello/")
    assert response.status_code == 200
    assert b"/hello/assets/gramlot.js" in response.content
    assert b'"rpcUrl":"/hello/gramlot/rpc"' in response.content
    assert response.cookies["gramlot_owner"]["httponly"]
    page_id = re.search(rb'"pageId":"([0-9a-f]+)"', response.content).group(1).decode()
    asset = client.get("/hello/assets/gramlot.js")
    assert asset.status_code == 200
    assert b"Gramlot" in b"".join(asset.streaming_content)

    def rpc(sender, *args, **kwargs):
        return sender.post("/hello/gramlot/rpc", envelope(page_id, *args, **kwargs),
                           content_type="application/json")

    main = rpc(client)
    assert main.status_code == 200
    assert main["Content-Type"] == "application/json"
    assert from_tytx(rpc_source(main.content)).nodes[0].value == "Hello Django"
    source = rpc(client, "detail", {"name": "Ada"})
    assert source.status_code == 200
    assert from_tytx(rpc_source(source.content)).nodes[0].value == "Ada"
    stranger = Client(enforce_csrf_checks=True)
    assert rpc_outcome(rpc(stranger).content) == "page_expired"
    assert client.post("/hello/gramlot/close", json.dumps({"pageId": page_id}),
                       content_type="application/json").status_code == 200
    assert rpc_outcome(rpc(client).content) == "page_expired"


def test_rejects_invalid_requests(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "index.py").write_text(
        "from gramlot import Page as Base\n"
        "class Page(Base):\n"
        "    def main(self, root): root.p('ok')\n"
    )
    integration = Pages(pages, mount_path="/hello", max_pages=1)
    global urlpatterns
    urlpatterns = [path("hello/", include(integration.urls))]
    clear_url_caches()
    client = Client(enforce_csrf_checks=True)
    assert client.get("/hello/missing").status_code == 404
    opened = client.get("/hello/")
    assert opened.status_code == 200
    page_id = re.search(rb'"pageId":"([0-9a-f]+)"', opened.content).group(1).decode()
    assert client.get("/hello/").status_code == 503
    endpoint = "/hello/gramlot/rpc"
    assert client.get(endpoint).status_code == 405
    assert client.post(endpoint, "{}", content_type="text/plain").status_code == 415
    assert client.post(endpoint, "{", content_type="application/json").status_code == 400
    assert client.post(endpoint, b"\xff", content_type="application/json").status_code == 400
    sent = json.loads(envelope(page_id))
    assert client.post(endpoint, json.dumps(sent | {"params": []}),
                       content_type="application/json").status_code == 400
    assert client.post("/hello/gramlot/close", "{}", content_type="application/json").status_code == 400
    unknown = client.post(endpoint, envelope(page_id, "unknown"), content_type="application/json")
    assert rpc_outcome(unknown.content) == "not_found"


def test_application_errors_are_not_reported_as_missing_pages(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "index.py").write_text(
        "from gramlot import Page as Base\n"
        "class Page(Base):\n"
        "    def main(self, root): raise LookupError('application failure')\n"
    )
    integration = Pages(pages, mount_path="/hello")
    global urlpatterns
    urlpatterns = [path("hello/", include(integration.urls))]
    clear_url_caches()
    client = Client(raise_request_exception=False)
    opened = client.get("/hello/")
    page_id = re.search(rb'"pageId":"([0-9a-f]+)"', opened.content).group(1).decode()
    response = client.post("/hello/gramlot/rpc", envelope(page_id), content_type="application/json")
    assert response.status_code == 200
    assert rpc_outcome(response.content) == "application_error"


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
    integration = Pages(pages, mount_path="/hello", content_security_policy=STRICT_CSP)
    global urlpatterns
    urlpatterns = [path("hello/", include(integration.urls))]
    clear_url_caches()
    client = Client()
    document = client.get("/hello/")
    nonce, runtime, argument = BOOTSTRAP.search(document.content.decode()).groups()
    assert document["Content-Security-Policy"] == STRICT_CSP.replace("{nonce}", nonce)
    assert json.loads(runtime) == "/hello/assets/gramlot.js"
    argument = json.loads(argument)
    assert argument["config"]["closeUrl"] == "/hello/gramlot/close"
    assert argument["resources"]["css"] == ["/hello/themes/theme.css", "local.css", "/hello/index.css"]
    assert argument["resources"]["js"] == [{"url": "/hello/index_aux.js", "group": None}]
    for url, media_type in (("/hello/themes/theme.css", "text/css"),
                            ("/hello/index.css", "text/css"),
                            ("/hello/index_aux.js", "text/javascript")):
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"].startswith(media_type)
        head = client.head(url)
        assert head.status_code == 200 and head.content == b""
    for url in ("/hello/index.py", "/hello/index.md", "/hello/missing.css", "/hello/escape.css"):
        assert client.get(url).status_code == 404
    assert client.post("/hello/index.css").status_code == 405


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
    integration = Pages(pages, mount_path="/hello")
    global urlpatterns
    urlpatterns = [path("hello/", include(integration.urls))]
    clear_url_caches()
    client = Client()
    argument = json.loads(BOOTSTRAP.search(client.get("/hello/foo").content.decode()).group(3))
    assert argument["resources"]["js"] == [{"url": "/hello/foo.js", "group": None}]
    response = client.get("/hello/foo.js")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/javascript; charset=utf-8"
    assert response.content.decode() == PAGE_MODULE
    head = client.head("/hello/foo.js")
    assert head.status_code == 200 and head.content == b""
    assert client.get("/hello/foo.py").status_code == 404


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
    integration = Pages(pages, mount_path="/hello", assets=assets)
    global urlpatterns
    urlpatterns = integration.urlpatterns
    clear_url_caches()
    client = Client()
    for url, media_type, body in (("/hello/assets/branding/logo.svg", "image/svg+xml", b"<svg/>"),
                                  ("/hello/gallery/dist/notices.json", "application/json", b"[]")):
        response = client.get(url)
        assert response.status_code == 200
        assert response["Content-Type"] == media_type
        assert response.content == body
        head = client.head(url)
        assert head.status_code == 200 and head.content == b""
    assert client.post("/hello/assets/branding/logo.svg").status_code == 405
    for url in ("/hello/assets/branding/other.svg", "/assets/branding/logo.svg"):
        assert client.get(url).status_code == 404
    response = client.get("/hello")
    assert response.status_code == 301 and response["Location"].endswith("/hello/")
    response = client.get("/hello?a=1")
    assert response.status_code == 301 and response["Location"].endswith("/hello/?a=1")
    assert client.get("/hello/").status_code == 200


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
    integration = Pages(pages, mount_path="/hello")
    global urlpatterns
    urlpatterns = integration.urlpatterns
    clear_url_caches()
    client = Client()
    response = client.get("/hello/themes/gramlot-base/theme.css")
    assert response.status_code == 200
    assert response["Content-Type"] == "text/css; charset=utf-8"
    assert response.content == CORE_THEME
    head = client.head("/hello/themes/gramlot-base/theme.css")
    assert head.status_code == 200 and head.content == b""
    assert client.get("/hello/themes/gramlot-base/README.md")["Content-Type"] == "text/markdown; charset=utf-8"
    assert client.post("/hello/themes/gramlot-base/theme.css").status_code == 405
    assert client.get("/hello/themes/gramlot-base/missing.css").status_code == 404
    assert client.get("/hello/themes/own.css").content == b"h1 { color: red; }"


def test_gallery_under_the_mount_path(tmp_path):
    folder, assets = staged(tmp_path, "django")
    integration = Pages(folder, mount_path="/py", assets=assets)
    global urlpatterns
    urlpatterns = integration.urlpatterns
    clear_url_caches()
    client = Client()
    for url, kind in expected("django"):
        response = client.get(url)
        assert response.status_code == 200, url
        assert response["Content-Type"].startswith(kind), url
    document = client.get("/py/").content.decode()
    main = client.post("/py/gramlot/rpc", envelope(page_id(document)), content_type="application/json")
    check_index_main(rpc_source(main.content))


def test_index_html_opens_the_page_of_its_folder(tmp_path):
    integration = Pages(titled_pages(tmp_path), mount_path="/hello")
    global urlpatterns
    urlpatterns = integration.urlpatterns
    clear_url_caches()
    client = Client()
    for url, title in INDEX_HTML_PATHS:
        response = client.get("/hello" + url)
        assert response.status_code == 200, url
        assert title_of(response.content.decode()) == title, url
    for url in INDEX_HTML_MISSING:
        assert client.get("/hello" + url).status_code == 404, url
