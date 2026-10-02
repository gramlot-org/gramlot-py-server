# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Explore live Data and Source through a plain FastAPI-hosted page."""
from gramlot.page import WebPage


class Page(WebPage):
    title = "FastAPI inspector"

    def main(self, root):
        root.data("message", "Hello from FastAPI")
        pane = root.div(padding="24px")
        pane.h1("Gramlot + FastAPI")
        pane.p("Open the inspector to explore Data and Source.")
        pane.textBox(value="^message", lbl="Message")
        pane.div("^message", margin_top="16px", font_size="24px")
