# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Translate the Gramlot server protocol into Django views and URLs."""

from __future__ import annotations

import json
from importlib.resources import files
from mimetypes import MimeTypes
from pathlib import Path
from secrets import token_urlsafe

from asgiref.sync import async_to_sync
from django.http import FileResponse, HttpResponse, HttpResponsePermanentRedirect
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt
from gramlot.server import (
    GramlotFileServer,
    InvalidRequest,
    PageNotFound,
    ServerCapacity,
    runtime_asset,
)

from gramlot_py_server.gallery import add_gallery
from gramlot_py_server.scaffold import add_new

OWNER_COOKIE = "gramlot_owner"
COMPANION_MEDIA_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}
# The core themes, served below the mount path as the runtime is. The built-in
# table of MimeTypes() ignores the system files; THEME_MEDIA_TYPES adds the types it
# lacks in some Python version: fonts and WebP in every one, Markdown before 3.12.
THEMES = Path(str(files("gramlot").joinpath("resources", "themes")))
MEDIA_TYPES = MimeTypes()
THEME_MEDIA_TYPES = {
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".webp": "image/webp",
    ".md": "text/markdown",
}


def theme_file(path: str) -> dict | None:
    """The file of the core themes at ``path`` (``/themes/…``), as an ``assets`` entry.

    Every file whose real path is below ``gramlot/resources/themes`` is served
    with the media type of its extension; ``None`` lets the request go on.
    """
    if not path.startswith("/themes/"):
        return None
    root = THEMES.resolve()
    real = root.joinpath(*path.removeprefix("/themes/").split("/")).resolve()
    if not (real.is_relative_to(root) and real.is_file()):
        return None
    media_type = THEME_MEDIA_TYPES.get(real.suffix) or MEDIA_TYPES.guess_type(real.name)[0]
    media_type = media_type or "application/octet-stream"
    if media_type.startswith("text/"):
        media_type += "; charset=utf-8"
    return {"file": real, "type": media_type}


class Pages:
    """Own a Gramlot ``GramlotFileServer`` and expose it at one Django URLconf mount point.

    Add ``urlpatterns`` to the URLconf: it includes ``urls`` at ``mount_path``,
    which is also passed to ``open_page`` as the mount prefix of browser URLs.
    The prefix without the final slash (``/py``) answers 301 to ``/py/``: pages
    link each other with relative URLs. The cookie associates browser requests
    with in-process page records; it is not authentication.

    GET and HEAD serve a ``.css`` or ``.js`` file whose real path is below the
    pages folder: the companions of ``GramlotFileServer`` (stylesheet, page module or
    ``_aux.js`` with the page ``Logic``) and ``Page.css`` files placed there.
    Every other file of the folder is not served.

    ``<path>/index.html`` opens the page ``<path>`` and ``/index.html`` the index,
    as a static host does.

    GET and HEAD serve every file below the themes folder of the core at
    ``/themes/…``, with the media type of its extension; a path the core does
    not have goes on to ``assets``, the companions and the pages.

    ``assets`` maps URLs below the mount path to files served by GET and HEAD,
    each ``{"file": path, "type": media type}``, as ``build_gallery`` of
    ``gramlot-examples`` returns them.

    ``content_security_policy`` is the application's policy, sent as the
    ``Content-Security-Policy`` header of each HTML page; ``{nonce}`` in it is
    replaced by the nonce that ``open_page`` puts on the bootstrap script.
    """

    def __init__(self, pages: str | Path, *, mount_path: str = "", page_ttl: float = 1800,
                 max_pages: int = 1000, content_security_policy: str | None = None,
                 assets: dict | None = None) -> None:
        self.mount_path = "/" + mount_path.strip("/") if mount_path.strip("/") else ""
        self.content_security_policy = content_security_policy
        self.assets = dict(assets or {})
        self.server = GramlotFileServer(
            pages,
            runtime_url="/assets/gramlot.js",
            rpc_url="/gramlot/rpc",
            close_url="/gramlot/close",
            page_ttl=page_ttl,
            max_pages=max_pages,
        )
        self.urls = [
            # Exempt from CSRF so that a POST answers 405 here, not 403 from the middleware.
            path("assets/gramlot.js", csrf_exempt(self.asset)),
            path("gramlot/rpc", csrf_exempt(self.rpc)),
            path("gramlot/close", csrf_exempt(self.close)),
            path("", csrf_exempt(self.page)),
            path("<path:page_path>", csrf_exempt(self.page)),
        ]

    @property
    def urlpatterns(self):
        """The URL patterns of the pages at ``mount_path``, with the redirect of the bare prefix."""
        if not self.mount_path:
            return [path("", include(self.urls))]
        prefix = self.mount_path.strip("/")
        return [path(prefix, self.redirect), path(prefix + "/", include(self.urls))]

    def redirect(self, request):
        query = request.META.get("QUERY_STRING", "")
        return HttpResponsePermanentRedirect(self.mount_path + "/" + (f"?{query}" if query else ""))

    def asset(self, request):
        if request.method not in ("GET", "HEAD"):
            return HttpResponse(status=405)
        response = FileResponse(runtime_asset().open("rb"), content_type="text/javascript")
        response["Cache-Control"] = "no-cache"
        return response

    def page(self, request, page_path=""):
        asset = theme_file("/" + page_path) or self.assets.get("/" + page_path)
        if asset is not None:
            return self.static(request, asset)
        suffix = next((suffix for suffix in COMPANION_MEDIA_TYPES if page_path.endswith(suffix)), None)
        if suffix is not None:
            return self.companion(request, page_path, suffix)
        if request.method not in ("GET", "HEAD"):
            return HttpResponse(status=405)
        # As on a static host, <path>/index.html is the page <path> and /index.html the index.
        if ("/" + page_path).endswith("/index.html"):
            page_path = page_path.removesuffix("index.html")
        owner = request.COOKIES.get(OWNER_COOKIE) or token_urlsafe(24)
        try:
            opened = async_to_sync(self.server.open_page)(page_path, owner=owner, prefix=self.mount_path)
        except PageNotFound:
            return HttpResponse("Page not found", status=404)
        except ServerCapacity:
            return HttpResponse("Page capacity reached", status=503)
        response = HttpResponse(opened.html, content_type="text/html; charset=utf-8")
        response["Cache-Control"] = "no-store"
        if self.content_security_policy is not None:
            policy = self.content_security_policy.replace("{nonce}", opened.nonce)
            response["Content-Security-Policy"] = policy
        response.set_cookie(OWNER_COOKIE, owner, path=self.mount_path or "/", httponly=True, samesite="Lax")
        return response

    def static(self, request, asset):
        """Serve one file of ``assets`` with its media type."""
        if request.method not in ("GET", "HEAD"):
            return HttpResponse(status=405)
        body = b"" if request.method == "HEAD" else Path(asset["file"]).read_bytes()
        response = HttpResponse(body, content_type=asset["type"])
        response["Cache-Control"] = "no-store"
        return response

    def companion(self, request, page_path, suffix):
        """Serve the file of ``page_path`` when its real path is below the pages folder."""
        if request.method not in ("GET", "HEAD"):
            return HttpResponse(status=405)
        root = self.server.pages_dir.resolve()
        real = root.joinpath(*page_path.strip("/").split("/")).resolve()
        if not (real.is_relative_to(root) and real.is_file()):
            return HttpResponse("Not found", status=404)
        body = b"" if request.method == "HEAD" else real.read_bytes()
        response = HttpResponse(body, content_type=COMPANION_MEDIA_TYPES[suffix])
        response["Cache-Control"] = "no-store"
        return response

    def rpc(self, request):
        return self._operation(request, "rpc")

    def close(self, request):
        return self._operation(request, "close")

    def _operation(self, request, operation):
        if request.method != "POST":
            return HttpResponse(status=405)
        if request.content_type != "application/json":
            return HttpResponse("Expected application/json", status=415)
        try:
            text = request.body.decode()
        except UnicodeDecodeError:
            return HttpResponse("Request body is not UTF-8", status=400)
        owner = request.COOKIES.get(OWNER_COOKIE)
        if operation == "rpc":
            try:
                result = async_to_sync(self.server.call)(text, owner=owner)
            except InvalidRequest:
                return HttpResponse("Invalid envelope", status=400)
        else:
            try:
                payload = json.loads(text)
                if not isinstance(payload, dict) or not isinstance(payload.get("pageId"), str):
                    raise ValueError("Missing pageId")
            except ValueError:
                return HttpResponse("Invalid JSON request", status=400)
            self.server.close_page(payload["pageId"], owner=owner)
            result = json.dumps({"ok": True})
        response = HttpResponse(result, content_type="application/json")
        response["Cache-Control"] = "no-store"
        return response


class _URLconf:
    """A ``ROOT_URLCONF`` object: Django reads its ``urlpatterns`` and caches it by identity."""

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns


def serve(pages: str | Path, *, host: str = "127.0.0.1", port: int = 8000, **options) -> None:
    """Serve ``pages`` with the Django development server until it stops.

    Django is configured here with the URLconf of one ``Pages``: the process must
    not have configured it before.
    """
    import django
    from django.conf import settings
    from django.core.management import call_command

    settings.configure(
        SECRET_KEY=token_urlsafe(32),
        ALLOWED_HOSTS=["127.0.0.1", "localhost", host],
        ROOT_URLCONF=_URLconf(Pages(pages, **options).urlpatterns),
        MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
    )
    django.setup()
    call_command("runserver", f"{host}:{port}", use_reloader=False)


def commands(verbs) -> None:
    """The verbs of ``gramlot django``: an entry point of ``gramlot_py_server.commands``."""
    add_new(verbs, "django", start="django-admin runserver --settings=settings --pythonpath=.", url="http://127.0.0.1:8000/")
    add_gallery(verbs, "django", serve)


__all__ = ["Pages"]
