# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Reusable, framework-neutral ASGI adapter for Gramlot native HTML."""

from __future__ import annotations

import asyncio
import json
from http.cookies import SimpleCookie
from pathlib import Path
from secrets import token_urlsafe
from typing import Any
from urllib.parse import unquote

from gramlot.server import (
    FileHost,
    HostCapacity,
    PageExpired,
    PageNotFound,
    SourceNotFound,
    runtime_asset,
)

JSON_MEDIA_TYPE = "application/json"
MAX_REQUEST_BYTES = 4096
OWNER_COOKIE = "gramlot_owner"


class NativeHtmlASGI:
    """Serve a trusted page directory through Gramlot's ``FileHost``.

    ``mount_path`` is passed to ``open_page`` as the mount prefix of browser URLs
    but is not expected in ASGI ``scope['path']``. This makes the adapter usable
    both at an ASGI root and behind a server which strips an application mount
    before dispatch.
    """

    def __init__(
        self,
        pages: str | Path,
        *,
        mount_path: str = "",
        page_ttl: float = 1800,
        max_pages: int = 1000,
    ) -> None:
        mount_path = "/" + mount_path.strip("/") if mount_path.strip("/") else ""
        self.mount_path = mount_path
        self.host = FileHost(
            pages,
            runtime_url="/assets/gramlot.js",
            main_url="/gramlot/main",
            source_url="/gramlot/source",
            close_url="/gramlot/close",
            page_ttl=page_ttl,
            max_pages=max_pages,
        )

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") == "lifespan":
            await self._lifespan(receive, send)
            return
        if scope.get("type") != "http":
            raise ValueError("NativeHtmlASGI supports HTTP only")
        method = scope.get("method", "GET").upper()
        path = unquote(scope.get("path", "/"))
        headers = {key.lower(): value for key, value in scope.get("headers", [])}

        if path == "/assets/gramlot.js":
            if method not in {"GET", "HEAD"}:
                await self._send(send, 405, b"", "text/plain", [(b"allow", b"GET, HEAD")])
                return
            body = b"" if method == "HEAD" else await self._runtime_bytes()
            await self._send(send, 200, body, "text/javascript; charset=utf-8")
            return

        operations = {
            "/gramlot/main": "main",
            "/gramlot/source": "source",
            "/gramlot/close": "close",
        }
        operation = operations.get(path)
        if operation is not None:
            if method != "POST":
                await self._send(send, 405, b"", "text/plain", [(b"allow", b"POST")])
                return
            await self._operation(operation, headers, receive, send)
            return

        if method != "GET":
            await self._send(send, 405, b"", "text/plain", [(b"allow", b"GET")])
            return
        owner = self._owner(headers) or token_urlsafe(24)
        try:
            opened = await self.host.open_page(path, owner=owner, prefix=self.mount_path)
        except PageNotFound:
            await self._send(send, 404, b"Page not found", "text/plain; charset=utf-8")
            return
        except HostCapacity:
            await self._send(send, 503, b"Page capacity reached", "text/plain; charset=utf-8")
            return
        cookie = f"{OWNER_COOKIE}={owner}; Path={self.mount_path or '/'}; HttpOnly; SameSite=Lax"
        await self._send(
            send,
            200,
            opened.html.encode(),
            "text/html; charset=utf-8",
            [(b"set-cookie", cookie.encode())],
        )

    async def _operation(self, operation, headers, receive, send) -> None:
        media_type = headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower()
        if media_type != JSON_MEDIA_TYPE.encode():
            await self._send(send, 415, b"Expected application/json", "text/plain; charset=utf-8")
            return
        try:
            payload = json.loads((await self._body(receive)).decode())
            if not isinstance(payload, dict) or not isinstance(payload.get("pageId"), str):
                raise ValueError
        except RequestTooLarge:
            await self._send(send, 413, b"Request too large", "text/plain; charset=utf-8")
            return
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            await self._send(send, 400, b"Invalid JSON request", "text/plain; charset=utf-8")
            return

        owner = self._owner(headers)
        if operation == "source" and not isinstance(payload.get("params", {}), dict):
            await self._send(
                send, 400, b"Source params must be a dictionary", "text/plain; charset=utf-8"
            )
            return
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
            await self._send(send, 404, b"Unknown page", "text/plain; charset=utf-8")
            return
        except SourceNotFound:
            await self._send(send, 404, b"Unknown Source method", "text/plain; charset=utf-8")
            return
        await self._send(send, 200, result.encode(), JSON_MEDIA_TYPE)

    async def _runtime_bytes(self) -> bytes:
        return await asyncio.to_thread(runtime_asset().read_bytes)

    async def _lifespan(self, receive, send) -> None:
        while True:
            event = await receive()
            if event["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif event["type"] == "lifespan.shutdown":
                self.host._pages.clear()
                await send({"type": "lifespan.shutdown.complete"})
                return

    @staticmethod
    async def _body(receive) -> bytes:
        body = bytearray()
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                raise ValueError("Disconnected")
            body.extend(event.get("body", b""))
            if len(body) > MAX_REQUEST_BYTES:
                raise RequestTooLarge
            if not event.get("more_body", False):
                return bytes(body)

    @staticmethod
    def _owner(headers: dict[bytes, bytes]) -> str | None:
        cookie = SimpleCookie()
        try:
            cookie.load(headers.get(b"cookie", b"").decode("latin-1"))
        except Exception:
            return None
        morsel = cookie.get(OWNER_COOKIE)
        return morsel.value if morsel else None

    @staticmethod
    async def _send(send, status: int, body: bytes, media_type: str,
                    headers: list[tuple[bytes, bytes]] | None = None) -> None:
        response_headers = [
            (b"content-type", media_type.encode()),
            (b"content-length", str(len(body)).encode()),
            (b"cache-control", b"no-store"),
        ]
        response_headers.extend(headers or [])
        await send({"type": "http.response.start", "status": status, "headers": response_headers})
        await send({"type": "http.response.body", "body": body})


class RequestTooLarge(ValueError):
    """Internal signal for a request body over the public 4 KiB limit."""


def create_asgi_application(pages: str | Path, **options: Any) -> NativeHtmlASGI:
    """Create a generic ASGI application for Uvicorn or another ASGI server."""

    return NativeHtmlASGI(pages, **options)


__all__ = ["NativeHtmlASGI", "create_asgi_application"]
