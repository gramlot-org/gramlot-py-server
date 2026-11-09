# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""ASGI application for Uvicorn or another ASGI server serving Gramlot pages."""

from __future__ import annotations

import asyncio

import inspect
import json
import logging
from functools import partial
from pathlib import Path
from typing import Any

from genro_tytx import to_tytx
from gramlot.server.upload import _UploadRegistry

from gramlot_py_server import base
from gramlot_py_server.store_channel import _StoreChannel
from gramlot_py_server.terminal_channel import _TerminalChannel
from gramlot_py_server.gallery import add_gallery
from gramlot_py_server.scaffold import add_new


logger = logging.getLogger(__name__)


class _Disconnected(Exception):
    """The ASGI peer disconnected."""


class _AsgiWebSocket:
    """The small socket interface used by the channel, backed by raw ASGI."""

    def __init__(self, receive, send):
        self.receive, self.send = receive, send

    async def accept(self):
        if (await self.receive())["type"] != "websocket.connect":
            raise _Disconnected()
        await self.send({"type": "websocket.accept"})

    async def refuse(self, code):
        await self.receive()
        await self.close(code)

    async def close(self, code):
        await self.send({"type": "websocket.close", "code": code})

    async def receive_text(self):
        event = await self.receive()
        if event["type"] == "websocket.disconnect":
            raise _Disconnected()
        if event["type"] != "websocket.receive" or not isinstance(event.get("text"), str):
            raise ValueError("Expected TYTX text")
        return event["text"]

    async def send_text(self, text):
        await self.send({"type": "websocket.send", "text": text})

    async def receive_bytes(self):
        event = await self.receive()
        if event["type"] == "websocket.disconnect":
            raise _Disconnected()
        if event["type"] != "websocket.receive" or not isinstance(event.get("bytes"), bytes):
            raise ValueError("Expected a binary frame")
        return event["bytes"]

    async def send_bytes(self, data):
        await self.send({"type": "websocket.send", "bytes": data})


class Application(base.Adapter):
    """Serve a trusted page directory through Gramlot's ``GramlotFileServer``.

    ``mount_path`` is the prefix of the request paths and is passed to
    ``open_page`` as the mount prefix of browser URLs. With ``mount_path="/py"``
    the application answers ``/py/…`` with the prefix removed and 404 to every
    other path, as the Django, Flask and FastAPI adapters do. ``/py`` without the
    final slash answers 301 to ``/py/``: pages link each other with relative URLs.
    The path is the ASGI ``scope["path"]``, which the server has already decoded.

    The HTTP rules, the same in every adapter, are those of ``gramlot_py_server.base``.
    """

    def __init__(self, pages: str | Path, *, websocket: bool = False, identity_provider=None, **options: Any) -> None:
        if identity_provider is not None and not callable(identity_provider):
            raise TypeError("identity_provider must be callable or None")
        self.identity_provider = identity_provider
        super().__init__(pages, **options)
        self.gramlot_server._uploads = _UploadRegistry()
        self._store_mutations = asyncio.Lock()
        self._store_channel = _StoreChannel(self.gramlot_server, self._invoke_store)
        self._terminal_channel = _TerminalChannel(self.gramlot_server)
        self.gramlot_server.websocket_url = "/gramlot/store" if websocket else None

    async def _invoke_store(self, function, *args, **kwargs):
        """Run synchronous store recipes off-loop, serially across this host's sockets."""
        async with self._store_mutations:
            worker = asyncio.create_task(asyncio.to_thread(function, *args, **kwargs))
            try:
                return await asyncio.shield(worker)
            except asyncio.CancelledError:
                # Drain a non-interruptible Python worker before closing its Bags.
                while not worker.done():
                    try:
                        await asyncio.shield(worker)
                    except asyncio.CancelledError:
                        continue
                    except Exception:
                        break
                if not worker.cancelled():
                    worker.exception()
                raise

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") == "websocket":
            await self._websocket(scope, receive, send)
            return
        if scope.get("type") == "lifespan":
            await self._lifespan(receive, send)
            return
        if scope.get("type") != "http":
            raise ValueError("Application supports HTTP only")
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        path, query = scope.get("path", "/"), scope.get("query_string", b"").decode("latin-1")
        if self.mount_path and path == self.mount_path:
            reply = self.redirect(query)
        elif self.mount_path and not path.startswith(self.mount_path + "/"):
            reply = self.reply(404, "Not found")
        else:
            relative = path[len(self.mount_path):]
            method = scope.get("method", "GET").upper()
            owner = self.owner_of(headers.get(b"cookie", b"").decode("latin-1"))
            if relative == "/gramlot/upload":
                reply = await self._upload(scope, headers, receive, owner) if method == "POST" else self.refuse("POST")
            else:
                identity = await self._identity(scope) if relative == self.gramlot_server.rpc_url and method == "POST" else None
                body = partial(self._body, receive)
                if relative == self.gramlot_server.close_url and method == "POST":
                    data = await body()
                    async def body():
                        return data
                reply = await self.handle(base.Request(
                    method=method, path=relative, body=body, query=query,
                    content_type=headers.get(b"content-type", b"").decode("latin-1"),
                    owner=owner, identity=identity,
                    if_none_match=headers.get(b"if-none-match", b"").decode("latin-1"),
                    if_modified_since=headers.get(b"if-modified-since", b"").decode("latin-1"),
                ))
                if relative == self.gramlot_server.close_url and method == "POST" and reply.status == 200:
                    payload = json.loads(data)
                    await self.gramlot_server._uploads.close_page(payload["pageId"], owner)
        await self._send(send, reply)

    async def _websocket(self, scope, receive, send):
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        if scope["path"] == self.mount_path + "/gramlot/terminal":
            await self._terminal_channel.serve(
                _AsgiWebSocket(receive, send), scope,
                owner=self.owner_of(headers.get(b"cookie", b"").decode("latin-1")),
                path=self.mount_path + "/gramlot/terminal", disconnect_error=_Disconnected,
                identity=await self._identity(scope),
            )
            return
        await self._store_channel.serve(
            _AsgiWebSocket(receive, send), scope,
            owner=self.owner_of(headers.get(b"cookie", b"").decode("latin-1")),
            path=self.mount_path + "/gramlot/store", disconnect_error=_Disconnected,
        )

    async def _lifespan(self, receive, send) -> None:
        while True:
            event = await receive()
            if event["type"] == "lifespan.startup":
                self._upload_sweeper = asyncio.create_task(self._sweep_uploads())
                await send({"type": "lifespan.startup.complete"})
            elif event["type"] == "lifespan.shutdown":
                sweeper = getattr(self, "_upload_sweeper", None)
                if sweeper:
                    sweeper.cancel()
                    await asyncio.gather(sweeper, return_exceptions=True)
                await self.gramlot_server._uploads.close_all()
                self.shutdown()
                await send({"type": "lifespan.shutdown.complete"})
                return

    async def _identity(self, scope):
        if self.identity_provider is None:
            return None
        value = self.identity_provider(scope)
        return await value if inspect.isawaitable(value) else value

    async def _upload(self, scope, headers, receive, owner):
        media = headers.get(b"content-type", b"").split(b";", 1)[0].strip().lower()
        if media != b"application/octet-stream":
            return self.reply(415, "Expected application/octet-stream")
        server = self.gramlot_server
        try:
            page_id = headers[b"x-gramlot-page-id"].decode("ascii")
            transfer_id = headers[b"x-gramlot-transfer-id"].decode("ascii")
            token = headers[b"x-gramlot-upload-token"].decode("ascii")
            transfer = server._upload_admit(page_id=page_id, owner=owner, identity=await self._identity(scope),
                transfer_id=transfer_id, token=token)
        except (KeyError, UnicodeError, PermissionError, LookupError, ValueError):
            return self.reply(403, "Upload admission refused")
        try:
            while True:
                event = await receive()
                if event["type"] == "http.disconnect":
                    raise ConnectionError("Upload disconnected")
                chunk = event.get("body", b"")
                for offset in range(0, len(chunk), 65536):
                    await transfer.write(chunk[offset:offset + 65536])
                    server._uploads.touch(transfer_id, page_id, owner)
                if not event.get("more_body", False):
                    break
            result = await transfer.finish()
            return self.reply(200, to_tytx(result), "application/json")
        except asyncio.CancelledError:
            try:
                await asyncio.shield(transfer.abort())
            finally:
                raise
        except Exception:
            try:
                await transfer.abort()
            except Exception:
                pass
            return self.reply(400, "Upload did not complete; query its status")

    async def _sweep_uploads(self):
        while True:
            await asyncio.sleep(30)
            try:
                server = self.gramlot_server
                server._prune()
                await server._uploads.expire()
                records = list(server._uploads._records.values())
                for page_id, owner in {(r["page_id"], r["owner"]) for r in records}:
                    if page_id not in server._pages:
                        await server._uploads.close_page(page_id, owner)
            except Exception:
                logger.exception("Upload cleanup failed; unresolved records are retained")

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
    async def _send(send, reply: base.Reply) -> None:
        headers = {
            "content-type": reply.content_type,
            # A 304 carries no Content-Length: there it would state the size of the file.
            **({} if reply.status == 304 else {"content-length": str(len(reply.body))}),
            **{name.lower(): value for name, value in reply.headers},
        }
        headers = [(name.encode("latin-1"), value.encode("latin-1")) for name, value in headers.items()]
        await send({"type": "http.response.start", "status": reply.status, "headers": headers})
        await send({"type": "http.response.body", "body": reply.body})


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
