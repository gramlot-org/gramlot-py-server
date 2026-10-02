# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Translate the Gramlot Host protocol into Django views and URLs."""

from __future__ import annotations

import json
from pathlib import Path
from secrets import token_urlsafe

from asgiref.sync import async_to_sync
from django.http import FileResponse, HttpResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from gramlot.server import (
    FileHost,
    HostCapacity,
    PageExpired,
    PageNotFound,
    SourceNotFound,
    runtime_asset,
)

MAX_REQUEST_BYTES = 4096
OWNER_COOKIE = "gramlot_owner"
COMPANION_MEDIA_TYPES = {
    ".css": "text/css; charset=utf-8",
    "_aux.js": "text/javascript; charset=utf-8",
}


class Pages:
    """Own a Gramlot ``FileHost`` and expose it at one Django URLconf mount point.

    Include ``urls`` at the same ``mount_path`` supplied here: ``mount_path`` is
    passed to ``open_page`` as the mount prefix of browser URLs. The cookie
    associates browser requests with in-process page records; it is not
    authentication.

    GET and HEAD serve a ``.css`` or ``_aux.js`` file whose real path is below the
    pages folder: the companions of ``FileHost`` and ``Page.css`` files placed
    there. Every other file of the folder is not served.

    ``content_security_policy`` is the application's policy, sent as the
    ``Content-Security-Policy`` header of each HTML page; ``{nonce}`` in it is
    replaced by the nonce that ``open_page`` puts on the bootstrap script.
    """

    def __init__(self, pages: str | Path, *, mount_path: str = "", page_ttl: float = 1800,
                 max_pages: int = 1000, content_security_policy: str | None = None) -> None:
        self.mount_path = "/" + mount_path.strip("/") if mount_path.strip("/") else ""
        self.content_security_policy = content_security_policy
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

    def asset(self, request):
        if request.method not in ("GET", "HEAD"):
            return HttpResponse(status=405)
        response = FileResponse(runtime_asset().open("rb"), content_type="text/javascript")
        response["Cache-Control"] = "no-cache"
        return response

    def page(self, request, page_path=""):
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


__all__ = ["Pages"]
