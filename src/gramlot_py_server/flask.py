# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Flask integration for the Gramlot ``Host`` protocol."""

from __future__ import annotations

import asyncio
import json
from importlib.resources import files
from mimetypes import MimeTypes
from pathlib import Path
from secrets import token_urlsafe

from flask import Blueprint, Response, request
from gramlot.server import (
    FileHost,
    HostCapacity,
    PageExpired,
    PageNotFound,
    SourceNotFound,
    runtime_asset,
)

from gramlot_py_server.scaffold import add_new

MAX_REQUEST_BYTES = 4096
OWNER_COOKIE = "gramlot_owner"
COMPANION_MEDIA_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}
# The core themes, served below the mount path as the runtime is. The built-in
# table of MimeTypes() ignores the system files; it lacks the font types.
THEMES = Path(str(files("gramlot").joinpath("resources", "themes")))
MEDIA_TYPES = MimeTypes()
FONT_MEDIA_TYPES = {".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf"}


def theme_file(path: str) -> dict | None:
    """The file of the core themes at ``path`` (``/themes/…``), as an ``assets`` entry.

    Every file whose real path is below ``gramlot/resources/themes`` is served
    with the media type of its extension; ``None`` lets the request go on.
    """
    if not path.startswith("/themes/"):
        return None
    root = THEMES.resolve()
    real = root.joinpath(*path.removeprefix("/themes/").split("/")).resolve()
    if not (real.is_relative_to(root) and real.is_file()):
        return None
    media_type = FONT_MEDIA_TYPES.get(real.suffix) or MEDIA_TYPES.guess_type(real.name)[0]
    media_type = media_type or "application/octet-stream"
    if media_type.startswith("text/"):
        media_type += "; charset=utf-8"
    return {"file": real, "type": media_type}


class Pages:
    """Own a Gramlot ``FileHost`` and its WSGI route translations.

    The blueprint is registered at ``mount_path``, which is also passed to
    ``open_page`` as the mount prefix of browser URLs. The prefix without the
    final slash (``/py``) answers 301 to ``/py/``: pages link each other with
    relative URLs.

    GET and HEAD serve a ``.css`` or ``.js`` file whose real path is below the
    pages folder: the companions of ``FileHost`` (stylesheet, page module or
    ``_aux.js`` with the page ``Logic``) and ``Page.css`` files placed there.
    Every other file of the folder is not served.

    GET and HEAD serve every file below the themes folder of the core at
    ``/themes/…``, with the media type of its extension; a path the core does
    not have goes on to ``assets``, the companions and the pages.

    ``assets`` maps URLs below the mount path to files served by GET and HEAD,
    each ``{"file": path, "type": media type}``, as ``build_gallery`` of
    ``gramlot-examples`` returns them.

    ``content_security_policy`` is the application's policy, sent as the
    ``Content-Security-Policy`` header of each HTML page; ``{nonce}`` in it is
    replaced by the nonce that ``open_page`` puts on the bootstrap script.
    """

    def __init__(self, pages: str | Path, *, mount_path: str = "", page_ttl: float = 1800,
                 max_pages: int = 1000, content_security_policy: str | None = None,
                 assets: dict | None = None) -> None:
        self.mount_path = "/" + mount_path.strip("/") if mount_path.strip("/") else ""
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

    def blueprint(self) -> Blueprint:
        name = "gramlot_pages_" + (self.mount_path.strip("/") or "root").replace("/", "_")
        blueprint = Blueprint(name, __name__, url_prefix=self.mount_path or None)
        blueprint.add_url_rule("/assets/gramlot.js", "asset", self.asset, methods=["GET", "HEAD"])
        blueprint.add_url_rule("/gramlot/main", "main", self.main, methods=["POST"])
        blueprint.add_url_rule("/gramlot/source", "source", self.source, methods=["POST"])
        blueprint.add_url_rule("/gramlot/close", "close", self.close, methods=["POST"])
        if self.mount_path:
            blueprint.add_url_rule("", "mount", self.redirect, strict_slashes=False)
        blueprint.add_url_rule("/", "index", self.page, defaults={"page_path": ""})
        blueprint.add_url_rule("/<path:page_path>", "page", self.page)
        return blueprint

    def redirect(self) -> Response:
        query = request.query_string.decode("latin-1")
        location = self.mount_path + "/" + (f"?{query}" if query else "")
        return Response(status=301, headers={"Location": location})

    def asset(self) -> Response:
        body = b"" if request.method == "HEAD" else runtime_asset().read_bytes()
        return Response(body, mimetype="text/javascript", headers={"Cache-Control": "no-cache"})

    def page(self, page_path="") -> Response:
        asset = theme_file("/" + page_path) or self.assets.get("/" + page_path)
        if asset is not None:
            return self.static(asset)
        suffix = next((suffix for suffix in COMPANION_MEDIA_TYPES if page_path.endswith(suffix)), None)
        if suffix is not None:
            return self.companion(page_path, suffix)
        owner = request.cookies.get(OWNER_COOKIE) or token_urlsafe(24)
        try:
            opened = asyncio.run(self.host.open_page(page_path, owner=owner, prefix=self.mount_path))
        except PageNotFound:
            return Response("Page not found", status=404)
        except HostCapacity:
            return Response("Page capacity reached", status=503)
        headers = {"Cache-Control": "no-store"}
        if self.content_security_policy is not None:
            headers["Content-Security-Policy"] = self.content_security_policy.replace("{nonce}", opened.nonce)
        response = Response(opened.html, mimetype="text/html", headers=headers)
        response.set_cookie(
            OWNER_COOKIE,
            owner,
            path=self.mount_path or "/",
            httponly=True,
            samesite="Lax",
        )
        return response

    def static(self, asset) -> Response:
        """Serve one file of ``assets`` with its media type."""
        body = b"" if request.method == "HEAD" else Path(asset["file"]).read_bytes()
        return Response(body, content_type=asset["type"], headers={"Cache-Control": "no-store"})

    def companion(self, page_path: str, suffix: str) -> Response:
        """Serve the file of ``page_path`` when its real path is below the pages folder."""
        root = self.host.pages_dir.resolve()
        real = root.joinpath(*page_path.strip("/").split("/")).resolve()
        if not (real.is_relative_to(root) and real.is_file()):
            return Response("Not found", status=404)
        body = b"" if request.method == "HEAD" else real.read_bytes()
        return Response(body, content_type=COMPANION_MEDIA_TYPES[suffix],
                        headers={"Cache-Control": "no-store"})

    def main(self) -> Response:
        return self._operation("main")

    def source(self) -> Response:
        return self._operation("source")

    def close(self) -> Response:
        return self._operation("close")

    def _operation(self, operation: str) -> Response:
        if request.mimetype != "application/json":
            return Response("Expected application/json", status=415)
        if request.content_length is not None and request.content_length > MAX_REQUEST_BYTES:
            return Response("Request too large", status=413)
        raw = request.get_data(cache=False)
        if len(raw) > MAX_REQUEST_BYTES:
            return Response("Request too large", status=413)
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict) or not isinstance(payload.get("pageId"), str):
                raise ValueError
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            return Response("Invalid JSON request", status=400)
        owner = request.cookies.get(OWNER_COOKIE)
        if operation == "source" and not isinstance(payload.get("params", {}), dict):
            return Response("Source params must be a dictionary", status=400)
        try:
            if operation == "main":
                result = asyncio.run(self.host.main(payload["pageId"], owner=owner))
            elif operation == "source":
                result = asyncio.run(self.host.source(
                    payload["pageId"], payload.get("method"), payload.get("params", {}), owner=owner
                ))
            else:
                self.host.close_page(payload["pageId"], owner=owner)
                result = json.dumps({"ok": True})
        except PageExpired:
            return Response("Unknown page", status=404)
        except SourceNotFound:
            return Response("Unknown Source method", status=404)
        return Response(result, mimetype="application/json", headers={"Cache-Control": "no-store"})


def mount_pages(app, pages: str | Path, **options) -> Pages:
    """Mount the bounded Gramlot page protocol on an existing Flask app."""

    integration = Pages(pages, **options)
    app.register_blueprint(integration.blueprint())
    app.extensions.setdefault("gramlot_pages", {})[integration.mount_path] = integration
    return integration


def commands(verbs) -> None:
    """The verbs of ``gramlot flask``: an entry point of ``gramlot_py_server.commands``."""
    add_new(verbs, "flask", start="flask --app app run", url="http://127.0.0.1:5000/")


__all__ = ["Pages", "mount_pages"]
