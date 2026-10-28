"""ASGI protocol contracts for the experimental shared page-store channel."""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
import json
import re
import httpx
import pytest
from genro_tytx import from_tytx, to_tytx
from genro_bag import Bag

PAGES = Path(__file__).parent / "fixtures" / "page_store"


def rpc(call_id, name="echo", **params):
    return dict(id=call_id, contentType="data", name=name, params=params)

@asynccontextmanager
async def channel(app, cookie, page_id, *, origin="http://test", prefix="", send_hook=None, headers=()):
    incoming, outgoing = asyncio.Queue(), asyncio.Queue()
    await incoming.put({"type": "websocket.connect"})
    scope = dict(type="websocket", scheme="ws", path=prefix + "/gramlot/store",
                 query_string=f"pageId={page_id}".encode(),
                 headers=[(b"host", b"test"), (b"origin", origin.encode()), (b"cookie", cookie.encode()), *headers])
    async def emit(event):
        await outgoing.put(event)
        if send_hook is not None:
            await send_hook(event)
    task = asyncio.create_task(app(scope, incoming.get, emit))
    async def receive():
        return await asyncio.wait_for(outgoing.get(), 2)
    async def send(message):
        await incoming.put(dict(type="websocket.receive", text=to_tytx({"pageId": page_id, **message})))
    try:
        yield await receive(), send, receive
    finally:
        if not task.done():
            await incoming.put({"type": "websocket.disconnect", "code": 1000})
        await asyncio.wait_for(task, 2)

async def open_page(client, prefix=""):
    response = await client.get(prefix + "/")
    assert response.status_code == 200
    config = json.loads(re.search(r"new PageBootstrap\((.+)\)\.run", response.text).group(1))["config"]
    cookie = "; ".join(f"{key}={value}" for key, value in client.cookies.items())
    return config["pageId"], cookie


class PageStoreChecks:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("separate_socket", [False, True])
    async def test_store_publishes_back_to_child_after_acceptance(self, separate_socket):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            child, _ = await open_page(client)
            target, _ = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(dict(op="attach", pageId=child))

                async def roundtrip():
                    await send(dict(op="publish", id="request", pageId=child, targetPageId=target,
                                    topic="reply", payload={"value": "from child"}))
                    assert from_tytx((await receive())["text"]) == dict(
                        id="request", pageId=child, contentType="data", value="ok")
                    event = from_tytx((await receive())["text"])
                    assert (event["op"], event["pageId"], event["topic"]) == ("publish", child, "received")
                    assert event["payload"]["record"].get_item("value") == "from child"
                    assert event["metadata"] == {"pageId": target}
                    assert "id" not in event
                    await send(rpc("still-alive", value=1))
                    assert from_tytx((await receive())["text"])["id"] == "still-alive"

                if separate_socket:
                    async with channel(app, cookie, target):
                        await roundtrip()
                else:
                    await send(dict(op="attach", pageId=target))
                    await roundtrip()
        assert not app.gramlot_server._page_channels
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_publish_defaults_to_sender_and_reaches_same_owner_store_on_another_socket(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            target, _ = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                async with channel(app, cookie, target) as (_, target_send, target_receive):
                    await send(dict(op="subscribe", binderId="a", path="order"))
                    await receive()
                    await target_send(dict(op="subscribe", binderId="b", path="order"))
                    await target_receive()
                    await send(dict(op="publish", id="own", topic="set_quantity", payload={"quantity": "4"}))
                    assert from_tytx((await receive())["text"])["value"] == "ok"
                    own = [from_tytx((await receive())["text"]) for _ in range(3)]
                    assert [(m["path"], str(m["value"])) for m in own] == [
                        ("quantity", "4"), ("total", "50.00"), ("status", "Calculated on the server")]
                    assert all(m["pageId"] == primary and m["op"] == "change" for m in own)
                    await send(dict(op="publish", id="other", targetPageId=target, topic="set_quantity", payload={"quantity": "8"}))
                    other = [from_tytx((await target_receive())["text"]) for _ in range(3)]
                    assert all(m["pageId"] == target and m["binderId"] == "b" for m in other)
                    assert other[0]["value"] == "8" and str(other[1]["value"]) == "100.00"
                    acknowledgement = from_tytx((await receive())["text"])
                    assert acknowledgement == dict(id="other", pageId=primary, contentType="data", value="ok")
                    # Unknown topics have no subscribers or retained delivery, but are accepted.
                    await send(dict(op="publish", id="unknown", topic="unknown", payload={}))
                    assert from_tytx((await receive())["text"])["value"] == "ok"
                    await send(rpc("barrier", value="still alive"))
                    assert from_tytx((await receive())["text"])["id"] == "barrier"
                    owner = client.cookies["gramlot_owner"]
                    assert app.gramlot_server.page_store(primary, owner=owner).data.get_item("order.quantity") == "4"
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_child_publish_retains_sender_identity_and_uses_its_own_store_by_default(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            child, _ = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(dict(op="attach", pageId=child))
                await send(dict(op="subscribe", pageId=child, binderId="c", path="order"))
                await receive()
                await send(dict(op="publish", id="child", pageId=child, topic="set_quantity", payload={"quantity": "7"}))
                assert from_tytx((await receive())["text"]) == dict(id="child", pageId=child, contentType="data", value="ok")
                messages = [from_tytx((await receive())["text"]) for _ in range(3)]
                assert all(message["pageId"] == child for message in messages)
                owner = client.cookies["gramlot_owner"]
                assert app.gramlot_server.page_store(primary, owner=owner).data.get_item("order.quantity") == "2"
                assert app.gramlot_server.page_store(child, owner=owner).data.get_item("order.quantity") == "7"
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("sender_is_child", [False, True])
    @pytest.mark.parametrize("invalid", ["foreign", "missing", "closed", "malformed", "subscriber"])
    async def test_publication_rejection_preserves_stores_binders_and_rpc(self, invalid, sender_is_child, caplog):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            child, _ = await open_page(client)
            owner = client.cookies["gramlot_owner"]
            if invalid == "foreign":
                client.cookies.clear()
            target, _ = await open_page(client)
            destination = app.gramlot_server.page_store(target, owner=client.cookies["gramlot_owner"])
            if invalid == "closed":
                app.gramlot_server.close_page(target, owner=owner)
            sender = child if sender_is_child else primary
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(dict(op="attach", pageId=child))
                for page in (primary, child):
                    await send(dict(op="subscribe", pageId=page, binderId="a", path="order"))
                    assert from_tytx((await receive())["text"])["op"] == "snapshot"
                await send(dict(rpc("pending", "delayed_echo", value="alive", delay=0.01), pageId=sender))
                message = dict(op="publish", id="rejected", pageId=sender, topic="set_quantity", targetPageId=target,
                               payload={"quantity": "99"})
                if invalid == "missing":
                    message["targetPageId"] = "missing"
                elif invalid == "malformed":
                    message["payload"] = []
                elif invalid == "subscriber":
                    message["payload"] = {}
                await send(message)
                responses = {m["id"]: m for m in [from_tytx((await receive())["text"]) for _ in range(2)]}
                refused = responses["rejected"]
                assert refused["pageId"] == sender
                if invalid == "subscriber":
                    assert refused["value"] == "ok" and "error" not in refused
                    assert "PageStore publication subscriber failed" in caplog.text
                else:
                    assert "value" not in refused
                    assert refused["error"]["code"] == ("invalid_request" if invalid == "malformed" else "page_expired")
                response = responses["pending"]
                assert (response["id"], response["pageId"], response["value"]) == ("pending", sender, "alive")
                assert destination.data.get_item("order.quantity") == "2"
                for page in (primary, child):
                    assert app.gramlot_server.page_store(page, owner=owner).data.get_item("order.quantity") == "2"
                    await send(dict(op="change", pageId=page, binderId="a", path="quantity",
                                    evt="upd_value", value="3", attr={}))
                    changes = [from_tytx((await receive())["text"]) for _ in range(2)]
                    assert [(m["pageId"], m["path"]) for m in changes] == [(page, "total"), (page, "status")]
                    await send(dict(op="publish", id="valid", pageId=page, topic="set_quantity", payload={"quantity": "4"}))
                    assert from_tytx((await receive())["text"]) == dict(id="valid", pageId=page, contentType="data", value="ok")
                    changes = [from_tytx((await receive())["text"]) for _ in range(2)]
                    assert [m["path"] for m in changes] == ["quantity", "total"]
                    assert all(m["pageId"] == page for m in changes)
                    await send(dict(rpc("after", value="still alive"), pageId=page))
                    assert from_tytx((await receive())["text"])["value"] == "still alive"
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_publication_sends_acceptance_before_entering_subscribers(self):
        app = self.create_application(PAGES, websocket=True)
        release = asyncio.Event()
        entered = asyncio.Event()
        async def hold_acceptance(event):
            if event["type"] == "websocket.send" and from_tytx(event["text"]).get("id") == "accepted":
                entered.set()
                await release.wait()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            store = app.gramlot_server.page_store(primary, owner=client.cookies["gramlot_owner"])
            async with channel(app, cookie, primary, send_hook=hold_acceptance) as (_, send, receive):
                await send(dict(op="subscribe", binderId="a", path="order"))
                await receive()
                await send(dict(op="publish", id="accepted", topic="set_quantity", payload={"quantity": "4"}))
                try:
                    ack = from_tytx((await receive())["text"])
                    assert ack["id"] == "accepted" and ack["value"] == "ok"
                    await asyncio.wait_for(entered.wait(), 2)
                    assert store.data.get_item("order.quantity") == "2"
                finally:
                    release.set()
                changes = [from_tytx((await receive())["text"]) for _ in range(3)]
                assert [m["path"] for m in changes] == ["quantity", "total", "status"]
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_publication_cannot_forge_an_unattached_sender(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            target, _ = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(dict(op="publish", id="forged", pageId=target, topic="set_quantity", payload={"quantity": "99"}))
                assert (await receive())["code"] == 1008
            assert app.gramlot_server.page_store(target, owner=client.cookies["gramlot_owner"]).data.get_item("order.quantity") == "2"
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_rpc_source_errors_and_reverse_completion_share_the_binder_channel(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(dict(rpc("main", "main"), contentType="source"))
                main = from_tytx((await receive())["text"])
                assert main["id"] == "main" and main["pageId"] == primary
                assert main["contentType"] == "source" and isinstance(main["value"], Bag)
                await send(rpc("slow", "delayed_echo", value="late", delay=0.05))
                await send(rpc("fast", value="early"))
                first = from_tytx((await receive())["text"])
                assert (first["id"], first["value"]) == ("fast", "early")
                await send(dict(op="subscribe", binderId="a", path="order"))
                assert from_tytx((await receive())["text"])["op"] == "snapshot"
                assert from_tytx((await receive())["text"])["id"] == "slow"
                for call_id, name, code in [
                    ("failed", "failing", "application_error"),
                    ("missing", "not_declared", "not_found"),
                    ("denied", "restricted", "not_authenticated"),
                ]:
                    await send(rpc(call_id, name))
                    message = from_tytx((await receive())["text"])
                    assert message["id"] == call_id and message["error"]["code"] == code
                await send(rpc("after-errors", value=42))
                assert from_tytx((await receive())["text"])["value"] == 42
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_rpc_identity_and_cancellation_are_scoped_to_the_attached_page(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            child, _ = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(dict(op="attach", pageId=child))
                await send(rpc("same", "delayed_echo", value="primary", delay=0.05))
                await send(dict(rpc("same", "delayed_echo", value="child", delay=0.1), pageId=child))
                await send(dict(op="cancel", pageId=child, id="same"))
                message = from_tytx((await receive())["text"])
                assert (message["pageId"], message["value"]) == (primary, "primary")
                await send(dict(rpc("barrier", "delayed_echo", value="done", delay=0.1), pageId=child))
                message = from_tytx((await receive())["text"])
                assert (message["pageId"], message["id"]) == (child, "barrier")
                await send(dict(rpc("detached", "delayed_echo", value="late", delay=0.1), pageId=child))
                await send(dict(op="detach", pageId=child))
                await send(rpc("after-detach", "delayed_echo", value="alive", delay=0.15))
                assert from_tytx((await receive())["text"])["id"] == "after-detach"
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("bad", [
        {"id": "bad", "contentType": "unknown", "name": "echo", "params": {}},
        {"id": "bad", "contentType": "data", "name": "echo", "params": []},
        {"id": "bad", "op": None},
    ])
    async def test_malformed_rpc_closes_the_channel(self, bad):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(bad)
                assert (await receive())["code"] == 1008
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_rpc_cannot_target_an_unattached_or_foreign_page(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            for foreign in [False, True]:
                primary, cookie = await open_page(client)
                if foreign:
                    client.cookies.clear()
                other, _ = await open_page(client)
                async with channel(app, cookie, primary) as (_, send, receive):
                    await send(dict(rpc("impersonation", value=1), pageId=other))
                    assert (await receive())["code"] == 1008
                assert other in app.gramlot_server._pages
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_disconnect_cancels_inflight_dispatch_and_releases_pages(self, monkeypatch):
        app = self.create_application(PAGES, websocket=True)
        started, cancelled = asyncio.Event(), asyncio.Event()
        async def waiting():
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()
        async def waiting_call(text, *, owner, identity=None):
            return await app.gramlot_server._invoke(waiting)
        monkeypatch.setattr(app.gramlot_server, "call", waiting_call)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(rpc("pending", value=1))
                await asyncio.wait_for(started.wait(), 2)
            assert cancelled.is_set()
            assert not app._store_channel._store_channels
            assert primary not in app.gramlot_server._pages
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("duplicate", [True, False])
    async def test_rpc_duplicate_ids_and_capacity_close_without_leaking_tasks(self, monkeypatch, duplicate):
        app = self.create_application(PAGES, websocket=True)
        running = set()
        async def waiting(call_id):
            running.add(call_id)
            try:
                await asyncio.Event().wait()
            finally:
                running.remove(call_id)
        async def waiting_call(text, *, owner, identity=None):
            return await app.gramlot_server._invoke(waiting, from_tytx(text)["id"])
        monkeypatch.setattr(app.gramlot_server, "call", waiting_call)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                for index in range(2 if duplicate else 257):
                    await send(rpc("same" if duplicate else str(index), value=1))
                assert (await receive())["code"] == 1008
            assert not running
            assert not app._store_channel._store_channels
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_snapshots_changes_controller_http_and_cleanup(self):
        app = self.create_application(PAGES, websocket=True, mount_path="/py")
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await open_page(client, "/py")
            async with channel(app, cookie, page_id, prefix="/py") as (opened, send, receive):
                assert opened["type"] == "websocket.accept"
                for binder in ("a", "b"):
                    await send(dict(op="subscribe", binderId=binder, path="order"))
                    message = from_tytx((await receive())["text"])
                    assert message["op"] == "snapshot"
                    assert message["value"].get_item("quantity") == "2"
                await send(dict(op="change", binderId="a", path="quantity",
                                evt="upd_value", value="3", attr={}))
                messages = [from_tytx((await receive())["text"]) for _ in range(5)]
                assert [(m["binderId"], m["path"]) for m in messages] == [
                    ("b", "quantity"), ("a", "total"), ("b", "total"), ("a", "status"), ("b", "status")]
                rpc = await client.post("/py/gramlot/rpc", content=to_tytx(dict(
                    id="rpc-one", pageId=page_id, contentType="data", name="echo", params={"value": "HTTP"})),
                    headers={"content-type": "application/json"})
                assert from_tytx(rpc.text)["value"] == "HTTP"
                await send(dict(op="unsubscribe", binderId="b"))
                await send(dict(op="change", binderId="a", path="status", evt="del", value=None, attr={}))
            assert page_id not in app.gramlot_server._pages
            assert page_id not in app.gramlot_server._page_stores
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_shared_socket_isolates_pages_and_detaches_only_the_child(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            child, _ = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(dict(op="attach", pageId=child))
                for target in (primary, child):
                    await send(dict(op="subscribe", pageId=target, binderId="same-id", path="order"))
                    message = from_tytx((await receive())["text"])
                    assert message["pageId"] == target
                    assert message["value"].get_item("quantity") == "2"
                await send(dict(op="change", pageId=child, binderId="same-id", path="quantity",
                                evt="upd_value", value="7", attr={}))
                messages = [from_tytx((await receive())["text"]) for _ in range(2)]
                assert [(m["pageId"], m["path"]) for m in messages] == [(child, "total"), (child, "status")]
                owner = client.cookies["gramlot_owner"]
                assert app.gramlot_server.page_store(primary, owner=owner).data.get_item("order.quantity") == "2"
                await send(dict(op="detach", pageId=child))
                await send(dict(op="change", binderId="same-id", path="quantity", evt="upd_value", value="3", attr={}))
                assert from_tytx((await receive())["text"])["pageId"] == primary
                await receive()
                assert child not in app.gramlot_server._pages
                assert child not in app._store_channel._store_channels
            assert not app._store_channel._store_channels
            assert not app.gramlot_server._page_stores
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("operation", ["attach", "subscribe"])
    async def test_shared_socket_rejects_foreign_owner_and_unattached_pages(self, operation):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            if operation == "attach":
                client.cookies.clear()
            other, _ = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(dict(op=operation, pageId=other, binderId="a", path="order"))
                assert (await receive())["code"] == 1008
            assert other in app.gramlot_server._pages
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_child_http_close_racing_detach_preserves_the_primary(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            child, _ = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(dict(op="attach", pageId=child))
                await send(dict(op="subscribe", pageId=child, binderId="child", path="order"))
                await receive()
                await client.post("/gramlot/close", json={"pageId": child})
                await send(dict(op="unsubscribe", pageId=child, binderId="child"))
                assert from_tytx((await receive())["text"]) == {"op": "closed", "pageId": child}
                await send(dict(op="detach", pageId=child))
                await send(dict(op="subscribe", binderId="primary", path="order"))
                assert from_tytx((await receive())["text"])["op"] == "snapshot"
                assert primary in app.gramlot_server._pages
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_page_cannot_join_two_sockets(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            other, _ = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                async with channel(app, cookie, primary) as (opened, _, _):
                    assert opened["code"] == 1008
                async with channel(app, cookie, other) as (_, other_send, other_receive):
                    await other_send(dict(op="attach", pageId=primary))
                    assert (await other_receive())["code"] == 1008
                await send(dict(op="subscribe", binderId="a", path="order"))
                assert from_tytx((await receive())["text"])["pageId"] == primary
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_primary_disconnect_closes_every_attached_store(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            primary, cookie = await open_page(client)
            child, _ = await open_page(client)
            async with channel(app, cookie, primary) as (_, send, receive):
                await send(dict(op="attach", pageId=child))
                for target in (primary, child):
                    await send(dict(op="subscribe", pageId=target, binderId="a", path="order"))
                    await receive()
                assert set(app._store_channel._store_channels) == {primary, child}
            assert not app._store_channel._store_channels
            assert not app.gramlot_server._pages
            assert not app.gramlot_server._page_stores
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("origin,cookie_mode", [("https://other.test", "owner"), ("http://test", "missing")])
    async def test_origin_and_owner_are_checked_before_accept(self, origin, cookie_mode):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await open_page(client)
            async with channel(app, cookie if cookie_mode == "owner" else "", page_id, origin=origin) as (opened, _, _):
                assert opened["type"] == "websocket.close"
            assert opened["code"] == 1008
            assert page_id in app.gramlot_server._pages
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_unknown_binder_cannot_mutate_the_store(self):
        app = self.create_application(PAGES, websocket=True)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await open_page(client)
            store = app.gramlot_server.page_store(page_id, owner=client.cookies["gramlot_owner"])
            async with channel(app, cookie, page_id) as (opened, send, receive):
                assert opened["type"] == "websocket.accept"
                await send(dict(op="change", binderId="unknown", path="quantity",
                                evt="upd_value", value="99", attr={}))
                assert (await receive())["code"] == 1008
            assert store.data.get_item("order.quantity") == "2"
        app.gramlot_server.close_all()

    @pytest.mark.asyncio
    async def test_mount_and_page_id_are_checked(self):
        app = self.create_application(PAGES, websocket=True, mount_path="/py")
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            page_id, cookie = await open_page(client, "/py")
            async with channel(app, cookie, page_id, prefix="/py/wrong") as (opened, _, _):
                assert opened["code"] == 1008
            async with channel(app, cookie, "unknown", prefix="/py") as (opened, _, _):
                assert opened["code"] == 1008
        app.gramlot_server.close_all()
