# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""ASGI application for Uvicorn or another ASGI server serving Gramlot pages."""

from __future__ import annotations

import asyncio
import json
import logging
from http.cookies import SimpleCookie
from importlib.resources import files
from mimetypes import MimeTypes
from pathlib import Path
from secrets import token_urlsafe
from typing import Any
from urllib.parse import unquote, parse_qs, urlsplit

from genro_tytx import from_tytx, to_tytx

from gramlot.server import (
    GramlotFileServer,
    InvalidRequest,
    PageNotFound,
    PageExpired,
    ServerCapacity,
    runtime_asset,
)

from gramlot_py_server.gallery import add_gallery
from gramlot_py_server.scaffold import add_new

JSON_MEDIA_TYPE = "application/json"
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
    """Serve a trusted page directory through Gramlot's ``GramlotFileServer``.

    ``mount_path`` is the prefix of the request paths and is passed to
    ``open_page`` as the mount prefix of browser URLs. With ``mount_path="/py"``
    the application answers ``/py/…`` with the prefix removed and 404 to every
    other path, as the Django, Flask and FastAPI adapters do. ``/py`` without the
    final slash answers 301 to ``/py/``: pages link each other with relative URLs.

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

    def __init__(
        self,
        pages: str | Path,
        *,
        mount_path: str = "",
        page_ttl: float = 1800,
        max_pages: int = 1000,
        content_security_policy: str | None = None,
        assets: dict[str, dict[str, Any]] | None = None,
        collections=(),
        websocket: bool = False,
    ) -> None:
        mount_path = "/" + mount_path.strip("/") if mount_path.strip("/") else ""
        self.mount_path = mount_path
        self.content_security_policy = content_security_policy
        self.assets = dict(assets or {})
        self._store_channels = {}
        self.server = GramlotFileServer(
            pages,
            runtime_url="/assets/gramlot.js",
            rpc_url="/gramlot/rpc",
            close_url="/gramlot/close",
            page_ttl=page_ttl,
            max_pages=max_pages, collections=collections,
            websocket_url="/gramlot/store" if websocket else None,
        )

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") == "websocket":
            await self._websocket(scope, receive, send)
            return
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

        if path == "/app.webmanifest":
            if method not in {"GET", "HEAD"}:
                await self._send(send, 405, b"", "text/plain", [(b"allow", b"GET, HEAD")])
                return
            try:
                manifest = await self.server.page_manifest(prefix=self.mount_path)
            except PageNotFound:
                await self._send(send, 404, b"Not found", "text/plain")
                return
            body = b"" if method == "HEAD" else json.dumps(manifest).encode()
            await self._send(send, 200, body, "application/manifest+json")
            return

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

        if path in ("/gramlot/rpc", "/gramlot/close"):
            if method != "POST":
                await self._send(send, 405, b"", "text/plain", [(b"allow", b"POST")])
                return
            await self._operation(path, headers, receive, send)
            return

        if method != "GET":
            await self._send(send, 405, b"", "text/plain", [(b"allow", b"GET")])
            return
        # As on a static host, <path>/index.html is the page <path> and /index.html the index.
        if path.endswith("/index.html"):
            path = path.removesuffix("index.html")
        owner = self._owner(headers) or token_urlsafe(24)
        try:
            opened = await self.server.open_page(path, owner=owner, prefix=self.mount_path)
        except PageNotFound:
            await self._send(send, 404, b"Page not found", "text/plain; charset=utf-8")
            return
        except ServerCapacity:
            await self._send(send, 503, b"Page capacity reached", "text/plain; charset=utf-8")
            return
        cookie = f"{OWNER_COOKIE}={owner}; Path={self.mount_path or '/'}; HttpOnly; SameSite=Lax"
        response_headers = [(b"set-cookie", cookie.encode())]
        if self.content_security_policy is not None:
            policy = self.content_security_policy.replace("{nonce}", opened.nonce)
            response_headers.append((b"content-security-policy", policy.encode()))
        await self._send(send, 200, opened.html.encode(), "text/html; charset=utf-8", response_headers)

    async def _websocket(self, scope, receive, send):
        """One primary socket multiplexes owned page stores and asynchronous RPC."""
        if (await receive())["type"] != "websocket.connect":
            return
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        owner = self._owner(headers)
        try:
            if self.server.websocket_url is None or scope["path"] != self.mount_path + "/gramlot/store":
                raise ValueError("Unknown WebSocket route")
            origin = urlsplit(headers.get(b"origin", b"").decode("ascii"))
            scheme = "https" if scope["scheme"] == "wss" else "http"
            if origin.scheme != scheme or origin.netloc != headers.get(b"host", b"").decode("ascii"):
                raise ValueError("Origin does not match")
            query = parse_qs(scope.get("query_string", b"").decode("ascii"), strict_parsing=True)
            if set(query) != {"pageId"} or len(query["pageId"]) != 1:
                raise ValueError("Expected a page ID")
            page_id = query["pageId"][0]
            store = self.server.page_store(page_id, owner=owner)
            if page_id in self._store_channels:
                raise ValueError("Page already has a store channel")
        except (ValueError, KeyError, PageExpired, UnicodeError):
            await send({"type": "websocket.close", "code": 1008})
            return
        outgoing = asyncio.Queue(maxsize=256)
        pages = {page_id: (store, set())}
        calls = {}
        self._store_channels[page_id] = pages

        def detach(target):
            for (call_page, _), task in calls.items():
                if call_page == target:
                    task.cancel()
            target_store, binders = pages.pop(target)
            for binder in binders:
                target_store.unsubscribe(binder)
            self._store_channels.pop(target, None)
            self.server.close_page(target, owner=owner)

        def deliver(wire, target):
            # Freeze the complete envelope now, before another controller mutates Data.
            outgoing.put_nowait(to_tytx(dict(from_tytx(wire), pageId=target)))

        def live_store(target):
            try:
                return self.server.page_store(target, owner=owner)
            except PageExpired:
                if target == page_id:
                    raise
                # An HTTP close beacon may arrive before the parent's detach.
                outgoing.put_nowait(to_tytx(dict(op="closed", pageId=target)))
                return None

        incoming = asyncio.create_task(receive())
        pending = asyncio.create_task(outgoing.get())
        try:
            self.server.connect_page_channel(page_id, lambda wire: deliver(wire, page_id), owner=owner)
            await send({"type": "websocket.accept"})
            while True:
                completed, _ = await asyncio.wait(
                    (incoming, pending, *calls.values()), timeout=self.server.page_ttl,
                    return_when=asyncio.FIRST_COMPLETED)
                if not completed:
                    for target in pages:
                        live_store(target)
                    continue
                for key, task in list(calls.items()):
                    if task not in completed:
                        continue
                    del calls[key]
                    if not task.cancelled():
                        wire = task.result()
                        if key[0] in pages:
                            deliver(wire, key[0])
                if pending in completed:
                    wire = pending.result()
                    if from_tytx(wire)["pageId"] in pages:
                        await send({"type": "websocket.send", "text": wire})
                    pending = asyncio.create_task(outgoing.get())
                if incoming not in completed:
                    continue
                event = incoming.result()
                if event["type"] == "websocket.disconnect":
                    return
                if event["type"] != "websocket.receive" or not isinstance(event.get("text"), str):
                    raise ValueError("Expected TYTX text")
                self.server.page_store(page_id, owner=owner)
                message = from_tytx(event["text"])
                if not isinstance(message, dict) or not isinstance(message.get("pageId"), str):
                    raise ValueError("Invalid page identity")
                target = message["pageId"]
                operation = message.get("op")
                if operation == "attach":
                    if target in self._store_channels:
                        raise ValueError("Page already has a store channel")
                    target_store = self.server.page_store(target, owner=owner)
                    self.server.connect_page_channel(target, lambda wire, target=target: deliver(wire, target), owner=owner)
                    pages[target] = (target_store, set())
                    self._store_channels[target] = pages
                    incoming = asyncio.create_task(receive())
                    continue
                if target not in pages:
                    raise ValueError("Page is not attached to this channel")
                if operation == "detach":
                    if target == page_id:
                        raise ValueError("Cannot detach the primary page")
                    detach(target)
                    incoming = asyncio.create_task(receive())
                    continue
                store = live_store(target)
                if store is None:
                    incoming = asyncio.create_task(receive())
                    continue
                if operation == "publish":
                    call_id = message.get("id")
                    if not isinstance(call_id, str) or not call_id or (target, call_id) in calls:
                        raise ValueError("Invalid or duplicate publication ID")
                    wire, dispatch = self.server.prepare_publish(event["text"], owner=owner)
                    # Send acceptance before entering application code, not merely enqueue it.
                    await send({"type": "websocket.send",
                                "text": to_tytx(dict(from_tytx(wire), pageId=target))})
                    if dispatch is not None:
                        try:
                            dispatch()
                        except asyncio.QueueFull:
                            raise
                        except Exception:
                            logging.getLogger(__name__).exception("PageStore publication subscriber failed")
                    incoming = asyncio.create_task(receive())
                    continue
                if operation is None or operation == "cancel":
                    call_id = message.get("id")
                    if not isinstance(call_id, str) or not call_id:
                        raise ValueError("Missing RPC ID")
                    key = (target, call_id)
                    if operation == "cancel":
                        if key in calls:
                            calls[key].cancel()
                    else:
                        if "op" in message:
                            raise ValueError("RPC envelope cannot declare an operation")
                        if key in calls:
                            raise ValueError("Duplicate RPC ID")
                        if len(calls) >= 256:
                            raise ValueError("Too many concurrent RPC calls")
                        calls[key] = asyncio.create_task(self.server.call(event["text"], owner=owner))
                    incoming = asyncio.create_task(receive())
                    continue
                binders = pages[target][1]
                binder_id = message.get("binderId")
                if not isinstance(binder_id, str) or not binder_id:
                    raise ValueError("Missing binder ID")
                if operation == "subscribe":
                    store.subscribe(binder_id, message["path"], lambda wire, target=target: deliver(wire, target))
                    binders.add(binder_id)
                elif binder_id not in binders:
                    raise ValueError("Unknown subscription")
                elif operation == "unsubscribe":
                    store.unsubscribe(binder_id)
                    binders.remove(binder_id)
                elif operation == "change":
                    store.change(binder_id, message)
                else:
                    raise ValueError("Unknown store operation")
                incoming = asyncio.create_task(receive())
        except (ValueError, KeyError, TypeError, PageExpired):
            await send({"type": "websocket.close", "code": 1008})
        except Exception:
            await send({"type": "websocket.close", "code": 1011})
            raise
        finally:
            incoming.cancel()
            pending.cancel()
            for task in calls.values():
                task.cancel()
            await asyncio.gather(incoming, pending, *calls.values(), return_exceptions=True)
            calls.clear()
            # Preserve the PoC lifetime: socket loss closes every attached page.
            for target in list(pages):
                detach(target)

    async def _operation(self, path, headers, receive, send) -> None:
        media_type = headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower()
        if media_type != JSON_MEDIA_TYPE.encode():
            await self._send(send, 415, b"Expected application/json", "text/plain; charset=utf-8")
            return
        try:
            text = (await self._body(receive)).decode()
        except UnicodeDecodeError:
            await self._send(send, 400, b"Request body is not UTF-8", "text/plain; charset=utf-8")
            return
        owner = self._owner(headers)
        if path == "/gramlot/rpc":
            try:
                result = await self.server.call(text, owner=owner)
            except InvalidRequest:
                await self._send(send, 400, b"Invalid envelope", "text/plain; charset=utf-8")
                return
            await self._send(send, 200, result.encode(), JSON_MEDIA_TYPE)
            return
        try:
            payload = json.loads(text)
            if not isinstance(payload, dict) or not isinstance(payload.get("pageId"), str):
                raise ValueError("Missing pageId")
        except ValueError:
            await self._send(send, 400, b"Invalid JSON request", "text/plain; charset=utf-8")
            return
        self.server.close_page(payload["pageId"], owner=owner)
        await self._send(send, 200, json.dumps({"ok": True}).encode(), JSON_MEDIA_TYPE)

    def _companion(self, path: str) -> Path | None:
        """Return the file of ``path`` when its real path is below the pages folder."""
        root = self.server.pages_dir.resolve()
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
                self.server.close_all()
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
