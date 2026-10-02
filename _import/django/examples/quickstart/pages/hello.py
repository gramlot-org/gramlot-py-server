# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Python-authored binding, server RPC and remote content in a normal Django project."""
from gramlot.page import endpoint, source
from gramlot_django import DjangoPage


class Page(DjangoPage):
    example_view = True

    def main(self, root):
        root.data('name', 'Ada')
        root.h1('Hello Gramlot')
        root.textBox(value='^name', lbl='Name', live=True)
        root.p('^name', id='bound-name')
        root.dataRpc('greeting', self.greet, name='^name', _on_start=True, _delay=1)
        root.p('^greeting', id='server-greeting')
        root.contentPane().remote(self.note, name='^name')

    @endpoint
    def greet(self, name: str):
        return f'Hello, {name}!'

    @source
    def note(self, root, name: str):
        root.p(f'Built in Python for {name}.', id='remote-note')
