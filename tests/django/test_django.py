"""The Django adapter serves the Gramlot browser protocol."""

import json
import re

import django
from django.conf import settings
from django.test import Client
from django.urls import clear_url_caches, include, path
from genro_tytx import from_tytx

from gramlot_py_server.django import Pages

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
    assert b"/hello/gramlot/main" in response.content
    assert response.cookies["gramlot_owner"]["httponly"]
    page_id = re.search(rb'"pageId":"([0-9a-f]+)"', response.content).group(1).decode()
    asset = client.get("/hello/assets/gramlot.js")
    assert asset.status_code == 200
    assert b"Gramlot" in b"".join(asset.streaming_content)

    main = client.post("/hello/gramlot/main", json.dumps({"pageId": page_id}),
                       content_type="application/json")
    assert main.status_code == 200
    assert from_tytx(main.content.decode()).nodes[0].value == "Hello Django"
    source = client.post(
        "/hello/gramlot/source",
        json.dumps({"pageId": page_id, "method": "detail", "params": {"name": "Ada"}}),
        content_type="application/json",
    )
    assert source.status_code == 200
    assert from_tytx(source.content.decode()).nodes[0].value == "Ada"
    stranger = Client(enforce_csrf_checks=True)
    assert stranger.post("/hello/gramlot/main", json.dumps({"pageId": page_id}),
                         content_type="application/json").status_code == 404
    assert client.post("/hello/gramlot/close", json.dumps({"pageId": page_id}),
                       content_type="application/json").status_code == 200
    assert client.post("/hello/gramlot/main", json.dumps({"pageId": page_id}),
                       content_type="application/json").status_code == 404


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
    endpoint = "/hello/gramlot/source"
    assert client.get(endpoint).status_code == 405
    assert client.post(endpoint, "{}", content_type="text/plain").status_code == 415
    assert client.post(endpoint, "{", content_type="application/json").status_code == 400
    assert client.post(endpoint, " " * 4097, content_type="application/json").status_code == 413
    assert client.post(
        endpoint, json.dumps({"pageId": page_id, "method": "x", "params": []}),
        content_type="application/json",
    ).status_code == 400
    assert client.post(
        endpoint, json.dumps({"pageId": page_id, "method": "unknown"}),
        content_type="application/json",
    ).status_code == 404


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
    response = client.post(
        "/hello/gramlot/main", json.dumps({"pageId": page_id}),
        content_type="application/json",
    )
    assert response.status_code == 500


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
