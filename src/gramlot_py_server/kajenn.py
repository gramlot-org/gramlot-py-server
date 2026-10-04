# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Kajenn integration for the Gramlot ``Host`` protocol."""

from __future__ import annotations

import json
import re
from pathlib import Path
from secrets import token_urlsafe

from genro_routes import RoutingClass, route
from gramlot.server import (
    FileHost,
    HostCapacity,
    PageExpired,
    PageNotFound,
    SourceNotFound,
    runtime_asset,
)
from kajenn import (
    HTTPBadRequest,
    HTTPException,
    HTTPNotFound,
    HTTPUnsupportedMediaType,
    RoutedApplication,
)

from gramlot_py_server.scaffold import add_new

MAX_REQUEST_BYTES = 4096
OWNER_COOKIE = "gramlot_owner"
COMPANION_MEDIA_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}


class _RuntimeAssets(RoutingClass):
    def __init__(self, application):
        self.application = application

    @route(name="gramlot.js", media_type="text/javascript")
    def runtime(self, _request, **_query):
        self.application.require_method(_request, "GET", "HEAD")
        _request.response.set_header("Cache-Control", "no-cache")
        return b"" if _request.method == "HEAD" else runtime_asset().read_bytes()

    @route(media_type="text/html")
    async def index(self, *segments, _request, **_query):
        """Every other path below ``assets/``: the application's assets, companions and pages."""
        return await self.application.index("assets", *segments, _request=_request, **_query)


class _Protocol(RoutingClass):
    def __init__(self, application):
        self.application = application

    @route(media_type="application/json")
    async def main(self, _request, body_raw=None, **_query):
        return await self.application.operation(_request, body_raw, "main")

    @route(media_type="application/json")
    async def source(self, _request, body_raw=None, **_query):
        return await self.application.operation(_request, body_raw, "source")

    @route(media_type="application/json")
    async def close(self, _request, body_raw=None, **_query):
        return await self.application.operation(_request, body_raw, "close")


class Application(RoutedApplication):
    """A Kajenn routed application backed by ``gramlot.server.FileHost``.

    Declare it in the site recipe with ``request(body="raw")``: the protocol
    reads JSON with ``json.loads``, not with TYTX hydration. The application's
    Kajenn ``mount`` is passed to ``open_page`` as the mount prefix of browser
    URLs. The mount without the final slash (``/py``) answers 301 to ``/py/``:
    pages link each other with relative URLs. Kajenn routes ``/py`` and ``/py/``
    alike; the application tells them apart by the ASGI ``raw_path``.

    GET and HEAD serve a ``.css`` or ``.js`` file whose real path is below the
    pages folder: the companions of ``FileHost`` (stylesheet, page module or
    ``_aux.js`` with the page ``Logic``) and ``Page.css`` files placed there.
    Every other file of the folder is not served.

    ``assets`` maps URLs below the mount to files served by GET and HEAD,
    each ``{"file": path, "type": media type}``, as ``build_gallery`` of
    ``gramlot-examples`` returns them.

    ``content_security_policy`` is the application's policy, sent as the
    ``Content-Security-Policy`` header of each HTML page; ``{nonce}`` in it is
    replaced by the nonce that ``open_page`` puts on the bootstrap script.
    """

    def __init__(self, pages: str | Path, *, page_ttl: float = 1800, max_pages: int = 1000,
                 content_security_policy: str | None = None, assets: dict | None = None,
                 **kwargs) -> None:
        super().__init__(**kwargs)
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", self.mount or ""):
            raise ValueError("mount must be a single lowercase URL segment")
        self.content_security_policy = content_security_policy
        self.assets = dict(assets or {})
        self.host = FileHost(
            pages,
            runtime_url="/assets/gramlot.js",
            main_url="/gramlot/main",
            source_url="/gramlot/source",
            close_url="/gramlot/close",
            page_ttl=page_ttl,
            max_pages=max_pages,
        )
        self.add_branches([
            {"name": "assets", "instance": _RuntimeAssets(self)},
            {"name": "gramlot", "instance": _Protocol(self)},
        ])

    @route(media_type="text/html")
    async def index(self, *segments, _request, **_query):
        page_path = "/".join(segments)
        if _request.scope.get("raw_path") == f"/{self.mount}".encode():
            return self.redirect(_request)
        asset = self.assets.get("/" + page_path)
        if asset is not None:
            return self.static(_request, asset)
        suffix = next((suffix for suffix in COMPANION_MEDIA_TYPES if page_path.endswith(suffix)), None)
        if suffix is not None:
            return self.companion(_request, page_path, suffix)
        self.require_method(_request, "GET")
        owner = _request.cookies.get(OWNER_COOKIE) or token_urlsafe(24)
        try:
            opened = await self.host.open_page(page_path, owner=owner, prefix=f"/{self.mount}")
        except PageNotFound as error:
            raise HTTPNotFound("Page not found") from error
        except HostCapacity as error:
            raise HTTPException(503, "Page capacity reached") from error
        _request.response.set_header("Cache-Control", "no-store")
        if self.content_security_policy is not None:
            policy = self.content_security_policy.replace("{nonce}", opened.nonce)
            _request.response.set_header("Content-Security-Policy", policy)
        _request.response.set_cookie(
            OWNER_COOKIE, owner, path=f"/{self.mount}", httponly=True, samesite="lax"
        )
        return opened.html

    def redirect(self, request):
        """Answer the mount without the final slash with 301 to the mount with it."""
        query = request.scope.get("query_string", b"").decode("latin-1")
        request.response.status_code = 301
        request.response.set_header("Location", f"/{self.mount}/" + (f"?{query}" if query else ""))
        return self.result_wrapper(b"", media_type="text/plain")

    def static(self, request, asset):
        """Serve one file of ``assets`` with its media type."""
        self.require_method(request, "GET", "HEAD")
        request.response.set_header("Cache-Control", "no-store")
        body = b"" if request.method == "HEAD" else Path(asset["file"]).read_bytes()
        return self.result_wrapper(body, media_type=asset["type"])

    def companion(self, request, page_path: str, suffix: str):
        """Serve the file of ``page_path`` when its real path is below the pages folder."""
        self.require_method(request, "GET", "HEAD")
        root = self.host.pages_dir.resolve()
        real = root.joinpath(*page_path.split("/")).resolve()
        if not (real.is_relative_to(root) and real.is_file()):
            raise HTTPNotFound("Not found")
        request.response.set_header("Cache-Control", "no-store")
        body = b"" if request.method == "HEAD" else real.read_bytes()
        return self.result_wrapper(body, media_type=COMPANION_MEDIA_TYPES[suffix])

    def require_method(self, request, *methods: str) -> None:
        if request.method not in methods:
            raise HTTPException(405, "Method not allowed")

    async def operation(self, request, body_raw: bytes | None, operation: str) -> str:
        self.require_method(request, "POST")
        if not self.raw_body:
            raise RuntimeError("Application requires request(body='raw')")
        content_type = str(request.content_type or "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise HTTPUnsupportedMediaType("Expected application/json")
        raw = body_raw or b""
        if len(raw) > MAX_REQUEST_BYTES:
            raise HTTPException(413, "Request too large")
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict) or not isinstance(payload.get("pageId"), str):
                raise ValueError
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            raise HTTPBadRequest("Invalid JSON request") from error
        if operation == "source" and not isinstance(payload.get("params", {}), dict):
            raise HTTPBadRequest("Source params must be a dictionary")
        owner = request.cookies.get(OWNER_COOKIE)
        request.response.set_header("Cache-Control", "no-store")
        try:
            result: str
            if operation == "main":
                result = await self.host.main(payload["pageId"], owner=owner)
            elif operation == "source":
                result = await self.host.source(
                    payload["pageId"], payload.get("method"), payload.get("params", {}), owner=owner
                )
            else:
                self.host.close_page(payload["pageId"], owner=owner)
                result = json.dumps({"ok": True})
        except PageExpired as error:
            raise HTTPNotFound("Unknown page") from error
        except SourceNotFound as error:
            raise HTTPNotFound("Unknown Source method") from error
        return result


def commands(verbs) -> None:
    """The verbs of ``gramlot kajenn``: an entry point of ``gramlot_py_server.commands``."""
    add_new(verbs, "kajenn", start="kajenn serve config.py --port 8000", url="http://127.0.0.1:8000/pages/")


__all__ = ["Application"]
