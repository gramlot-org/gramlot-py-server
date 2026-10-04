"""The Uvicorn example serves the pages of the README and the tutorial."""
import re
from pathlib import Path

import httpx
import pytest

from gramlot_py_server.uvicorn import create_application

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
PAGES = EXAMPLES / "pages"
STRICT_CSP = "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"


@pytest.mark.asyncio
async def test_quick_start_page_serves_the_bound_field_and_the_formula(load_example, source_tags, page_id):
    app = load_example("uvicorn/app.py").application
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        document = await client.get("/hello")
        assert document.status_code == 200
        assert "<title>Hello</title>" in document.text
        assert "'unsafe-eval'" in document.headers["content-security-policy"]
        main = await client.post("/gramlot/main", json={"pageId": page_id(document.text)})
        assert main.status_code == 200
        tags = source_tags(main.text)
        assert tags["input"]["value"] == "^.name"
        assert tags["input"]["live"] is True
        assert tags["dataFormula"]["formula"] == "'Hello, ' + name"
        assert tags["dataSetter"]["value"] == "Ada"


@pytest.mark.asyncio
async def test_tutorial_page_with_companion_and_stylesheet_under_the_strict_profile(source_tags, page_id):
    app = create_application(PAGES, content_security_policy=STRICT_CSP)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        document = await client.get("/greeting")
        assert document.status_code == 200
        nonce = re.search(r'nonce="([^"]+)"', document.text).group(1)
        assert document.headers["content-security-policy"] == STRICT_CSP.replace("{nonce}", nonce)
        assert '"css":["/greeting.css"]' in document.text
        assert '{"url":"/greeting_aux.js","group":null}' in document.text
        assert (await client.get("/greeting.css")).headers["content-type"] == "text/css; charset=utf-8"
        companion = await client.get("/greeting_aux.js")
        assert companion.headers["content-type"] == "text/javascript; charset=utf-8"
        assert "greet(kwargs)" in companion.text
        assert (await client.get("/greeting.py")).status_code == 404
        main = await client.post("/gramlot/main", json={"pageId": page_id(document.text)})
        tags = source_tags(main.text)
        assert tags["dataFormula"]["func"] == "greet"
        assert "formula" not in tags["dataFormula"]
