"""The Uvicorn example of the tutorial serves its pages."""
import re
from pathlib import Path

import httpx
import pytest

from gramlot_py_server.uvicorn import create_application
from rpc_checks import RPC_HEADERS, envelope, rpc_source

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
PAGES = EXAMPLES / "pages"
STRICT_CSP = "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"


@pytest.mark.asyncio
async def test_tutorial_application_serves_the_bound_field_and_the_formula(load_example, source_tags, page_id):
    app = load_example("uvicorn/app.py").application
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        document = await client.get("/hello")
        assert document.status_code == 200
        assert "<title>Hello</title>" in document.text
        assert "'unsafe-eval'" in document.headers["content-security-policy"]
        main = await client.post("/gramlot/rpc", content=envelope(page_id(document.text)), headers=RPC_HEADERS)
        assert main.status_code == 200
        tags = source_tags(rpc_source(main.text))
        assert tags["input"]["value"] == "^.name"
        assert tags["input"]["live"] is True
        assert tags["dataFormula"]["formula"] == "'Hello, ' + name"
        assert tags["dataSetter"]["value"] == "Ada"


@pytest.mark.asyncio
async def test_tutorial_page_with_page_module_and_stylesheet_under_the_strict_profile(source_tags, page_id):
    app = create_application(PAGES, content_security_policy=STRICT_CSP)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        document = await client.get("/greeting")
        assert document.status_code == 200
        nonce = re.search(r'nonce="([^"]+)"', document.text).group(1)
        assert document.headers["content-security-policy"] == STRICT_CSP.replace("{nonce}", nonce)
        assert '"css":["/greeting.css"]' in document.text
        assert '{"url":"/greeting.js","group":null}' in document.text
        assert (await client.get("/greeting.css")).headers["content-type"] == "text/css; charset=utf-8"
        companion = await client.get("/greeting.js")
        assert companion.headers["content-type"] == "text/javascript; charset=utf-8"
        assert "greet(kwargs)" in companion.text
        assert (await client.get("/greeting.py")).status_code == 404
        main = await client.post("/gramlot/rpc", content=envelope(page_id(document.text)), headers=RPC_HEADERS)
        tags = source_tags(rpc_source(main.text))
        assert tags["dataFormula"]["func"] == "greet"
        assert "formula" not in tags["dataFormula"]
