# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""The HTTP rules that every adapter shares, written once.

The core ``GramlotServer`` and ``GramlotFileServer`` carry every rule that does not
depend on the transport (GC-101 Part A): the request body decoding, the envelopes,
the close message, the companion and theme files, the index mapping. This module
carries what the core leaves to the adapter of an HTTP framework (GC-101 Part B):
the method each URL accepts and the ``Allow`` header of a 405, the ``Cache-Control``
of every response, the owner cookie (section 135), the media types of the served
files, the status codes of the page, rpc and close requests, and the shutdown.

An adapter translates the request of its framework into a ``Request``, awaits
``Adapter.handle`` and translates the ``Reply`` into a response of its framework.
It adds only its routing, its way to read cookies and bodies and its way to
write responses.
"""

from __future__ import annotations

import asyncio
import json
import weakref
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from http.cookies import CookieError, SimpleCookie
from mimetypes import MimeTypes
from pathlib import Path, PurePosixPath
from secrets import token_urlsafe
from types import MappingProxyType
from typing import Any

from gramlot.server import (
    GramlotFileServer,
    InvalidRequest,
    PageNotFound,
    ServerCapacity,
    runtime_asset,
)

TEXT = "text/plain; charset=utf-8"
JSON = "application/json"
JAVASCRIPT = "text/javascript; charset=utf-8"
NO_STORE = "no-store"
# The runtime is the same file for a given core version: the browser may keep it but must revalidate it.
NO_CACHE = "no-cache"


@dataclass(frozen=True)
class Request:
    """One HTTP request in the terms the adapters share.

    ``path`` is the URL path below the mount prefix, percent-decoded once, starting
    with ``/``. ``query`` is the raw query string. ``content_type`` is the
    ``Content-Type`` header as sent. ``owner`` is the value of the owner cookie, or
    ``None``. ``identity`` is the identity of the request that the adapter hands to
    ``GramlotServer.call``, or ``None`` for an adapter without an identity system.
    ``body`` reads the request body; the adapter reads it only when it is asked for.
    """

    method: str
    path: str
    body: Callable[[], Awaitable[bytes]]
    query: str = ""
    content_type: str = ""
    owner: str | None = None
    identity: Any = None


@dataclass(frozen=True)
class Reply:
    """One HTTP response in the terms the adapters share.

    ``content_type`` is the whole ``Content-Type`` value. ``headers`` are the other
    headers, ``Cache-Control`` included, each name once.
    """

    status: int
    body: bytes
    content_type: str
    headers: tuple[tuple[str, str], ...]


def stored(data: bytes) -> Callable[[], Awaitable[bytes]]:
    """The ``Request.body`` of a framework that has already read the body as ``data``."""

    async def read() -> bytes:
        return data

    return read


class Adapter:
    """The server of one pages folder and the HTTP rules of GC-101 Part B.

    A concrete adapter inherits from this class: it builds its routes, turns its
    framework request into a ``Request``, awaits ``handle`` and turns the ``Reply``
    into its framework response.

    ``mount_path`` is the prefix of the request paths and the mount prefix passed to
    ``open_page`` to prefix the root-relative URLs of the browser. The prefix without
    its final slash (``/py``) answers 301 to ``/py/``: pages link each other with
    relative URLs.

    GET and HEAD serve a ``.css`` or ``.js`` file whose real path is below the
    pages folder: the companions of ``GramlotFileServer`` (stylesheet, page module or
    ``_aux.js`` with the page ``Logic``) and ``Page.css`` files placed there.
    Every other file of the folder is not served.

    ``<path>/index.html`` opens the page ``<path>`` and ``/index.html`` the index,
    as a static host does.

    GET and HEAD serve every file below the themes folder of the core at
    ``/themes/…``, with the media type of its extension; a path the core does
    not have goes on to ``assets``, the companions and the pages.

    ``assets`` maps URLs below the mount path to files served by GET and HEAD,
    each ``{"file": path, "type": media type}``, as ``build_gallery`` of
    ``gramlot-examples`` returns them.

    ``content_security_policy`` is the application's policy, sent as the
    ``Content-Security-Policy`` header of each HTML page; ``{nonce}`` in it is
    replaced by the nonce that ``open_page`` puts on the bootstrap script.

    The resolution order of a path is: the web manifest, the runtime, the core themes,
    ``assets``, the companion files, the rpc and close URLs, the pages. A page path
    accepts GET only; every other method, HEAD included, answers 405 with ``Allow: GET``.
    The cookie ``gramlot_owner`` associates a browser with its pages; it is not
    authentication. Every response, errors and redirects included, carries
    ``Cache-Control: no-store``, except the runtime, which carries ``no-cache``
    as the JavaScript servers do.
    """

    METHODS = ("GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS")
    OWNER_COOKIE = "gramlot_owner"
    # The URL suffixes of the companion files and their media types (GC-101 section 145).
    COMPANION_MEDIA_TYPES = MappingProxyType({".css": "text/css; charset=utf-8", ".js": JAVASCRIPT})
    # The built-in table of MimeTypes() ignores the system files. These are the types it
    # lacks in some Python version: fonts and WebP in every one, Markdown before 3.12.
    THEME_MEDIA_TYPES = MappingProxyType({
        ".woff2": "font/woff2",
        ".woff": "font/woff",
        ".ttf": "font/ttf",
        ".otf": "font/otf",
        ".webp": "image/webp",
        ".md": "text/markdown",
    })
    server_class: type[GramlotFileServer] = GramlotFileServer

    def __init__(
        self,
        pages: str | Path,
        *,
        mount_path: str = "",
        page_ttl: float = 1800,
        max_pages: int = 1000,
        content_security_policy: str | None = None,
        assets: dict[str, dict[str, Any]] | None = None,
        collections: Any = (),
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._mount_path = "/" + mount_path.strip("/") if mount_path.strip("/") else ""
        self.content_security_policy = content_security_policy
        self.assets = dict(assets or {})
        self.mime_types = MimeTypes()
        self.gramlot_server = self.server_class(
            pages, page_ttl=page_ttl, max_pages=max_pages, collections=collections
        )

    @property
    def mount_path(self) -> str:
        """The mount prefix: ``/<segments>``, or ``""`` at the root."""
        return self._mount_path

    def shutdown(self) -> None:
        """Forget every registered page: the adapter calls it when its framework stops."""
        self.gramlot_server.close_all()

    def close_at_exit(self) -> weakref.finalize:
        """Forget every registered page when the interpreter exits or the adapter is
        collected. For a framework with no shutdown hook."""
        return weakref.finalize(self, self.gramlot_server.close_all)

    def reply(
        self,
        status: int,
        body: str | bytes = b"",
        content_type: str = TEXT,
        headers: tuple[tuple[str, str], ...] = (),
        cache_control: str = NO_STORE,
    ) -> Reply:
        """A reply with the headers that every response carries."""
        data = body.encode() if isinstance(body, str) else body
        return Reply(status, data, content_type, (("Cache-Control", cache_control), *headers))

    def refuse(self, *allowed: str) -> Reply:
        """The 405 of a URL that accepts only the ``allowed`` methods."""
        return self.reply(405, "Method not allowed", headers=(("Allow", ", ".join(allowed)),))

    def redirect(self, query: str = "") -> Reply:
        """The 301 of the mount prefix without its final slash, the query string kept."""
        location = self.mount_path + "/" + (f"?{query}" if query else "")
        return self.reply(301, headers=(("Location", location),))

    def owner_cookie(self, owner: str) -> str:
        """The ``Set-Cookie`` value of the owner (GC-101 section 135): a session cookie."""
        cookie: SimpleCookie = SimpleCookie()
        cookie[self.OWNER_COOKIE] = owner
        morsel = cookie[self.OWNER_COOKIE]
        morsel["path"] = self.mount_path or "/"
        morsel["httponly"] = True
        morsel["samesite"] = "Lax"
        return cookie.output(header="").strip()

    def owner_of(self, cookie_header: str) -> str | None:
        """The owner in the value of a ``Cookie`` header, or ``None``."""
        cookie: SimpleCookie = SimpleCookie()
        try:
            cookie.load(cookie_header)
        except CookieError:
            return None
        morsel = cookie.get(self.OWNER_COOKIE)
        return morsel.value if morsel else None

    def media_type(self, file: Path) -> str:
        """The media type of a core theme file, by its extension; ``charset`` is added to text."""
        media_type = self.THEME_MEDIA_TYPES.get(file.suffix) or self.mime_types.guess_type(file.name)[0]
        media_type = media_type or "application/octet-stream"
        return f"{media_type}; charset=utf-8" if media_type.startswith("text/") else media_type

    async def handle(self, request: Request) -> Reply:
        """Answer one request below the mount prefix."""
        path, server = request.path, self.gramlot_server
        if path == "/app.webmanifest":
            return await self.manifest(request)
        if path == server.runtime_url:
            return await self.send_file(request, runtime_asset(), JAVASCRIPT, NO_CACHE)
        theme = server.theme_file(path)
        if theme is not None:
            return await self.send_file(request, theme, self.media_type(theme))
        asset = self.assets.get(path)
        if asset is not None:
            return await self.send_file(request, Path(asset["file"]), asset["type"])
        suffix = PurePosixPath(path).suffix
        if suffix in self.COMPANION_MEDIA_TYPES:
            companion = server.companion_file(path)
            if companion is None:
                return self.reply(404, "Not found")
            return await self.send_file(request, companion, self.COMPANION_MEDIA_TYPES[suffix])
        if path in (server.rpc_url, server.close_url):
            return await self.operate(request)
        return await self.page(request)

    async def send_file(self, request: Request, source: Any, media_type: str, cache_control: str = NO_STORE) -> Reply:
        """The file ``source`` for ``GET`` and ``HEAD``."""
        if request.method not in ("GET", "HEAD"):
            return self.refuse("GET", "HEAD")
        body = b"" if request.method == "HEAD" else await asyncio.to_thread(source.read_bytes)
        return self.reply(200, body, media_type, cache_control=cache_control)

    async def manifest(self, request: Request) -> Reply:
        """The web manifest of the installable root page, for ``GET`` and ``HEAD``."""
        if request.method not in ("GET", "HEAD"):
            return self.refuse("GET", "HEAD")
        try:
            manifest = await self.gramlot_server.page_manifest(prefix=self.mount_path)
        except PageNotFound:
            return self.reply(404, "Not found")
        body = b"" if request.method == "HEAD" else json.dumps(manifest).encode()
        return self.reply(200, body, "application/manifest+json")

    async def operate(self, request: Request) -> Reply:
        """The rpc and close requests: ``POST`` of ``application/json`` only."""
        if request.method != "POST":
            return self.refuse("POST")
        if request.content_type.split(";", 1)[0].strip().lower() != JSON:
            return self.reply(415, "Expected application/json")
        server = self.gramlot_server
        try:
            text = server.decode_body(await request.body())
        except InvalidRequest as error:
            return self.reply(400, str(error))
        if request.path == server.rpc_url:
            try:
                result = await server.call(text, owner=request.owner, identity=request.identity)
            except InvalidRequest:
                return self.reply(400, "Invalid envelope")
            return self.reply(200, result, JSON)
        try:
            server.close(text, owner=request.owner)
        except InvalidRequest:
            return self.reply(400, "Invalid JSON request")
        return self.reply(200, json.dumps({"ok": True}), JSON)

    async def page(self, request: Request) -> Reply:
        """The bootstrap document of the page at the path, for ``GET`` only."""
        if request.method != "GET":
            return self.refuse("GET")
        owner = request.owner or token_urlsafe(24)
        try:
            opened = await self.gramlot_server.open_page(request.path, owner=owner, prefix=self.mount_path)
        except PageNotFound:
            return self.reply(404, "Page not found")
        except ServerCapacity:
            return self.reply(503, "Page capacity reached")
        headers = [("Set-Cookie", self.owner_cookie(owner))]
        if self.content_security_policy is not None:
            policy = self.content_security_policy.replace("{nonce}", opened.nonce)
            headers.append(("Content-Security-Policy", policy))
        return self.reply(200, opened.html, "text/html; charset=utf-8", tuple(headers))
