# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Native HTML integration for the Kajenn server."""

from __future__ import annotations

import re

from genro_asgi import BaseApplication
from gramlot.server import runtime_asset

from gramlot_minimal.asgi import NativeHtmlASGI


class _KajennASGI(NativeHtmlASGI):
    def __init__(self, application, *args, **kwargs):
        self.application = application
        super().__init__(*args, **kwargs)

    async def _runtime_bytes(self) -> bytes:
        if self.application.server is None:
            raise RuntimeError("Mount this application on a Genro ASGI server first")
        return await self.application.server.run_sync(runtime_asset().read_bytes)


class KajennNativeHtmlApplication(BaseApplication):
    """A mountable Genro ASGI application backed by ``gramlot.server.Host``."""

    def __init__(
        self,
        pages,
        *,
        mount: str = "page",
        code: str = "gramlot-native-html",
        page_ttl: float = 1800,
        max_pages: int = 1000,
    ) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", mount):
            raise ValueError("mount must be a single lowercase URL segment")
        super().__init__(code=code, mount=mount)
        self.native_html = _KajennASGI(
            self,
            pages,
            mount_path=f"/{mount}",
            page_ttl=page_ttl,
            max_pages=max_pages,
        )
        self.host = self.native_html.host

    async def __call__(self, scope, receive, send) -> None:
        await self.native_html(scope, receive, send)


__all__ = ["KajennNativeHtmlApplication"]
