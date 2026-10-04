"""Serve the pages inside a Flask app: ``flask --app app run --port 8000``."""
from pathlib import Path

from flask import Flask

from gramlot_py_server.flask import mount_pages

PAGES = Path(__file__).resolve().parent / "pages"

app = Flask(__name__)
mount_pages(
    app,
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)
