# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Uvicorn Python/ASGI integration for Gramlot."""

from .asgi import NativeHtmlASGI, create_asgi_application

__all__ = ["NativeHtmlASGI", "create_asgi_application"]
