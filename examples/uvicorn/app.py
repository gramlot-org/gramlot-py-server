"""Serve the example pages with Uvicorn: ``uvicorn app:application``."""
from pathlib import Path

from gramlot_py_server.uvicorn import create_application

PAGES = Path(__file__).resolve().parents[1] / "pages"

application = create_application(
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'",
)
