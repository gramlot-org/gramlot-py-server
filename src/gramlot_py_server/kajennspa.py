# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Gramlot pages as branches of a session-backed Kajenn SPA."""

from __future__ import annotations

import asyncio
import re
from contextvars import ContextVar

from genro_routes import RoutingClass, route
from gramlot import Page as GramlotPage, PageStore as GramlotPageStore
from gramlot.server import PageExpired
from kajenn import Page as KajennPage, Request, SpaApplicationBase, SpaRegistry
from kajenn.exceptions import HTTPForbidden, WebSocketDisconnect
from kajenn.spa_registry import UnknownPage
from kajenn.websocket import WebSocket

from . import base
from .kajenn import Application as LegacyApplication, _KajennFileServer, _KajennOperations
from .store_channel import _StoreChannel
from .terminal_channel import _TerminalChannel

__all__ = ["Application", "Page", "PageStore", "PagesDispatcher"]


class Page(GramlotPage, KajennPage):
    """A Gramlot Page bound to its SPA application and logical page ID."""

    def __init__(self, application=None, page_id=None, connection_id=None):
        # Manifest generation may construct a page before a visit exists.
        super().__init__(application, page_id, connection_id)
        self._database_access = application

    @property
    def request_identity(self):
        if self.application is None:
            return getattr(self, "_request_identity", None)
        return self.application._page_identity.get()

    @property
    def store(self):
        """The live Gramlot PageStore, retained across instance eviction."""
        return self.state.page_store["store"]


class PageStore(GramlotPageStore):
    """A store that may rebuild shared bindings after a verified session login."""

    def on_user_changed(self, previous, current):
        """Rebind authorized views after the adapter has cleared the old bindings."""


class _Registry(SpaRegistry):
    def new_store(self):
        return {}

    def page_user_changed(self, previous, current):
        store = current.page_store.get("store")
        if store is not None:
            store.unbind_paths()
            if isinstance(store, PageStore):
                store.on_user_changed(previous, current)

    def page_detached(self, state):
        server = state.page_store.get("server")
        if server is not None:
            server.release_gramlot_page(state.page_id, state.connection_id)


class _SpaFileServer(_KajennFileServer):
    @property
    def capabilities(self):
        return [*super().capabilities, "pageStoreReconnect"]

    def register_page(self, cls, *, owner, path):
        if not issubclass(cls, Page):
            raise TypeError("A kajennspa page must extend gramlot_py_server.kajennspa.Page")
        pid = super().register_page(cls, owner=owner, path=path)
        registry = self.application.registry
        try:
            registry.new_page(pid, connection_id=owner, page_class=cls)
            registry.page_state(pid, connection_id=owner).page_store["server"] = self
        except BaseException:
            super().close_page(pid, owner=owner)
            raise
        return pid

    def create_page_store(self, store_class, *, page_id, owner):
        store = super().create_page_store(store_class, page_id=page_id, owner=owner)
        store.application = self.application
        store.page_id = page_id
        store.connection_id = owner
        self.application.registry.page_state(page_id, connection_id=owner).page_store["store"] = (
            store
        )
        return store

    def resolve_page_store(self, page_class):
        cls = super().resolve_page_store(page_class)
        return PageStore if cls is GramlotPageStore else cls

    def page_for_call(self, cls, *, page_id, owner, identity):
        try:
            return self.application.registry.resolve_page(
                self.application, page_id, connection_id=owner
            )
        except UnknownPage as error:
            raise PageExpired("Unknown, expired or unowned page") from error

    async def call(self, text, *, owner=None, identity=None):
        token = self.application._page_identity.set(identity)
        try:
            return await super().call(text, owner=owner, identity=identity)
        finally:
            self.application._page_identity.reset(token)

    def close_page(self, page_id, *, owner=None):
        try:
            state = self.application.registry.page_state(page_id, connection_id=owner)
        except UnknownPage:
            return
        if state.page_store.get("server") is self:
            self.application.registry.drop_page(page_id, connection_id=owner)

    def release_gramlot_page(self, page_id, owner):
        super().close_page(page_id, owner=owner)

    def close_all(self):
        for pid, record in list(self._pages.items()):
            self.close_page(pid, owner=record[2])
        super().close_all()


class PagesDispatcher(_KajennOperations, base.Adapter, RoutingClass):
    """Serve one pages folder below a named branch of the application."""

    server_class = _SpaFileServer

    def __init__(self, application, name, pages, *, websocket=True, **options):
        self.application = application
        self.name = name
        prefix = "/".join(filter(None, (application.mount, name)))
        # Adapter builds the file server before collection discovery.
        super().__init__(pages, mount_path=prefix, **options)
        self._init_operations(application._operation_lock)
        self.gramlot_server.application = application
        self.gramlot_server._database_access = self
        self.gramlot_server.websocket_url = "/gramlot/store" if websocket else None
        self._store_channel = _StoreChannel(
            self.gramlot_server,
            self._invoke_page,
            self._store_request,
            keep_pages_on_disconnect=True,
        )
        self._terminal_channel = _TerminalChannel(self.gramlot_server, self._operation)
        self.route.plug("pydantic")

    @property
    def server(self):
        return self.application.server

    def db(self, name=None):
        return self.application.db(name)

    def async_db(self, name=None):
        return self.application.async_db(name)

    @route(media_type="text/html", channel_channels="api")
    async def index(self, *segments, _request, body_raw=None, **_query):
        path = _request.path.removeprefix("/" + self.name)
        query = _request.scope.get("query_string", b"").decode("latin-1")
        if not path:
            reply = self.redirect(query)
        else:
            async with self._operation():
                cid = self.application.connection_id(_request)
                reply = await self.handle(
                    base.Request(
                        method=_request.method,
                        path=path,
                        query=query,
                        body=base.stored(body_raw or b""),
                        owner=cid,
                        identity=_request.avatar(),
                        content_type=str(_request.content_type or ""),
                        if_none_match=LegacyApplication.raw_header(_request, b"if-none-match"),
                        if_modified_since=LegacyApplication.raw_header(
                            _request, b"if-modified-since"
                        ),
                    )
                )
        for name, value in reply.headers:
            if name.lower() != "set-cookie":
                _request.response.set_header(name, value)
        _request.response.status_code = reply.status
        return self.application.result_wrapper(reply.body, media_type=reply.content_type)

    async def serve_socket(self, socket, scope, owner):
        channel = (
            self._terminal_channel if scope["path"] == "/gramlot/terminal" else self._store_channel
        )
        await channel.serve(
            socket,
            scope,
            owner=owner,
            path=scope["path"],
            identity=scope.get("auth"),
            disconnect_error=WebSocketDisconnect,
        )


class Application(SpaApplicationBase):
    """Mount typed API routes and one or more Gramlot page dispatchers together."""

    registry_class = _Registry
    uses_session_websocket = True

    def __init__(self, pages=None, *, branch="pages", websocket=True, **kwargs):
        super().__init__(**kwargs)
        self._dispatchers = {}
        self._operation_lock = asyncio.Lock()
        self._page_identity = ContextVar("gramlot_page_identity", default=None)
        if pages is not None:
            self.add_pages(branch, pages, websocket=websocket)

    def add_pages(self, name, pages, **options):
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
            raise ValueError("Pages branch must be a single lowercase path segment")
        dispatcher = PagesDispatcher(self, name, pages, **options)
        self.route.add_branches({"name": name, "instance": dispatcher})
        self._dispatchers[name] = dispatcher
        return dispatcher

    def raw_body_for_path(self, path):
        return path.lstrip("/").partition("/")[0] in self._dispatchers or super().raw_body_for_path(
            path
        )

    async def serve_websocket(self, scope, receive, send):
        name, _, suffix = scope["path"].lstrip("/").partition("/")
        dispatcher = self._dispatchers.get(name)
        socket = WebSocket(scope, receive, send)
        if dispatcher is None or suffix not in ("gramlot/store", "gramlot/terminal"):
            await socket.refuse(1008, "Unknown Gramlot channel")
            return
        try:
            async with dispatcher._operation():
                cid = self.connection_id(
                    Request(scope, receive, server=self.server, application=self)
                )
        except HTTPForbidden:
            await socket.refuse(1008, "A live SPA visit is required")
            return
        self.server.websockets.register(socket)
        try:
            await dispatcher.serve_socket(socket, {**scope, "path": "/" + suffix}, cid)
        finally:
            self.server.websockets.unregister(socket)

    def on_shutdown(self):
        for dispatcher in self._dispatchers.values():
            dispatcher.shutdown()

    def on_remove(self):
        self.on_shutdown()
