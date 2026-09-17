# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Optional, invocation-scoped legacy GnrApp access for Genro ASGI pages.

This host adapter owns execution/cleanup, not SQL or shared database contracts.
An initialized GnrApp is supplied by the caller; importing this module needs no gnr.
"""
import inspect

from gramlot.page import WebPage
from gramlot.transport import TYTX_FORMAT, from_tytx, to_tytx

from .application import GramlotApplication, PageCollection


class GenropyPage(WebPage):
    """Use self.db only during a synchronous Source or Data service."""

    @property
    def db(self):
        if not getattr(self, '_legacy_active', False):
            raise RuntimeError('Legacy database access requires a synchronous page service')
        if self._legacy_db is None:
            # Record it before initialization so partial failures still clean up.
            self._legacy_db = self._legacy_application.db
            self._legacy_db.clearCurrentEnv()
            self._legacy_db.updateEnv(pagename=self._legacy_context.page_name,
                                      gramlot_method=self._legacy_context.method_name)
        return self._legacy_db


class GenropyPageCollection(PageCollection):
    def __init__(self, *args, genropy_application, **kwargs):
        db = getattr(genropy_application, 'db', None)
        if db is None or any(not callable(getattr(db, name, None)) for name in
                             ('clearCurrentEnv', 'updateEnv', 'closeConnection')):
            raise TypeError('genropy_application must expose an initialized legacy GnrApp database')
        self.genropy_application = genropy_application
        super().__init__(*args, **kwargs)

    def prepare_page(self, page, context):
        if isinstance(page, GenropyPage):
            page._legacy_application = self.genropy_application
            page._legacy_context = context
            page._legacy_db = None

    def invoke_sync(self, page, method, args, kwargs):
        if not isinstance(page, GenropyPage):
            return super().invoke_sync(page, method, args, kwargs)
        page._legacy_active = True
        try:
            result = method(*args, **kwargs)
            if inspect.isawaitable(result):
                close = getattr(result, 'close', None)
                if close is not None:
                    close()
                raise TypeError('Synchronous legacy services must not return awaitables')
            # Fully encode/decode before connection cleanup; only portable TYTX values
            # leave this worker. Pages explicitly materialize legacy query/Bag values.
            return from_tytx(to_tytx(result, TYTX_FORMAT), transport=TYTX_FORMAT)
        finally:
            page._legacy_active = False
            if page._legacy_db is not None:
                try:
                    page._legacy_db.closeConnection()
                finally:
                    page._legacy_db.clearCurrentEnv()
                    page._legacy_db = None


class GenropyApplication(GramlotApplication):
    """Genro ASGI host with optional legacy database lifecycle integration.

    No implicit commit, no shutdown of the caller-owned GnrApp, and no inferred
    GenroPy permissions. Pages own queries and explicit transaction decisions.
    """

    registry_class = GenropyPageCollection
