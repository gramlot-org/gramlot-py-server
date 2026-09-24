# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Experimental Gramlot host integration for Genro ASGI."""

__all__ = [
    "KajennNativeHtmlApplication",
    "NativeHtmlASGI",
    "create_asgi_application",
]


def __getattr__(name):
    if name == "GramlotApplication":
        from .application import GramlotApplication

        return GramlotApplication
    if name in {"NativeHtmlASGI", "create_asgi_application"}:
        from .asgi import NativeHtmlASGI, create_asgi_application

        return {"NativeHtmlASGI": NativeHtmlASGI,
                "create_asgi_application": create_asgi_application}[name]
    if name == "KajennNativeHtmlApplication":
        from .native_html import KajennNativeHtmlApplication

        return KajennNativeHtmlApplication
    raise AttributeError(name)
