"""Shared channel contract through raw ASGI."""
from gramlot_py_server.uvicorn import create_application
from page_store_checks import PageStoreChecks


class TestPageStore(PageStoreChecks):
    create_application = staticmethod(create_application)


async def test_store_worker_cancellation_drains_before_next_mutation():
    import asyncio
    import threading
    import pytest
    from page_store_checks import PAGES

    app = create_application(PAGES, websocket=True)
    entered, release = threading.Event(), threading.Event()
    mutations = []
    def first():
        entered.set()
        if not release.wait(3):
            raise RuntimeError('Test did not release worker')
        mutations.append('first')
    running = asyncio.create_task(app._invoke_store(first))
    try:
        assert await asyncio.to_thread(entered.wait, 2)
        running.cancel()
        following = asyncio.create_task(app._invoke_store(lambda: mutations.append('second')))
        # The cancelled coroutine still owns the mutation lock while its worker runs.
        await asyncio.sleep(0)
        assert not running.done() and not following.done()
        assert mutations == []
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await running
    await following
    assert mutations == ['first', 'second']
    app.gramlot_server.close_all()
