import asyncio

import httpx
import pytest

from gramlot_py_server.uvicorn import _Disconnected, create_application
from page_store_checks import open_page
from terminal_checks import PAGES, TerminalChecks


class TestTerminal(TerminalChecks):
    create_application = staticmethod(create_application)


class _Socket:
    """A socket whose first frame arrives as the page closes, before the session's close is observed."""

    def __init__(self, on_receive):
        self.on_receive, self.events, self.count = on_receive, [], 0

    async def accept(self):
        self.events.append("accept")

    async def refuse(self, code):
        self.events.append(("refuse", code))

    async def close(self, code):
        self.events.append(("close", code))

    async def send_bytes(self, data):
        self.events.append(("send", data))

    async def receive_bytes(self):
        self.count += 1
        if self.count == 1:
            self.on_receive()
            return bytes([0]) + b"x"
        await asyncio.sleep(3600)


@pytest.mark.asyncio
async def test_a_frame_arriving_as_the_session_closes_ends_with_1000():
    app = create_application(PAGES, websocket=True)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        page_id, cookie = await open_page(client)
        owner = app.owner_of(cookie)
        loop = asyncio.get_running_loop()
        socket = _Socket(lambda: loop.call_soon(loop.call_soon,
                                                lambda: app.gramlot_server.close_page(page_id, owner=owner)))
        scope = dict(type="websocket", scheme="ws", path="/gramlot/terminal",
                     query_string=f"pageId={page_id}&session=echo".encode(),
                     headers=[(b"host", b"test"), (b"origin", b"http://test")])
        await asyncio.wait_for(app._terminal_channel.serve(
            socket, scope, owner=owner, path="/gramlot/terminal", disconnect_error=_Disconnected), 2)
        assert socket.events[0] == "accept" and socket.events[-1] == ("close", 1000)
