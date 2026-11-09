# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""The terminal socket: one WebSocket per terminal session, binary frames only (#87).

``/gramlot/terminal?pageId=…&session=…`` opens the ``@terminal`` method ``session`` of the page's store.
The frames are those of ``gramlot.server.terminal``. The socket closes when the session closes, and the
session closes when the socket closes. The page's store channel is a separate socket: terminal output
never enters its queue.
"""

import asyncio
import time
from contextlib import nullcontext
from urllib.parse import parse_qs

from gramlot.server import PageExpired
from gramlot.server.terminal import TerminalClosed

from gramlot_py_server.store_channel import same_origin

# A frame renews the page at most once per interval: a keyboard-only session outlives page_ttl.
RENEWAL = 60


class _TerminalChannel:
    def __init__(self, server, request_context=nullcontext):
        self.gramlot_server = server
        self.request_context = request_context

    async def serve(self, socket, scope, *, owner, path, disconnect_error, identity=None):
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        accepted = asyncio.Event()

        async def send(frame):
            await accepted.wait()
            await socket.send_bytes(frame)

        async with self.request_context():
            try:
                if self.gramlot_server.websocket_url is None or scope["path"] != path:
                    raise ValueError("Unknown WebSocket route")
                if not same_origin(scope, headers):
                    raise ValueError("Origin does not match")
                query = parse_qs(scope.get("query_string", b"").decode("ascii"), strict_parsing=True)
                if set(query) != {"pageId", "session"} or any(len(values) != 1 for values in query.values()):
                    raise ValueError("Expected a page ID and a session")
                page_id, name = query["pageId"][0], query["session"][0]
                terminal = await self.gramlot_server.open_terminal(
                    page_id, name, send=send, owner=owner, identity=identity,
                    host=headers.get(b"host", b"").decode("ascii"))
            except (ValueError, LookupError, PermissionError, TypeError, UnicodeError):
                await socket.refuse(1008)
                return
        incoming = closed = None
        renewed = time.monotonic()
        try:
            await socket.accept()
            accepted.set()
            closed = asyncio.ensure_future(terminal.wait_closed())
            while True:
                incoming = asyncio.ensure_future(socket.receive_bytes())
                await asyncio.wait((incoming, closed), return_when=asyncio.FIRST_COMPLETED)
                # The session ended (method returned, page closed): frames still arriving are dropped.
                if terminal.closed:
                    if incoming.done() and not incoming.cancelled():
                        incoming.exception()
                    await socket.close(1000)
                    return
                try:
                    terminal.receive(incoming.result())
                except TerminalClosed:
                    await socket.close(1000)
                    return
                except (ValueError, TypeError):
                    await socket.close(1008)
                    return
                if time.monotonic() - renewed >= RENEWAL:
                    renewed = time.monotonic()
                    try:
                        async with self.request_context():
                            self.gramlot_server.page_store(page_id, owner=owner)
                    except PageExpired:
                        await socket.close(1000)
                        return
        except disconnect_error:
            return
        finally:
            for task in (incoming, closed):
                if task is not None:
                    task.cancel()
            self.gramlot_server.close_terminal(terminal)
