"""The example pages of the README and the tutorial run on the adapter."""
import re
from pathlib import Path

import httpx
import pytest
from genro_tytx import from_tytx

from gramlot_uvicorn import create_asgi_application

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "tests" / "pages"
STRICT_CSP = "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"


def nodes(source):
    """Return ``(tag, attributes)`` of every node of a Source document, depth first."""
    found = []

    def walk(bag):
        for node in bag.nodes:
            found.append((node.label.split("_")[0], dict(node.attr)))
            if hasattr(node.value, "nodes"):
                walk(node.value)

    walk(from_tytx(source))
    return found


def test_readme_quick_start_page_is_the_tested_page():
    readme = (ROOT / "README.md").read_text()
    blocks = re.findall(r"```python\n(.*?)```", readme, re.S)
    assert blocks, "README has no Python block"
    assert blocks[0] == (PAGES / "hello.py").read_text()


@pytest.mark.asyncio
async def test_quick_start_page_serves_the_bound_field_and_the_formula():
    app = create_asgi_application(PAGES)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        document = await client.get("/hello")
        assert document.status_code == 200
        assert "<title>Hello</title>" in document.text
        page_id = re.search(r'"pageId":"([0-9a-f]+)"', document.text).group(1)
        main = await client.post("/gramlot/main", json={"pageId": page_id})
        assert main.status_code == 200
        tags = {tag: attrs for tag, attrs in nodes(main.text)}
        assert tags["input"]["value"] == "^.name"
        assert tags["input"]["live"] is True
        assert tags["dataFormula"]["formula"] == "'Hello, ' + name"
        assert tags["dataSetter"]["value"] == "Ada"


@pytest.mark.asyncio
async def test_tutorial_page_with_companion_and_stylesheet_under_the_strict_profile():
    app = create_asgi_application(PAGES, content_security_policy=STRICT_CSP)
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
        page_id = re.search(r'"pageId":"([0-9a-f]+)"', document.text).group(1)
        main = await client.post("/gramlot/main", json={"pageId": page_id})
        tags = {tag: attrs for tag, attrs in nodes(main.text)}
        assert tags["dataFormula"]["func"] == "greet"
        assert "formula" not in tags["dataFormula"]
