# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Shared Gramlot channel rules; each adapter owns its native socket."""

import asyncio
import logging
import threading
from contextlib import nullcontext
from urllib.parse import parse_qs, urlsplit

from genro_tytx import from_tytx, to_tytx
from gramlot.server import PageExpired


class _StoreChannel:
    def __init__(self, server, invoke, request_context=nullcontext):
        self.gramlot_server = server
        self.request_context = request_context
        self.invoke = invoke
        self._store_channels = {}

    async def serve(self, socket, scope, *, owner, path, disconnect_error, identity=None):
        """One primary socket multiplexes owned page stores and asynchronous RPC."""
        async with self.request_context():
            headers = {key.lower(): value for key, value in scope.get("headers", [])}
            try:
                if self.gramlot_server.websocket_url is None or scope["path"] != path:
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
                await socket.refuse(1008)
                return
        outgoing = asyncio.Queue(maxsize=256)
        loop = asyncio.get_running_loop()
        loop_thread = threading.get_ident()
        pages = {page_id: (store, set())}
        calls = {}
        self._store_channels[page_id] = pages

        async def detach(target):
            for (call_page, _), task in calls.items():
                if call_page == target:
                    task.cancel()
            target_store, binders = pages.pop(target)
            def close():
                for binder in binders:
                    target_store.unsubscribe(binder)
                self.gramlot_server.close_page(target, owner=owner)
            await self.invoke(close)
            self._store_channels.pop(target, None)

        async def enqueue(wire):
            outgoing.put_nowait(wire)

        def deliver(wire, target):
            # Freeze Data in its execution thread before scheduling delivery.
            wire = to_tytx(dict(from_tytx(wire), pageId=target))
            if threading.get_ident() == loop_thread:
                outgoing.put_nowait(wire)
            else:
                asyncio.run_coroutine_threadsafe(enqueue(wire), loop).result()

        def live_store(target):
            try:
                return self.gramlot_server.page_store(target, owner=owner)
            except PageExpired:
                if target == page_id:
                    raise
                # An HTTP close beacon may arrive before the parent's detach.
                outgoing.put_nowait(to_tytx(dict(op="closed", pageId=target)))
                return None

        send_lock = asyncio.Lock()

        async def send_text(wire):
            async with send_lock:
                await socket.send_text(wire)

        async def write_updates():
            # Drain frozen deltas while the reader awaits application processing.
            while True:
                wire = await outgoing.get()
                if from_tytx(wire)["pageId"] in pages:
                    await send_text(wire)

        incoming = writer = None
        try:
            async with self.request_context():
                self.gramlot_server.connect_page_channel(page_id, lambda wire: deliver(wire, page_id), owner=owner)
                await socket.accept()
            incoming = asyncio.create_task(socket.receive_text())
            writer = asyncio.create_task(write_updates())
            while True:
                completed, _ = await asyncio.wait(
                    (incoming, writer, *calls.values()), timeout=self.gramlot_server.page_ttl,
                    return_when=asyncio.FIRST_COMPLETED)
                if not completed:
                    async with self.request_context():
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
                if writer in completed:
                    writer.result()
                if incoming not in completed:
                    continue
                text = incoming.result()
                async with self.request_context():
                    self.gramlot_server.page_store(page_id, owner=owner)
                    message = from_tytx(text)
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
                        incoming = asyncio.create_task(socket.receive_text())
                        continue
                    if target not in pages:
                        raise ValueError("Page is not attached to this channel")
                    if operation == "detach":
                        if target == page_id:
                            raise ValueError("Cannot detach the primary page")
                        await detach(target)
                        incoming = asyncio.create_task(socket.receive_text())
                        continue
                    store = live_store(target)
                    if store is None:
                        incoming = asyncio.create_task(socket.receive_text())
                        continue
                    if operation == "publish":
                        call_id = message.get("id")
                        if not isinstance(call_id, str) or not call_id or (target, call_id) in calls:
                            raise ValueError("Invalid or duplicate publication ID")
                        wire, dispatch = self.gramlot_server.prepare_publish(text, owner=owner)
                        # Send acceptance before entering application code, not merely enqueue it.
                        await send_text(to_tytx(dict(from_tytx(wire), pageId=target)))
                        if dispatch is not None:
                            try:
                                await self.invoke(dispatch)
                            except asyncio.QueueFull:
                                raise
                            except Exception:
                                logging.getLogger(__name__).exception("PageStore publication subscriber failed")
                        incoming = asyncio.create_task(socket.receive_text())
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
                            calls[key] = asyncio.create_task(self._call(text, owner=owner, identity=identity))
                        incoming = asyncio.create_task(socket.receive_text())
                        continue
                    binders = pages[target][1]
                    binder_id = message.get("binderId")
                    if not isinstance(binder_id, str) or not binder_id:
                        raise ValueError("Missing binder ID")
                    if operation == "subscribe":
                        await self.invoke(store.subscribe, binder_id, message["path"], lambda wire, target=target: deliver(wire, target))
                        binders.add(binder_id)
                    elif binder_id not in binders:
                        raise ValueError("Unknown subscription")
                    elif operation == "unsubscribe":
                        await self.invoke(store.unsubscribe, binder_id)
                        binders.remove(binder_id)
                    elif operation == "change":
                        await self.invoke(store.change, binder_id, message)
                    else:
                        raise ValueError("Unknown store operation")
                    incoming = asyncio.create_task(socket.receive_text())
        except disconnect_error:
            return
        except (ValueError, KeyError, TypeError, PageExpired):
            await socket.close(1008)
        except Exception:
            await socket.close(1011)
            raise
        finally:
            tasks = [task for task in (incoming, writer, *calls.values()) if task is not None]
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            calls.clear()
            # Preserve the PoC lifetime: socket loss closes every attached page.
            async with self.request_context():
                for target in list(pages):
                    await detach(target)

    async def _call(self, text, *, owner, identity):
        async with self.request_context():
            return await self.gramlot_server.call(text, owner=owner, identity=identity)
