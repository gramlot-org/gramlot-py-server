"""The installed Django adapter serves the native Gramlot browser protocol."""

import json
import re

import django
from django.conf import settings
from django.test import Client
from django.urls import clear_url_caches, include, path
from genro_tytx import from_tytx

from gramlot_django import NativeHtmlPages

if not settings.configured:
    settings.configure(
        SECRET_KEY="test-only",
        ALLOWED_HOSTS=["testserver"],
        ROOT_URLCONF=__name__,
        MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
    )
django.setup()

urlpatterns = []


def test_native_page_source_lifecycle_and_owner(tmp_path):
    pages = tmp_path / "pages"
    pages.mkdir()
    (pages / "index.py").write_text(
        "from gramlot import Page as Base, source\n"
        "class Page(Base):\n"
        "    title = 'Django native page'\n"
        "    def main(self, root): root.h1('Hello Django')\n"
        "    @source\n"
        "    def detail(self, root, name): root.p(name)\n"
    )
    integration = NativeHtmlPages(pages, prefix="/hello")
    global urlpatterns
    urlpatterns = [path("hello/", include(integration.urls))]
    clear_url_caches()
    client = Client(enforce_csrf_checks=True)
    response = client.get("/hello/")
    assert response.status_code == 200
    assert b"/hello/assets/gramlot.js" in response.content
    assert b"/hello/gramlot/main" in response.content
    assert response.cookies["gramlot_owner"]["httponly"]
    page_id = re.search(rb'"pageId": "([0-9a-f]+)"', response.content).group(1).decode()
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
    integration = NativeHtmlPages(pages, prefix="/hello", max_pages=1)
    global urlpatterns
    urlpatterns = [path("hello/", include(integration.urls))]
    clear_url_caches()
    client = Client(enforce_csrf_checks=True)
    assert client.get("/hello/missing").status_code == 404
    opened = client.get("/hello/")
    assert opened.status_code == 200
    page_id = re.search(rb'"pageId": "([0-9a-f]+)"', opened.content).group(1).decode()
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
    integration = NativeHtmlPages(pages, prefix="/hello")
    global urlpatterns
    urlpatterns = [path("hello/", include(integration.urls))]
    clear_url_caches()
    client = Client(raise_request_exception=False)
    opened = client.get("/hello/")
    page_id = re.search(rb'"pageId": "([0-9a-f]+)"', opened.content).group(1).decode()
    response = client.post(
        "/hello/gramlot/main", json.dumps({"pageId": page_id}),
        content_type="application/json",
    )
    assert response.status_code == 500
