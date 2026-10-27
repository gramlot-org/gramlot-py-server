# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""FastAPI integration for the Gramlot server protocol."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import Response

from gramlot_py_server import base
from gramlot_py_server.gallery import add_gallery
from gramlot_py_server.scaffold import add_new


class Pages(base.Adapter):
    """Own a Gramlot ``GramlotFileServer`` and its FastAPI route translations.

    The routes are included at ``mount_path``, which is also passed to
    ``open_page`` as the mount prefix of browser URLs. The prefix without the
    final slash (``/py``) answers 301 to ``/py/``: pages link each other with
    relative URLs.

    The HTTP rules, the same in every adapter, are those of ``gramlot_py_server.base``.
    """

    def mount(self, app: FastAPI) -> None:
        """Include the routes and register ``shutdown``. Every method of every URL reaches
        ``route``, which answers 405; the routes stay out of the OpenAPI schema."""
        router = APIRouter(prefix=self.mount_path)
        methods = list(self.METHODS)
        if self.mount_path:
            router.add_api_route("", self.mount_route, methods=methods, include_in_schema=False)
        router.add_api_route("/", self.route, methods=methods, include_in_schema=False)
        router.add_api_route("/{page_path:path}", self.route, methods=methods, include_in_schema=False)
        app.include_router(router)
        app.router.add_event_handler("shutdown", self.shutdown)

    async def mount_route(self, request: Request) -> Response:
        """The bare mount prefix."""
        return self.response(self.redirect(request.url.query))

    async def route(self, request: Request, page_path: str = "") -> Response:
        """Every URL below the mount prefix."""
        return self.response(await self.handle(base.Request(
            method=request.method,
            path="/" + page_path,
            body=request.body,
            query=request.url.query,
            content_type=request.headers.get("content-type", ""),
            owner=request.cookies.get(self.OWNER_COOKIE),
        )))

    @staticmethod
    def response(reply: base.Reply) -> Response:
        """The Starlette response of a ``Reply``."""
        return Response(reply.body, status_code=reply.status,
                        headers={"Content-Type": reply.content_type, **dict(reply.headers)})


class Application(FastAPI):
    """Ready-made FastAPI application serving Gramlot pages."""

    def __init__(self, pages: str | Path, *, mount_path: str = "", page_ttl: float = 1800,
                 max_pages: int = 1000, content_security_policy: str | None = None,
                 assets: dict | None = None, collections=(), **fastapi_options) -> None:
        super().__init__(**fastapi_options)
        self.gramlot_pages = mount_pages(
            self, pages, mount_path=mount_path, page_ttl=page_ttl, max_pages=max_pages,
            content_security_policy=content_security_policy, assets=assets, collections=collections,
        )


def mount_pages(app: FastAPI, pages: str | Path, **options) -> Pages:
    """Mount the bounded Gramlot page protocol on an existing FastAPI app."""

    integration = Pages(pages, **options)
    integration.mount(app)
    return integration


def serve(pages: str | Path, *, host: str = "127.0.0.1", port: int = 8000, **options) -> None:
    """Serve ``pages`` in a FastAPI ``Application`` under Uvicorn until it stops."""
    import uvicorn

    uvicorn.run(Application(pages, **options), host=host, port=port)


def commands(verbs) -> None:
    """The verbs of ``gramlot fastapi``: an entry point of ``gramlot_py_server.commands``."""
    add_new(verbs, "fastapi", start="uvicorn app:app", url="http://127.0.0.1:8000/")
    add_gallery(verbs, "fastapi", serve)


__all__ = ["Application", "Pages", "mount_pages"]
