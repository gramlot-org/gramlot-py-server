# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Exercise optional lazy editors with the same installed browser runtime."""
from gramlot_django import DjangoPage


class Page(DjangoPage):
    def main(self, root):
        root.h1('Local editors')
        root.gramlotIde(
            id='html-editor', filename='sample.html', language='html',
            datapath='html_editor', height='400px', content='<p>Hello HTML</p>',
        )
        root.gramlotIde(
            id='markdown-editor', filename='sample.md', language='markdown',
            datapath='markdown_editor', height='400px', content='# Hello Markdown',
        )
