"""Run with Playwright installed and GRAMLOT_CHROMIUM pointing at a Chromium executable."""

import asyncio
import os
import secrets
import socket
from contextlib import asynccontextmanager

import pytest
import uvicorn
from genro_tytx import from_tytx
from test_kajennspa import pytestmark as spa_required, running

chromium = os.environ.get("GRAMLOT_CHROMIUM")
pytestmark = [
    spa_required,
    pytest.mark.skipif(not chromium, reason="requires GRAMLOT_CHROMIUM"),
]


@asynccontextmanager
async def listener(app):
    """Allow the test to hold one tab's next handshake while the other stays online."""
    blocked = {}

    async def site(scope, receive, send):
        if scope["type"] == "websocket":
            gate = blocked.get(scope["query_string"])
            if gate:
                await gate.wait()
        await app(scope, receive, send)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen()
        runner = uvicorn.Server(
            uvicorn.Config(
                site, lifespan="off", ws="websockets-sansio", log_level="error"
            )
        )
        task = asyncio.create_task(runner.serve(sockets=[sock]))
        try:
            async with asyncio.timeout(15):
                while not runner.started:
                    if task.done():
                        await task
                    await asyncio.sleep(0.01)
            yield (
                runner,
                blocked,
                f"http://127.0.0.1:{sock.getsockname()[1]}/demo/pages/",
            )
        finally:
            for gate in blocked.values():
                gate.set()
            runner.should_exit = True
            await task


async def write(page, value):
    await page.locator("#editor").fill(value)
    await page.locator("#editor").press("Tab")


async def details(page):
    result = await page.evaluate("""async () => {
        const r = await fetch("gramlot/rpc", {method:"POST", headers:{"Content-Type":"application/json"},
            body:JSON.stringify({id:"browser", name:"details", contentType:"data", params:{}, pageId:gramlot.pageId})});
        if (!r.ok) throw Error("HTTP " + r.status);
        return await r.text();
    }""")
    return from_tytx(result)["value"]


@pytest.mark.parametrize(
    "options", [{}, {"spawner": "subprocess"}], ids=["local", "subprocess"]
)
async def test_two_tabs_recover_after_login_and_network_loss(tmp_path, options):
    from playwright.async_api import async_playwright, expect

    async with (
        running(tmp_path, **options) as app,
        listener(app) as (runner, blocked, url),
        async_playwright() as pw,
    ):
        store = app.applications["_auth"].store
        password = secrets.token_urlsafe(18)
        store.save_user(
            {
                "identity": "mario",
                "password_hash": store.hash_password(password),
                "tags": [],
                "groups": [],
                "status": "confirmed",
            }
        )
        browser = await pw.chromium.launch(executable_path=chromium)
        async with browser:
            context = await browser.new_context()
            a, b = await context.new_page(), await context.new_page()
            ids = []
            for page in (a, b):
                await page.goto(url)
                await expect(page.locator("#live-spa")).to_be_visible()
                await page.wait_for_function("window.gramlot?._pageStore?.ready")
                ids.append(
                    await page.evaluate("""() => {
                    window.originalSocket = gramlot._pageStore.socket;
                    originalSocket.addEventListener("close", e => {window.guestClose = e.code});
                    return gramlot.pageId;
                }""")
                )
            assert ids[0] != ids[1]
            await write(a, "guest A")
            await expect(b.locator("#mirror")).to_have_text("guest A")
            await write(b, "guest B")
            await expect(a.locator("#mirror")).to_have_text("guest B")

            login = await a.evaluate(
                """async password => (await fetch("/_auth/login", {method:"POST",
                headers:{"Content-Type":"application/json"}, body:JSON.stringify({identity:"mario",password})})).json()""",
                password,
            )
            assert login["identity"] == "mario"
            # Access the original pages under the new principal, causing their stores to rebind.
            for page in (a, b):
                assert (await details(page))["user"] == "mario"
            for page in (a, b):
                await page.wait_for_function("""window.guestClose === 1008 && gramlot._pageStore.ready &&
                    gramlot._pageStore.socket !== originalSocket && [...gramlot._pageStore.binders.values()].every(b => b.ready)""")
                await expect(page.locator("#mirror")).to_have_text("")
            await write(a, "signed A")
            await expect(b.locator("#mirror")).to_have_text("signed A")
            await write(b, "signed B")
            await expect(a.locator("#mirror")).to_have_text("signed B")

            query = ("pageId=" + ids[0]).encode()
            gate = blocked[query] = asyncio.Event()
            (socket_a,) = [
                connection
                for connection in runner.server_state.connections
                if getattr(connection, "scope", {}).get("type") == "websocket"
                and connection.scope["query_string"] == query
            ]
            socket_a.transport.abort()
            await a.wait_for_function("gramlot._pageStore.reconnecting")
            await write(a, "offline edit")
            await write(b, "authoritative")
            await expect(a.locator("#editor")).to_have_value("offline edit")
            async with asyncio.timeout(5):
                while (await details(b))["text"] != "authoritative":
                    await asyncio.sleep(0.02)
            gate.set()
            await expect(a.locator("#mirror")).to_have_text(
                "authoritative", timeout=10000
            )
            await expect(a.locator("#editor")).to_have_value("authoritative")
            await write(a, "after recovery")
            await expect(b.locator("#mirror")).to_have_text("after recovery")
            await write(b, "reverse after recovery")
            await expect(a.locator("#mirror")).to_have_text("reverse after recovery")
            assert [await page.evaluate("gramlot.pageId") for page in (a, b)] == ids
