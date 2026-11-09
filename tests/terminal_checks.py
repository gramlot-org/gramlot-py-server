"""ASGI contracts of the terminal socket (#87): binary frames on a socket of their own."""
import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import pytest
from genro_tytx import from_tytx
from gramlot.server import GramlotServer

import gramlot_py_server.terminal_channel as terminal_channel

from page_store_checks import channel, open_page, rpc

PAGES = Path(__file__).parent / "fixtures" / "terminal"
INPUT, OUTPUT, RESIZE, ACK = 0, 1, 4, 5


def ack(count):
    return bytes([ACK]) + count.to_bytes(4, "big")


@asynccontextmanager
async def terminal(app, cookie, page_id, session, *, origin="http://test", prefix="", query=None, peer=("127.0.0.1", 50000)):
    incoming, outgoing = asyncio.Queue(), asyncio.Queue()
    await incoming.put({"type": "websocket.connect"})
    scope = dict(type="websocket", scheme="ws", path=prefix + "/gramlot/terminal",
                 query_string=(query if query is not None else f"pageId={page_id}&session={session}").encode(),
                 headers=[(b"host", b"test"), (b"origin", origin.encode()), (b"cookie", cookie.encode())], client=peer)
    task = asyncio.create_task(app(scope, incoming.get, outgoing.put))

    async def receive(timeout=2):
        return await asyncio.wait_for(outgoing.get(), timeout)

    async def send(frame):
        await incoming.put(dict(type="websocket.receive", **({"text": frame} if isinstance(frame, str) else {"bytes": frame})))

    try:
        yield await receive(), send, receive
    finally:
        if not task.done():
            await incoming.put({"type": "websocket.disconnect", "code": 1000})
        await asyncio.wait_for(task, 2)


class TerminalChecks:
    async def page(self, client):
        return await open_page(client)

    def app(self):
        return self.create_application(PAGES, websocket=True)

    @pytest.mark.asyncio
    async def test_input_returns_as_output_frames_and_resize_reaches_the_method(self):
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            async with terminal(app, cookie, page_id, "echo") as (accepted, send, receive):
                assert accepted["type"] == "websocket.accept"
                await send(bytes([INPUT]) + b"ls\r")
                assert await receive() == {"type": "websocket.send", "bytes": bytes([OUTPUT]) + b"ls\r"}
            async with terminal(app, cookie, page_id, "sizes") as (accepted, send, receive):
                await send(bytes([RESIZE]) + json.dumps({"Width": 80, "Height": 24}).encode())
                assert (await receive())["bytes"] == bytes([OUTPUT]) + b"24x80"

    @pytest.mark.asyncio
    async def test_a_returning_method_closes_the_socket(self):
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            async with terminal(app, cookie, page_id, "bye") as (accepted, send, receive):
                assert (await receive())["bytes"] == bytes([OUTPUT]) + b"bye"
                assert (await receive())["type"] == "websocket.close"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("case", ["origin", "owner", "unknown", "query", "guarded"])
    async def test_refused_sessions_close_with_1008(self, case):
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            options = dict(origin="http://evil") if case == "origin" else dict(query=f"pageId={page_id}") if case == "query" else {}
            owner = "gramlot_owner=intruder" if case == "owner" else cookie
            session = {"unknown": "missing", "guarded": "guarded"}.get(case, "echo")
            async with terminal(app, owner, page_id, session, **options) as (first, send, receive):
                assert first["type"] == "websocket.close" and first["code"] == 1008

    @pytest.mark.asyncio
    async def test_output_waits_for_acknowledgement_and_the_store_channel_keeps_answering(self):
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            async with channel(app, cookie, page_id) as (store_accepted, store_send, store_receive):
                assert store_accepted["type"] == "websocket.accept"
                async with terminal(app, cookie, page_id, "flood") as (accepted, send, receive):
                    received = 0
                    while received < 1 << 20:
                        received += len((await receive())["bytes"]) - 1
                    assert received == 1 << 20
                    with pytest.raises(asyncio.TimeoutError):
                        await receive(timeout=0.2)
                    await store_send(rpc("r1", value="still here"))
                    reply = from_tytx((await store_receive())["text"])
                    assert reply["id"] == "r1" and reply["value"] == "still here", reply
                    total = received
                    await send(ack(received))
                    while True:
                        event = await receive()
                        if event["type"] == "websocket.close":
                            break
                        total += len(event["bytes"]) - 1
                        await send(ack(len(event["bytes"]) - 1))
                    assert total == 48 * 65536

    @pytest.mark.asyncio
    async def test_closing_the_page_closes_its_terminal_socket(self):
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            async with terminal(app, cookie, page_id, "echo") as (accepted, send, receive):
                response = await client.post("/gramlot/close", json={"pageId": page_id})
                assert response.status_code in (200, 204)
                event = await receive()
                assert event["type"] == "websocket.close" and event["code"] == 1000, event

    @pytest.mark.asyncio
    async def test_a_frame_on_an_unknown_channel_closes_the_socket_with_1008(self):
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            async with terminal(app, cookie, page_id, "echo") as (accepted, send, receive):
                await send(bytes([9]))
                event = await receive()
                assert event["type"] == "websocket.close" and event["code"] == 1008

    @pytest.mark.asyncio
    async def test_opening_the_name_again_closes_the_open_session(self):
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            async with terminal(app, cookie, page_id, "echo") as (first, first_send, first_receive):
                async with terminal(app, cookie, page_id, "echo") as (second, send, receive):
                    assert second["type"] == "websocket.accept"
                    event = await first_receive()
                    assert event["type"] == "websocket.close" and event["code"] == 1000
                    await send(bytes([INPUT]) + b"again")
                    assert (await receive())["bytes"] == bytes([OUTPUT]) + b"again"

    @pytest.mark.asyncio
    async def test_a_text_frame_closes_the_socket_with_1008(self):
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            async with terminal(app, cookie, page_id, "echo") as (accepted, send, receive):
                await send("ls")
                event = await receive()
                assert event["type"] == "websocket.close" and event["code"] == 1008

    @pytest.mark.asyncio
    async def test_the_session_knows_the_host_header_and_the_peer_address(self):
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            async with terminal(app, cookie, page_id, "peer", peer=("::1", 4000)) as (accepted, send, receive):
                assert (await receive())["bytes"] == bytes([OUTPUT]) + b"test ::1"

    @pytest.mark.asyncio
    async def test_a_frame_after_the_renewal_interval_renews_the_page(self, monkeypatch):
        renewals = []
        page_store = GramlotServer.page_store

        def counting(server, page_id, **options):
            renewals.append(page_id)
            return page_store(server, page_id, **options)
        monkeypatch.setattr(GramlotServer, "page_store", counting)
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            async with terminal(app, cookie, page_id, "echo") as (accepted, send, receive):
                opened = len(renewals)
                await send(bytes([INPUT]) + b"a")
                await receive()
                assert len(renewals) == opened
                monkeypatch.setattr(terminal_channel, "RENEWAL", 0)
                await send(bytes([INPUT]) + b"b")
                await receive()
                assert renewals[opened:] == [page_id]

    @pytest.mark.asyncio
    async def test_a_browser_leaving_while_output_waits_cancels_the_method(self, monkeypatch):
        tasks = []
        open_terminal = GramlotServer.open_terminal

        async def recording(server, page_id, session, **options):
            opened = await open_terminal(server, page_id, session, **options)
            tasks.append((opened, server._terminals[(page_id, session)][1]))
            return opened
        monkeypatch.setattr(GramlotServer, "open_terminal", recording)
        app = self.app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await self.page(client)
            async with terminal(app, cookie, page_id, "held") as (accepted, send, receive):
                received = 0
                while received < 1 << 20:
                    received += len((await receive())["bytes"]) - 1
                session, task = tasks[0]
                assert session.unacknowledged == 1 << 20 and not task.done()
            with pytest.raises(asyncio.CancelledError):
                await asyncio.wait_for(task, 2)
            assert session.closed
