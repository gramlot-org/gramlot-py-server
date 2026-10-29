# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Kajenn integration for the Gramlot server protocol."""

from __future__ import annotations

import asyncio
import inspect
import re
from contextlib import asynccontextmanager
from contextvars import ContextVar
from pathlib import Path

from genro_routes import route
from genro_toolbox import tags_match
from .collection_resources import _CollectionFileServer
from kajenn import RoutedApplication
from kajenn.exceptions import HTTPException, WebSocketDisconnect
from kajenn.websocket import WebSocket

from gramlot_py_server import base
from gramlot_py_server.store_channel import _StoreChannel
from gramlot_py_server.gallery import add_gallery
from gramlot_py_server.scaffold import add_new


class _KajennFileServer(_CollectionFileServer):
    """The core ``GramlotFileServer`` with the capability ``auth``.

    ``evaluate_auth`` evaluates a rule with ``genro_toolbox.tags_match`` against
    the tags of the Kajenn avatar that the adapter passes with each call
    (``identity``), as the genro-routes ``AuthPlugin`` does for route entries. The
    server keeps no identity: HTTP supplies it per request, WebSocket at handshake.
    """

    async def _invoke(self, function, *args, **kwargs):
        return await self._database_access._invoke_page(function, *args, **kwargs)

    @property
    def capabilities(self) -> list[str]:
        """The capabilities announced in the bootstrap: ``auth``."""
        return ["auth"]

    def evaluate_auth(self, rule, *, owner, identity):
        """``None`` when the tags of the avatar ``identity`` satisfy ``rule``, else
        ``"not_authenticated"`` (no avatar) or ``"not_authorized"``."""
        if rule is None:
            return None
        if identity is None:
            return "not_authenticated"
        return None if tags_match(rule, set(identity.tags)) else "not_authorized"


class Application(base.Adapter, RoutedApplication):
    """A Kajenn routed application backed by ``gramlot.server.GramlotFileServer``.

    The application builds ``_KajennFileServer``, a ``GramlotFileServer`` with the
    capability ``auth``: an ``auth`` rule is evaluated with ``tags_match`` against
    the tags of the Kajenn avatar of the request (``request.avatar()``), which the
    application passes to ``GramlotServer.call`` with each rpc request.

    Declare it in the site recipe with ``request(body="raw")``: the request
    envelope reaches ``GramlotServer.call`` as the TYTX text the browser sent,
    without Kajenn's TYTX hydration. The application's
    Kajenn ``mount`` is passed to ``open_page`` as the mount prefix of browser
    URLs. The mount without the final slash (``/py``) answers 301 to ``/py/``:
    pages link each other with relative URLs. Kajenn routes ``/py`` and ``/py/``
    alike; the application tells them apart by the ASGI ``raw_path``.
    An empty ``mount`` puts the application at the site root, without prefix.

    The HTTP rules, the same in every adapter, are those of ``gramlot_py_server.base``.
    """

    server_class = _KajennFileServer

    def __init__(self, pages: str | Path, *, mount_path: None = None, websocket: bool = False, **options) -> None:
        if mount_path is not None:
            raise TypeError("mount_path is the mount of the Kajenn application: declare mount in the site recipe")
        super().__init__(pages, **options)
        self.gramlot_server._database_access = self
        self._operation_lock = asyncio.Lock()
        self._execution = ContextVar("gramlot_kajenn_execution", default=None)
        self._store_channel = _StoreChannel(self.gramlot_server, self.gramlot_server._invoke, self._store_request)
        self.gramlot_server.websocket_url = "/gramlot/store" if websocket else None
        if self.mount != "" and not re.fullmatch(r"[a-z][a-z0-9_-]*", self.mount or ""):
            raise ValueError("mount must be a single lowercase URL segment or empty")

    @property
    def mount_path(self) -> str:
        """The mount prefix of the browser URLs: ``/<mount>``, or ``""`` at the site root."""
        return f"/{self.mount}" if self.mount else ""

    @route(media_type="text/html")
    async def index(self, *segments, _request, body_raw=None, **_query):
        """Every URL below the mount.

        Kajenn has already removed the mount from request.path. Route arguments
        omit an explicit "index" selector, so they cannot identify the file path.
        """
        query = _request.scope.get("query_string", b"").decode("latin-1")
        if self.mount and _request.scope.get("raw_path") == f"/{self.mount}".encode():
            reply = self.redirect(query)
        else:
            async with self._operation():
                reply = await self.handle(base.Request(
                    method=_request.method,
                    path=_request.path,
                    body=lambda: self.read_body(body_raw),
                    query=query,
                    content_type=str(_request.content_type or ""),
                    owner=_request.cookies.get(self.OWNER_COOKIE),
                    identity=_request.avatar(),
                ))
        for name, value in reply.headers:
            _request.response.set_header(name, value)
        _request.response.status_code = reply.status
        return self.result_wrapper(reply.body, media_type=reply.content_type)

    @asynccontextmanager
    async def _operation(self, *, register=False):
        async with self._operation_lock:
            token = self._execution.set(True)
            call = self.server.requests.register({
                "type": "websocket", "path": self.mount_path + "/gramlot/store",
            }) if register else None
            try:
                yield
            finally:
                try:
                    if call is not None:
                        try:
                            await call.run_cleanups()
                        finally:
                            self.server.requests.unregister(call)
                finally:
                    self._execution.reset(token)

    def _store_request(self):
        return self._operation(register=True)

    async def _invoke_page(self, function, *args, **kwargs):
        """Use Kajenn's pool and release sync databases on their owning thread."""
        if self._execution.get() is None:
            raise RuntimeError("Page execution requires a Kajenn operation")
        if inspect.iscoroutinefunction(function):
            result = function(*args, **kwargs)
        else:
            def run():
                try:
                    return function(*args, **kwargs)
                finally:
                    self.server.release_databases(self.server.requests.current)
            worker = asyncio.create_task(self.server.run_sync(run))
            try:
                result = await asyncio.shield(worker)
            except asyncio.CancelledError:
                # A Python worker cannot be interrupted; drain it before releasing
                # its operation and allowing another mutation of the live Bags.
                await self._drain(asyncio.gather(worker, return_exceptions=True))
                raise
        if not inspect.isawaitable(result):
            return result
        self._operation_lock.release()
        try:
            return await result
        finally:
            waiter = asyncio.create_task(self._operation_lock.acquire())
            try:
                await asyncio.shield(waiter)
            except asyncio.CancelledError:
                await self._drain(waiter)
                raise

    @staticmethod
    async def _drain(task):
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
        return task.result()

    async def serve_websocket(self, scope, receive, send):
        """Kajenn demux passes its native socket seam with the mount removed."""
        socket = WebSocket(scope, receive, send)
        cookie = self.handshake_cookie
        if cookie is not None and cookie not in socket.cookies:
            await socket.refuse(1008, "connection cookie required")
            return
        try:
            identity = await self.server.authenticate(scope)
        except HTTPException:
            await socket.refuse(1008, "unauthorized")
            return
        self.server.websockets.register(socket)
        try:
            await self._store_channel.serve(
                socket, scope, owner=socket.cookies.get(self.OWNER_COOKIE),
                path="/gramlot/store", disconnect_error=WebSocketDisconnect,
                identity=identity,
            )
        finally:
            self.server.websockets.unregister(socket)

    async def read_body(self, body_raw: bytes | None) -> bytes:
        """The raw request body, which the site recipe must declare with ``request(body="raw")``."""
        if not self.raw_body:
            raise RuntimeError("Application requires request(body='raw')")
        return body_raw or b""

    def on_shutdown(self) -> None:
        """Forget every registered page when the Kajenn server stops."""
        self.shutdown()


def serve(pages: str | Path, *, host: str = "127.0.0.1", port: int = 8000, mount_path: str = "",
          **options) -> None:
    """Serve ``pages`` in a Kajenn site until it stops; ``mount_path`` is the Kajenn mount."""
    from kajenn import AsgiServer
    from kajenn.config.templates import DefaultConfiguration

    class Site(DefaultConfiguration):
        def applications_section(self, cfg):
            cfg.applications().application(
                code="pages", mount=mount_path.strip("/"), app_class=Application, pages=pages, **options,
            ).request(body="raw")

    AsgiServer(config=Site).serve(host=host, port=port)


def commands(verbs) -> None:
    """The verbs of ``gramlot kajenn``: an entry point of ``gramlot_py_server.commands``."""
    add_new(verbs, "kajenn", start="kajenn serve config.py --port 8000", url="http://127.0.0.1:8000/pages/")
    add_gallery(verbs, "kajenn", serve)


__all__ = ["Application"]
