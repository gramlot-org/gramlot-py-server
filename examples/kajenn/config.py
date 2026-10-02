"""Kajenn site of the example: ``kajenn serve config.py``, pages under ``/pages``."""
from pathlib import Path

from kajenn.config.templates import DefaultConfiguration

from gramlot_py_server.kajenn import Application

PAGES = Path(__file__).resolve().parents[1] / "pages"


class Site(DefaultConfiguration):
    def applications_section(self, cfg):
        cfg.applications().application(
            code="pages",
            mount="pages",
            app_class=Application,
            pages=PAGES,
            content_security_policy=(
                "script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'"
            ),
        ).request(body="raw")
