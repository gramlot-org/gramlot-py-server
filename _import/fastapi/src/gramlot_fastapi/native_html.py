# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""FastAPI integration for Gramlot's native HTML ``Host`` contract."""

from __future__ import annotations

import json
from pathlib import Path
from secrets import token_urlsafe

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from gramlot.server import Host, HostCapacity, PageExpired, PageNotFound, SourceNotFound, runtime_asset

MAX_REQUEST_BYTES = 4096
OWNER_COOKIE = "gramlot_owner"


class NativeHtmlPages:
    """Own one neutral Host and its FastAPI route translations."""

    def __init__(self, pages: str | Path, *, prefix: str = "", page_ttl=1800, max_pages=1000):
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

    def mount(self, app: FastAPI) -> None:
        router = APIRouter(prefix=self.prefix)
        router.add_api_route("/assets/gramlot.js", self.asset, methods=["GET", "HEAD"])
        router.add_api_route("/gramlot/main", self.main, methods=["POST"])
        router.add_api_route("/gramlot/source", self.source, methods=["POST"])
        router.add_api_route("/gramlot/close", self.close, methods=["POST"])
        router.add_api_route("/", self.page, methods=["GET"])
        router.add_api_route("/{page_path:path}", self.page, methods=["GET"])
        app.include_router(router)
        app.router.add_event_handler("shutdown", self.shutdown)

    async def shutdown(self) -> None:
        self.host._pages.clear()

    async def asset(self, request: Request) -> Response:
        body = b"" if request.method == "HEAD" else runtime_asset().read_bytes()
        return Response(body, media_type="text/javascript", headers={"Cache-Control": "no-cache"})

    async def page(self, request: Request, page_path: str = "") -> Response:
        owner = request.cookies.get(OWNER_COOKIE) or token_urlsafe(24)
        try:
            opened = await self.host.open_page(page_path, owner=owner)
        except PageNotFound:
            return Response("Page not found", status_code=404)
        except HostCapacity:
            return Response("Page capacity reached", status_code=503)
        response = HTMLResponse(opened.html, headers={"Cache-Control": "no-store"})
        response.set_cookie(
            OWNER_COOKIE,
            owner,
            path=self.prefix or "/",
            httponly=True,
            samesite="lax",
        )
        return response

    async def main(self, request: Request) -> Response:
        return await self._operation(request, "main")

    async def source(self, request: Request) -> Response:
        return await self._operation(request, "source")

    async def close(self, request: Request) -> Response:
        return await self._operation(request, "close")

    async def _operation(self, request: Request, operation: str) -> Response:
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            return Response("Expected application/json", status_code=415)
        try:
            raw = await self._body(request)
            payload = json.loads(raw)
            if not isinstance(payload, dict) or not isinstance(payload.get("pageId"), str):
                raise ValueError
        except RequestTooLarge:
            return Response("Request too large", status_code=413)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return Response("Invalid JSON request", status_code=400)
        owner = request.cookies.get(OWNER_COOKIE)
        if operation == "source" and not isinstance(payload.get("params", {}), dict):
            return Response("Source params must be a dictionary", status_code=400)
        try:
            if operation == "main":
                result = await self.host.main(payload["pageId"], owner=owner)
            elif operation == "source":
                result = await self.host.source(
                    payload["pageId"], payload.get("method"), payload.get("params", {}), owner=owner
                )
            else:
                self.host.close_page(payload["pageId"], owner=owner)
                result = json.dumps({"ok": True})
        except PageExpired:
            return Response("Unknown page", status_code=404)
        except SourceNotFound:
            return Response("Unknown Source method", status_code=404)
        return Response(result, media_type="application/json", headers={"Cache-Control": "no-store"})

    @staticmethod
    async def _body(request: Request) -> str:
        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > MAX_REQUEST_BYTES:
            raise RequestTooLarge
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAX_REQUEST_BYTES:
                raise RequestTooLarge
        return body.decode()


class RequestTooLarge(ValueError):
    pass


class NativeHtmlApplication(FastAPI):
    """Ready-made FastAPI application for native HTML Gramlot pages."""

    def __init__(self, pages: str | Path, *, prefix: str = "", page_ttl=1800,
                 max_pages=1000, **fastapi_options):
        super().__init__(**fastapi_options)
        self.gramlot_native_html = mount_native_html(
            self, pages, prefix=prefix, page_ttl=page_ttl, max_pages=max_pages
        )


def mount_native_html(app: FastAPI, pages: str | Path, **options) -> NativeHtmlPages:
    """Mount the bounded native HTML protocol on an existing FastAPI app."""

    integration = NativeHtmlPages(pages, **options)
    integration.mount(app)
    return integration


__all__ = ["NativeHtmlApplication", "NativeHtmlPages", "mount_native_html"]
