# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Host Gramlot applications with FastAPI."""

__all__ = [
    "NativeHtmlApplication",
    "NativeHtmlPages",
    "mount_native_html",
]


def __getattr__(name):
    if name in {"NativeHtmlApplication", "NativeHtmlPages", "mount_native_html"}:
        from .native_html import NativeHtmlApplication, NativeHtmlPages, mount_native_html

        return {
            "NativeHtmlApplication": NativeHtmlApplication,
            "NativeHtmlPages": NativeHtmlPages,
            "mount_native_html": mount_native_html,
        }[name]
    if name in {"GramlotApplication", "PageCollection", "mount_gramlot"}:
        from .application import GramlotApplication, PageCollection, mount_gramlot

        return {
            "GramlotApplication": GramlotApplication,
            "PageCollection": PageCollection,
            "mount_gramlot": mount_gramlot,
        }[name]
    raise AttributeError(name)
