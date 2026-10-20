# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Flask integration for the Gramlot server protocol."""

from __future__ import annotations

import asyncio
from pathlib import Path

from flask import Blueprint, Flask, Response, request

from gramlot_py_server import base
from gramlot_py_server.gallery import add_gallery
from gramlot_py_server.scaffold import add_new


class Pages(base.Adapter):
    """Own a Gramlot ``GramlotFileServer`` and its WSGI route translations.

    The blueprint is registered at ``mount_path``, which is also passed to
    ``open_page`` as the mount prefix of browser URLs. The prefix without the
    final slash (``/py``) answers 301 to ``/py/``: pages link each other with
    relative URLs.

    WSGI has no shutdown signal: the registered pages are forgotten when the
    interpreter exits or the ``Pages`` is collected (``close_at_exit``).
    The HTTP rules, the same in every adapter, are those of ``gramlot_py_server.base``.
    """

    def __init__(self, pages: str | Path, **options) -> None:
        super().__init__(pages, **options)
        self.finalizer = self.close_at_exit()

    def blueprint(self) -> Blueprint:
        """The blueprint of the pages: every method of every URL reaches ``view``, which answers 405."""
        name = "gramlot_pages_" + (self.mount_path.strip("/") or "root").replace("/", "_")
        blueprint = Blueprint(name, __name__, url_prefix=self.mount_path or None)
        methods = list(self.METHODS)
        if self.mount_path:
            blueprint.add_url_rule("", "mount", self.mount_view, methods=methods,
                                   provide_automatic_options=False, strict_slashes=False)
        blueprint.add_url_rule("/", "index", self.view, methods=methods,
                               provide_automatic_options=False, defaults={"page_path": ""})
        blueprint.add_url_rule("/<path:page_path>", "page", self.view, methods=methods,
                               provide_automatic_options=False)
        return blueprint

    def mount_view(self) -> Response:
        """The bare mount prefix."""
        return self.response(self.redirect(request.query_string.decode("latin-1")))

    def view(self, page_path: str = "") -> Response:
        """Every URL below the mount prefix."""
        return self.response(asyncio.run(self.handle(base.Request(
            method=request.method,
            path="/" + page_path,
            body=base.stored(request.get_data(cache=False)),
            query=request.query_string.decode("latin-1"),
            content_type=request.headers.get("Content-Type", ""),
            owner=request.cookies.get(self.OWNER_COOKIE),
        ))))

    @staticmethod
    def response(reply: base.Reply) -> Response:
        """The Flask response of a ``Reply``."""
        return Response(reply.body, status=reply.status, content_type=reply.content_type,
                        headers=list(reply.headers))


def mount_pages(app, pages: str | Path, **options) -> Pages:
    """Mount the bounded Gramlot page protocol on an existing Flask app."""

    integration = Pages(pages, **options)
    app.register_blueprint(integration.blueprint())
    app.extensions.setdefault("gramlot_pages", {})[integration.mount_path] = integration
    return integration


def serve(pages: str | Path, *, host: str = "127.0.0.1", port: int = 8000, **options) -> None:
    """Serve ``pages`` in a Flask app with the Flask development server until it stops."""
    app = Flask(__name__)
    mount_pages(app, pages, **options)
    app.run(host=host, port=port)


def commands(verbs) -> None:
    """The verbs of ``gramlot flask``: an entry point of ``gramlot_py_server.commands``."""
    add_new(verbs, "flask", start="flask --app app run --port 8000", url="http://127.0.0.1:8000/")
    add_gallery(verbs, "flask", serve)


__all__ = ["Pages", "mount_pages"]
