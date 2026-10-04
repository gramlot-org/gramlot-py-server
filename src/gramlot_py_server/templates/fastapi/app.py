"""Serve the pages inside a FastAPI app: ``uvicorn app:app``."""
from pathlib import Path

from fastapi import FastAPI

from gramlot_py_server.fastapi import mount_pages

PAGES = Path(__file__).resolve().parent / "pages"

app = FastAPI()
mount_pages(
    app,
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)
