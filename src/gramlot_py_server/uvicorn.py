# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""ASGI application for Uvicorn or another ASGI server serving Gramlot pages."""

from __future__ import annotations

import asyncio
import logging
from urllib.parse import parse_qs, urlsplit

from genro_tytx import from_tytx, to_tytx
from gramlot.server import PageExpired

from functools import partial
from pathlib import Path
from typing import Any

from gramlot_py_server import base
from gramlot_py_server.gallery import add_gallery
from gramlot_py_server.scaffold import add_new


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

    def __init__(self, pages: str | Path, *, websocket: bool = False, **options: Any) -> None:
        super().__init__(pages, **options)
        self._store_channels = {}
        self.gramlot_server.websocket_url = "/gramlot/store" if websocket else None

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
            reply = await self.handle(base.Request(
                method=scope.get("method", "GET").upper(),
                path=path[len(self.mount_path):],
                body=partial(self._body, receive),
                query=query,
                content_type=headers.get(b"content-type", b"").decode("latin-1"),
                owner=self.owner_of(headers.get(b"cookie", b"").decode("latin-1")),
            ))
        await self._send(send, reply)

    async def _websocket(self, scope, receive, send):
        """One primary socket multiplexes owned page stores and asynchronous RPC."""
        if (await receive())["type"] != "websocket.connect":
            return
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        owner = self.owner_of(headers.get(b"cookie", b"").decode("latin-1"))
        try:
            if self.gramlot_server.websocket_url is None or scope["path"] != self.mount_path + "/gramlot/store":
                raise ValueError("Unknown WebSocket route")
            origin = urlsplit(headers.get(b"origin", b"").decode("ascii"))
            scheme = "https" if scope["scheme"] == "wss" else "http"
            if origin.scheme != scheme or origin.netloc != headers.get(b"host", b"").decode("ascii"):
                raise ValueError("Origin does not match")
            query = parse_qs(scope.get("query_string", b"").decode("ascii"), strict_parsing=True)
            if set(query) != {"pageId"} or len(query["pageId"]) != 1:
                raise ValueError("Expected a page ID")
            page_id = query["pageId"][0]
            store = self.gramlot_server.page_store(page_id, owner=owner)
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
            self.gramlot_server.close_page(target, owner=owner)

        def deliver(wire, target):
            # Freeze the complete envelope now, before another controller mutates Data.
            outgoing.put_nowait(to_tytx(dict(from_tytx(wire), pageId=target)))

        def live_store(target):
            try:
                return self.gramlot_server.page_store(target, owner=owner)
            except PageExpired:
                if target == page_id:
                    raise
                # An HTTP close beacon may arrive before the parent's detach.
                outgoing.put_nowait(to_tytx(dict(op="closed", pageId=target)))
                return None

        incoming = asyncio.create_task(receive())
        pending = asyncio.create_task(outgoing.get())
        try:
            self.gramlot_server.connect_page_channel(page_id, lambda wire: deliver(wire, page_id), owner=owner)
            await send({"type": "websocket.accept"})
            while True:
                completed, _ = await asyncio.wait(
                    (incoming, pending, *calls.values()), timeout=self.gramlot_server.page_ttl,
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
                self.gramlot_server.page_store(page_id, owner=owner)
                message = from_tytx(event["text"])
                if not isinstance(message, dict) or not isinstance(message.get("pageId"), str):
                    raise ValueError("Invalid page identity")
                target = message["pageId"]
                operation = message.get("op")
                if operation == "attach":
                    if target in self._store_channels:
                        raise ValueError("Page already has a store channel")
                    target_store = self.gramlot_server.page_store(target, owner=owner)
                    self.gramlot_server.connect_page_channel(target, lambda wire, target=target: deliver(wire, target), owner=owner)
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
                    wire, dispatch = self.gramlot_server.prepare_publish(event["text"], owner=owner)
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
                        calls[key] = asyncio.create_task(self.gramlot_server.call(event["text"], owner=owner))
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

    async def _lifespan(self, receive, send) -> None:
        while True:
            event = await receive()
            if event["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif event["type"] == "lifespan.shutdown":
                self.shutdown()
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
    async def _send(send, reply: base.Reply) -> None:
        headers = {
            "content-type": reply.content_type,
            "content-length": str(len(reply.body)),
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
