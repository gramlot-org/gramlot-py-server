# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""FastAPI integration for the Gramlot ``Host`` protocol."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from secrets import token_urlsafe

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
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
    ".js": "text/javascript; charset=utf-8",
}


class Pages:
    """Own a Gramlot ``FileHost`` and its FastAPI route translations.

    The routes are included at ``mount_path``, which is also passed to
    ``open_page`` as the mount prefix of browser URLs. The prefix without the
    final slash (``/py``) answers 301 to ``/py/``: pages link each other with
    relative URLs.

    GET and HEAD serve a ``.css`` or ``.js`` file whose real path is below the
    pages folder: the companions of ``FileHost`` (stylesheet, page module or
    ``_aux.js`` with the page ``Logic``) and ``Page.css`` files placed there.
    Every other file of the folder is not served.

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

    def mount(self, app: FastAPI) -> None:
        router = APIRouter(prefix=self.mount_path)
        router.add_api_route("/assets/gramlot.js", self.asset, methods=["GET", "HEAD"])
        router.add_api_route("/gramlot/main", self.main, methods=["POST"])
        router.add_api_route("/gramlot/source", self.source, methods=["POST"])
        router.add_api_route("/gramlot/close", self.close, methods=["POST"])
        if self.mount_path:
            router.add_api_route("", self.redirect, methods=["GET", "HEAD"])
        router.add_api_route("/", self.page, methods=["GET", "HEAD"])
        router.add_api_route("/{page_path:path}", self.page, methods=["GET", "HEAD"])
        app.include_router(router)
        app.router.add_event_handler("shutdown", self.shutdown)

    async def shutdown(self) -> None:
        self.host._pages.clear()

    async def redirect(self, request: Request) -> Response:
        query = request.url.query
        return RedirectResponse(self.mount_path + "/" + (f"?{query}" if query else ""), 301)

    async def asset(self, request: Request) -> Response:
        body = b"" if request.method == "HEAD" else runtime_asset().read_bytes()
        return Response(body, media_type="text/javascript", headers={"Cache-Control": "no-cache"})

    async def page(self, request: Request, page_path: str = "") -> Response:
        asset = self.assets.get("/" + page_path)
        if asset is not None:
            return await self.static(request, asset)
        suffix = next((suffix for suffix in COMPANION_MEDIA_TYPES if page_path.endswith(suffix)), None)
        if suffix is not None:
            return await self.companion(request, page_path, suffix)
        if request.method != "GET":
            return Response(status_code=405, headers={"Allow": "GET"})
        owner = request.cookies.get(OWNER_COOKIE) or token_urlsafe(24)
        try:
            opened = await self.host.open_page(page_path, owner=owner, prefix=self.mount_path)
        except PageNotFound:
            return Response("Page not found", status_code=404)
        except HostCapacity:
            return Response("Page capacity reached", status_code=503)
        headers = {"Cache-Control": "no-store"}
        if self.content_security_policy is not None:
            headers["Content-Security-Policy"] = self.content_security_policy.replace("{nonce}", opened.nonce)
        response = HTMLResponse(opened.html, headers=headers)
        response.set_cookie(
            OWNER_COOKIE,
            owner,
            path=self.mount_path or "/",
            httponly=True,
            samesite="lax",
        )
        return response

    async def static(self, request: Request, asset) -> Response:
        """Serve one file of ``assets`` with its media type."""
        body = b"" if request.method == "HEAD" else await asyncio.to_thread(Path(asset["file"]).read_bytes)
        return Response(body, headers={"Content-Type": asset["type"], "Cache-Control": "no-store"})

    async def companion(self, request: Request, page_path: str, suffix: str) -> Response:
        """Serve the file of ``page_path`` when its real path is below the pages folder."""
        root = self.host.pages_dir.resolve()
        real = root.joinpath(*page_path.strip("/").split("/")).resolve()
        if not (real.is_relative_to(root) and real.is_file()):
            return Response("Not found", status_code=404)
        body = b"" if request.method == "HEAD" else await asyncio.to_thread(real.read_bytes)
        return Response(body, headers={"Content-Type": COMPANION_MEDIA_TYPES[suffix],
                                       "Cache-Control": "no-store"})

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


class Application(FastAPI):
    """Ready-made FastAPI application serving Gramlot pages."""

    def __init__(self, pages: str | Path, *, mount_path: str = "", page_ttl: float = 1800,
                 max_pages: int = 1000, content_security_policy: str | None = None,
                 assets: dict | None = None, **fastapi_options) -> None:
        super().__init__(**fastapi_options)
        self.gramlot_pages = mount_pages(
            self, pages, mount_path=mount_path, page_ttl=page_ttl, max_pages=max_pages,
            content_security_policy=content_security_policy, assets=assets,
        )


def mount_pages(app: FastAPI, pages: str | Path, **options) -> Pages:
    """Mount the bounded Gramlot page protocol on an existing FastAPI app."""

    integration = Pages(pages, **options)
    integration.mount(app)
    return integration


__all__ = ["Application", "Pages", "mount_pages"]
