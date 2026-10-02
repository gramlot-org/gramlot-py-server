# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Kajenn integration for Gramlot's native HTML ``Host`` contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from secrets import token_urlsafe

from genro_routes import RoutingClass, route
from gramlot.server import Host, HostCapacity, PageExpired, PageNotFound, SourceNotFound, runtime_asset
from kajenn import (
    HTTPBadRequest,
    HTTPException,
    HTTPNotFound,
    HTTPUnsupportedMediaType,
    RoutedApplication,
)

MAX_REQUEST_BYTES = 4096
OWNER_COOKIE = "gramlot_owner"


class _RuntimeAssets(RoutingClass):
    def __init__(self, application):
        self.application = application

    @route(name="gramlot.js", media_type="text/javascript")
    def runtime(self, _request, **_query):
        self.application.require_method(_request, "GET", "HEAD")
        _request.response.set_header("Cache-Control", "no-cache")
        return b"" if _request.method == "HEAD" else runtime_asset().read_bytes()


class _Protocol(RoutingClass):
    def __init__(self, application):
        self.application = application

    @route(media_type="application/json")
    async def main(self, _request, body_raw=None, **_query):
        return await self.application.operation(_request, body_raw, "main")

    @route(media_type="application/json")
    async def source(self, _request, body_raw=None, **_query):
        return await self.application.operation(_request, body_raw, "source")

    @route(media_type="application/json")
    async def close(self, _request, body_raw=None, **_query):
        return await self.application.operation(_request, body_raw, "close")


class KajennNativeHtmlApplication(RoutedApplication):
    """A Kajenn routed application backed by ``gramlot.server.Host``.

    Declare it in the site recipe with ``request(body="raw")``: the protocol
    reads JSON with ``json.loads``, not with TYTX hydration.
    """

    def __init__(self, pages: str | Path, *, page_ttl: float = 1800,
                 max_pages: int = 1000, **kwargs) -> None:
        super().__init__(**kwargs)
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", self.mount or ""):
            raise ValueError("mount must be a single lowercase URL segment")
        prefix = f"/{self.mount}"
        self.host = Host(
            pages,
            runtime_url=f"{prefix}/assets/gramlot.js",
            main_url=f"{prefix}/gramlot/main",
            source_url=f"{prefix}/gramlot/source",
            close_url=f"{prefix}/gramlot/close",
            page_ttl=page_ttl,
            max_pages=max_pages,
        )
        self.add_branches([
            {"name": "assets", "instance": _RuntimeAssets(self)},
            {"name": "gramlot", "instance": _Protocol(self)},
        ])

    @route(media_type="text/html")
    async def index(self, *segments, _request, **_query):
        self.require_method(_request, "GET")
        owner = _request.cookies.get(OWNER_COOKIE) or token_urlsafe(24)
        try:
            opened = await self.host.open_page("/".join(segments), owner=owner)
        except PageNotFound as error:
            raise HTTPNotFound("Page not found") from error
        except HostCapacity as error:
            raise HTTPException(503, "Page capacity reached") from error
        _request.response.set_header("Cache-Control", "no-store")
        _request.response.set_cookie(
            OWNER_COOKIE, owner, path=f"/{self.mount}", httponly=True, samesite="lax"
        )
        return opened.html

    def require_method(self, request, *methods: str) -> None:
        if request.method not in methods:
            raise HTTPException(405, "Method not allowed")

    async def operation(self, request, body_raw: bytes | None, operation: str) -> str:
        self.require_method(request, "POST")
        if not self.raw_body:
            raise RuntimeError("KajennNativeHtmlApplication requires request(body='raw')")
        content_type = str(request.content_type or "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise HTTPUnsupportedMediaType("Expected application/json")
        raw = body_raw or b""
        if len(raw) > MAX_REQUEST_BYTES:
            raise HTTPException(413, "Request too large")
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict) or not isinstance(payload.get("pageId"), str):
                raise ValueError
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise HTTPBadRequest("Invalid JSON request") from error
        if operation == "source" and not isinstance(payload.get("params", {}), dict):
            raise HTTPBadRequest("Source params must be a dictionary")
        owner = request.cookies.get(OWNER_COOKIE)
        request.response.set_header("Cache-Control", "no-store")
        try:
            if operation == "main":
                return await self.host.main(payload["pageId"], owner=owner)
            if operation == "source":
                return await self.host.source(
                    payload["pageId"], payload.get("method"), payload.get("params", {}), owner=owner
                )
            self.host.close_page(payload["pageId"], owner=owner)
            return json.dumps({"ok": True})
        except PageExpired as error:
            raise HTTPNotFound("Unknown page") from error
        except SourceNotFound as error:
            raise HTTPNotFound("Unknown Source method") from error


__all__ = ["KajennNativeHtmlApplication"]
