"""The Kajenn example serves the pages of the README and the tutorial."""
import httpx
import pytest
from kajenn import AsgiServer


@pytest.mark.asyncio
async def test_example_serves_the_quick_start_page_and_the_companions(load_example, source_tags, page_id):
    server = AsgiServer(config=load_example("kajenn/config.py").Site)
    transport = httpx.ASGITransport(app=server)
    async with httpx.AsyncClient(transport=transport, base_url="http://test/pages") as client:
        document = await client.get("/hello")
        assert document.status_code == 200
        assert "<title>Hello</title>" in document.text
        assert "'unsafe-eval'" in document.headers["content-security-policy"]
        assert '"mainUrl":"/pages/gramlot/main"' in document.text
        main = await client.post("/gramlot/main", json={"pageId": page_id(document.text)})
        tags = source_tags(main.text)
        assert tags["input"]["value"] == "^.name"
        assert tags["dataFormula"]["formula"] == "'Hello, ' + name"
        assert (await client.get("/greeting")).status_code == 200
        css = await client.get("/greeting.css")
        assert css.headers["content-type"] == "text/css; charset=utf-8"
        assert "greet(kwargs)" in (await client.get("/greeting_aux.js")).text
