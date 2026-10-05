# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""ASGI application for Uvicorn or another ASGI server serving Gramlot pages."""

from __future__ import annotations

import asyncio
import json
from http.cookies import SimpleCookie
from importlib.resources import files
from mimetypes import MimeTypes
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

from gramlot_py_server.gallery import add_gallery
from gramlot_py_server.scaffold import add_new

JSON_MEDIA_TYPE = "application/json"
MAX_REQUEST_BYTES = 4096
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


class Application:
    """Serve a trusted page directory through Gramlot's ``FileHost``.

    ``mount_path`` is the prefix of the request paths and is passed to
    ``open_page`` as the mount prefix of browser URLs. With ``mount_path="/py"``
    the application answers ``/py/…`` with the prefix removed and 404 to every
    other path, as the Django, Flask and FastAPI adapters do. ``/py`` without the
    final slash answers 301 to ``/py/``: pages link each other with relative URLs.

    GET and HEAD serve a ``.css`` or ``.js`` file whose real path is below the
    pages folder: the companions of ``FileHost`` (stylesheet, page module or
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

    def __init__(
        self,
        pages: str | Path,
        *,
        mount_path: str = "",
        page_ttl: float = 1800,
        max_pages: int = 1000,
        content_security_policy: str | None = None,
        assets: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        mount_path = "/" + mount_path.strip("/") if mount_path.strip("/") else ""
        self.mount_path = mount_path
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

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") == "lifespan":
            await self._lifespan(receive, send)
            return
        if scope.get("type") != "http":
            raise ValueError("Application supports HTTP only")
        method = scope.get("method", "GET").upper()
        path = unquote(scope.get("path", "/"))
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        if self.mount_path:
            if path == self.mount_path:
                location = self.mount_path + "/"
                if scope.get("query_string"):
                    location += "?" + scope["query_string"].decode("latin-1")
                await self._send(send, 301, b"", "text/plain", [(b"location", location.encode())])
                return
            if not path.startswith(self.mount_path + "/"):
                await self._send(send, 404, b"Not found", "text/plain; charset=utf-8")
                return
            path = path[len(self.mount_path):]

        if path == "/assets/gramlot.js":
            if method not in {"GET", "HEAD"}:
                await self._send(send, 405, b"", "text/plain", [(b"allow", b"GET, HEAD")])
                return
            body = b"" if method == "HEAD" else await self._runtime_bytes()
            await self._send(send, 200, body, "text/javascript; charset=utf-8")
            return

        asset = theme_file(path) or self.assets.get(path)
        if asset is not None:
            if method not in {"GET", "HEAD"}:
                await self._send(send, 405, b"", "text/plain", [(b"allow", b"GET, HEAD")])
                return
            body = b"" if method == "HEAD" else await asyncio.to_thread(Path(asset["file"]).read_bytes)
            await self._send(send, 200, body, asset["type"])
            return

        suffix = next((suffix for suffix in COMPANION_MEDIA_TYPES if path.endswith(suffix)), None)
        if suffix is not None:
            if method not in {"GET", "HEAD"}:
                await self._send(send, 405, b"", "text/plain", [(b"allow", b"GET, HEAD")])
                return
            filename = self._companion(path)
            if filename is None:
                await self._send(send, 404, b"Not found", "text/plain; charset=utf-8")
                return
            body = b"" if method == "HEAD" else await asyncio.to_thread(filename.read_bytes)
            await self._send(send, 200, body, COMPANION_MEDIA_TYPES[suffix])
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
        # As on a static host, <path>/index.html is the page <path> and /index.html the index.
        if path.endswith("/index.html"):
            path = path.removesuffix("index.html")
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
        response_headers = [(b"set-cookie", cookie.encode())]
        if self.content_security_policy is not None:
            policy = self.content_security_policy.replace("{nonce}", opened.nonce)
            response_headers.append((b"content-security-policy", policy.encode()))
        await self._send(send, 200, opened.html.encode(), "text/html; charset=utf-8", response_headers)

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

    def _companion(self, path: str) -> Path | None:
        """Return the file of ``path`` when its real path is below the pages folder."""
        root = self.host.pages_dir.resolve()
        real = root.joinpath(*path.strip("/").split("/")).resolve()
        return real if real.is_relative_to(root) and real.is_file() else None

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


def create_application(pages: str | Path, **options: Any) -> Application:
    """Create a generic ASGI application for Uvicorn or another ASGI server."""

    return Application(pages, **options)


def serve(pages: str | Path, *, host: str = "127.0.0.1", port: int = 8000, **options: Any) -> None:
    """Serve ``pages`` with Uvicorn until it stops; ``options`` are those of ``Application``."""
    import uvicorn

    uvicorn.run(create_application(pages, **options), host=host, port=port)


def commands(verbs) -> None:
    """The verbs of ``gramlot uvicorn``: an entry point of ``gramlot_py_server.commands``."""
    add_new(verbs, "uvicorn", start="uvicorn app:application", url="http://127.0.0.1:8000/")
    add_gallery(verbs, "uvicorn", serve)


__all__ = ["Application", "create_application"]
