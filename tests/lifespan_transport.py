"""HTTPX test transport that also runs the server's ASGI lifespan."""

import asyncio
import httpx


class LifespanTransport(httpx.ASGITransport):
    instances = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._lifespan_task = None
        self.instances.append(self)

    async def handle_async_request(self, request):
        if self._lifespan_task is None:
            self._events = asyncio.Queue()
            self._answers = asyncio.Queue()
            self._lifespan_task = asyncio.create_task(
                self.app({"type": "lifespan"}, self._events.get, self._answers.put)
            )
            await self._events.put({"type": "lifespan.startup"})
            answer = await self._answers.get()
            if answer["type"] != "lifespan.startup.complete":
                await self._lifespan_task
                raise RuntimeError(answer.get("message", answer["type"]))
        return await super().handle_async_request(request)

    async def shutdown(self):
        if self._lifespan_task is not None and not self._lifespan_task.done():
            await self._events.put({"type": "lifespan.shutdown"})
            assert (await self._answers.get())["type"] == "lifespan.shutdown.complete"
            await self._lifespan_task
        await super().aclose()

    async def aclose(self):
        await super().aclose()
