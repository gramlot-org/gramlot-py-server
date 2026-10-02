# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""A host-independent page using the experimental Gramlot database interface."""
from gramlot.database import DbPageMixin
from gramlot.page import WebPage


class Page(DbPageMixin, WebPage):
    title = 'FastAPI + SQLAlchemy'

    def main(self, root):
        pane = root.div(padding='24px', max_width='560px')
        pane.h1('FastAPI + SQLAlchemy')
        pane.p('Read-only SQLite demo: try Alice, Bruno or Carla.')
        root.data('customer', 1)
        root.data('caption', None)
        pane.dbSelect(dbtable='customers', value='^customer',
                      selectedCaption='^caption', lbl='Customer', width='100%')
        pane.div('^customer', mask='Selected identity: %s')
        pane.div('^caption', mask='Selected name: %s')
