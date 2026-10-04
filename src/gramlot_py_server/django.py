# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Translate the Gramlot Host protocol into Django views and URLs."""

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
    FileHost,
    HostCapacity,
    PageExpired,
    PageNotFound,
    SourceNotFound,
    runtime_asset,
)

from gramlot_py_server.scaffold import add_new

MAX_REQUEST_BYTES = 4096
OWNER_COOKIE = "gramlot_owner"
COMPANION_MEDIA_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}
# The core themes, served below the mount path as the runtime is. The built-in
# table of MimeTypes() ignores the system files; it lacks the font types.
THEMES = Path(str(files("gramlot").joinpath("resources", "themes")))
MEDIA_TYPES = MimeTypes()
FONT_MEDIA_TYPES = {".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf"}


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
    media_type = FONT_MEDIA_TYPES.get(real.suffix) or MEDIA_TYPES.guess_type(real.name)[0]
    media_type = media_type or "application/octet-stream"
    if media_type.startswith("text/"):
        media_type += "; charset=utf-8"
    return {"file": real, "type": media_type}


class Pages:
    """Own a Gramlot ``FileHost`` and expose it at one Django URLconf mount point.

    Add ``urlpatterns`` to the URLconf: it includes ``urls`` at ``mount_path``,
    which is also passed to ``open_page`` as the mount prefix of browser URLs.
    The prefix without the final slash (``/py``) answers 301 to ``/py/``: pages
    link each other with relative URLs. The cookie associates browser requests
    with in-process page records; it is not authentication.

    GET and HEAD serve a ``.css`` or ``.js`` file whose real path is below the
    pages folder: the companions of ``FileHost`` (stylesheet, page module or
    ``_aux.js`` with the page ``Logic``) and ``Page.css`` files placed there.
    Every other file of the folder is not served.

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
        self.host = FileHost(
            pages,
            runtime_url="/assets/gramlot.js",
            main_url="/gramlot/main",
            source_url="/gramlot/source",
            close_url="/gramlot/close",
            page_ttl=page_ttl,
            max_pages=max_pages,
        )
        self.urls = [
            path("assets/gramlot.js", self.asset),
            path("gramlot/main", csrf_exempt(self.main)),
            path("gramlot/source", csrf_exempt(self.source)),
            path("gramlot/close", csrf_exempt(self.close)),
            path("", self.page),
            path("<path:page_path>", self.page),
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
        owner = request.COOKIES.get(OWNER_COOKIE) or token_urlsafe(24)
        try:
            opened = async_to_sync(self.host.open_page)(page_path, owner=owner, prefix=self.mount_path)
        except PageNotFound:
            return HttpResponse("Page not found", status=404)
        except HostCapacity:
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
        root = self.host.pages_dir.resolve()
        real = root.joinpath(*page_path.strip("/").split("/")).resolve()
        if not (real.is_relative_to(root) and real.is_file()):
            return HttpResponse("Not found", status=404)
        body = b"" if request.method == "HEAD" else real.read_bytes()
        response = HttpResponse(body, content_type=COMPANION_MEDIA_TYPES[suffix])
        response["Cache-Control"] = "no-store"
        return response

    def main(self, request):
        return self._operation(request, "main")

    def source(self, request):
        return self._operation(request, "source")

    def close(self, request):
        return self._operation(request, "close")

    def _operation(self, request, operation):
        if request.method != "POST":
            return HttpResponse(status=405)
        if request.content_type != "application/json":
            return HttpResponse("Expected application/json", status=415)
        if len(request.body) > MAX_REQUEST_BYTES:
            return HttpResponse("Request too large", status=413)
        try:
            payload = json.loads(request.body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return HttpResponse("Invalid JSON request", status=400)
        if not isinstance(payload, dict) or not isinstance(payload.get("pageId"), str):
            return HttpResponse("Invalid JSON request", status=400)
        if operation == "source" and not isinstance(payload.get("params", {}), dict):
            return HttpResponse("Source params must be a dictionary", status=400)
        owner = request.COOKIES.get(OWNER_COOKIE)
        try:
            if operation == "main":
                result = async_to_sync(self.host.main)(payload["pageId"], owner=owner)
            elif operation == "source":
                result = async_to_sync(self.host.source)(
                    payload["pageId"], payload.get("method"), payload.get("params", {}),
                    owner=owner,
                )
            else:
                self.host.close_page(payload["pageId"], owner=owner)
                result = json.dumps({"ok": True})
        except PageExpired:
            return HttpResponse("Unknown page", status=404)
        except SourceNotFound:
            return HttpResponse("Unknown Source method", status=404)
        response = HttpResponse(result, content_type="application/json")
        response["Cache-Control"] = "no-store"
        return response


def commands(verbs) -> None:
    """The verbs of ``gramlot django``: an entry point of ``gramlot_py_server.commands``."""
    add_new(verbs, "django", start="django-admin runserver --settings=settings --pythonpath=.", url="http://127.0.0.1:8000/")


__all__ = ["Pages"]
