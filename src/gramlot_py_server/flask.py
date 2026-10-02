# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Flask integration for the Gramlot ``Host`` protocol."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from secrets import token_urlsafe

from flask import Blueprint, Response, request
from gramlot.server import Host, HostCapacity, PageExpired, PageNotFound, SourceNotFound, runtime_asset

MAX_REQUEST_BYTES = 4096
OWNER_COOKIE = "gramlot_owner"


class Pages:
    """Own one neutral Host and its WSGI route translations."""

    def __init__(self, pages: str | Path, *, prefix="", page_ttl=1800, max_pages=1000):
        self.prefix = "/" + prefix.strip("/") if prefix.strip("/") else ""
        self.host = Host(
            pages,
            runtime_url=f"{self.prefix}/assets/gramlot.js",
            main_url=f"{self.prefix}/gramlot/main",
            source_url=f"{self.prefix}/gramlot/source",
            close_url=f"{self.prefix}/gramlot/close",
            page_ttl=page_ttl,
            max_pages=max_pages,
        )

    def blueprint(self) -> Blueprint:
        name = "gramlot_pages_" + (self.prefix.strip("/") or "root").replace("/", "_")
        blueprint = Blueprint(name, __name__, url_prefix=self.prefix or None)
        blueprint.add_url_rule("/assets/gramlot.js", "asset", self.asset, methods=["GET", "HEAD"])
        blueprint.add_url_rule("/gramlot/main", "main", self.main, methods=["POST"])
        blueprint.add_url_rule("/gramlot/source", "source", self.source, methods=["POST"])
        blueprint.add_url_rule("/gramlot/close", "close", self.close, methods=["POST"])
        blueprint.add_url_rule("/", "index", self.page, defaults={"page_path": ""})
        blueprint.add_url_rule("/<path:page_path>", "page", self.page)
        return blueprint

    def asset(self) -> Response:
        body = b"" if request.method == "HEAD" else runtime_asset().read_bytes()
        return Response(body, mimetype="text/javascript", headers={"Cache-Control": "no-cache"})

    def page(self, page_path="") -> Response:
        owner = request.cookies.get(OWNER_COOKIE) or token_urlsafe(24)
        try:
            opened = asyncio.run(self.host.open_page(page_path, owner=owner))
        except PageNotFound:
            return Response("Page not found", status=404)
        except HostCapacity:
            return Response("Page capacity reached", status=503)
        response = Response(opened.html, mimetype="text/html", headers={"Cache-Control": "no-store"})
        response.set_cookie(
            OWNER_COOKIE,
            owner,
            path=self.prefix or "/",
            httponly=True,
            samesite="Lax",
        )
        return response

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
    app.extensions.setdefault("gramlot_pages", {})[integration.prefix] = integration
    return integration


__all__ = ["Pages", "mount_pages"]
