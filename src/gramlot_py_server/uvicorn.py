# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""ASGI application for Uvicorn or another ASGI server serving Gramlot pages."""

from __future__ import annotations

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

    async def __call__(self, scope, receive, send) -> None:
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
        headers = [
            (b"content-type", reply.content_type.encode()),
            (b"content-length", str(len(reply.body)).encode()),
            *((name.lower().encode("latin-1"), value.encode("latin-1")) for name, value in reply.headers),
        ]
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
