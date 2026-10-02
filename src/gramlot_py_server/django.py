# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Translate the neutral Gramlot Host protocol into Django views and URLs."""

from __future__ import annotations

import json
from pathlib import Path
from secrets import token_urlsafe

from asgiref.sync import async_to_sync
from django.http import FileResponse, HttpResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from gramlot.server import Host, HostCapacity, PageExpired, PageNotFound, SourceNotFound, runtime_asset

MAX_REQUEST_BYTES = 4096
OWNER_COOKIE = "gramlot_owner"


class NativeHtmlPages:
    """Own a native Host and expose it at one Django URLconf mount point.

    Mount ``urls`` at the same ``prefix`` supplied here. The cookie associates
    browser requests with in-process page records; it is not authentication.
    """

    def __init__(self, pages: str | Path, *, prefix="", page_ttl=1800, max_pages=1000):
        self.prefix = "/" + prefix.strip("/") if prefix.strip("/") else ""
        self.host = Host(
            pages,
            runtime_url=f"{self.prefix}/assets/gramlot.js",
            main_url=f"{self.prefix}/gramlot/main",
            source_url=f"{self.prefix}/gramlot/source",
            close_url=f"{self.prefix}/gramlot/close",
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
        if request.method not in ("GET", "HEAD"):
            return HttpResponse(status=405)
        owner = request.COOKIES.get(OWNER_COOKIE) or token_urlsafe(24)
        try:
            opened = async_to_sync(self.host.open_page)(page_path, owner=owner)
        except PageNotFound:
            return HttpResponse("Page not found", status=404)
        except HostCapacity:
            return HttpResponse("Page capacity reached", status=503)
        response = HttpResponse(opened.html, content_type="text/html; charset=utf-8")
        response["Cache-Control"] = "no-store"
        response.set_cookie(OWNER_COOKIE, owner, path=self.prefix or "/", httponly=True, samesite="Lax")
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
