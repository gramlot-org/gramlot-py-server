"""Serve the example pages inside a FastAPI app: ``fastapi dev app.py`` or ``uvicorn app:app``."""
from pathlib import Path

from fastapi import FastAPI

from gramlot_py_server.fastapi import mount_pages

PAGES = Path(__file__).resolve().parents[1] / "pages"

app = FastAPI()
mount_pages(
    app,
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'",
)
