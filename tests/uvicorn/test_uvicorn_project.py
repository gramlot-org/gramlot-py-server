"""``gramlot uvicorn new`` creates the quick start project, which serves its page."""
import httpx
import pytest
from project_checks import check_document, check_files, check_main
from rpc_checks import RPC_HEADERS, envelope, rpc_source


@pytest.mark.asyncio
async def test_new_project_serves_the_page_and_its_logic(new_project, capsys, source_tags, page_id):
    folder, module = new_project("uvicorn", "app.py")
    check_files(folder, "app.py", "gramlot-py-server[uvicorn]>=0.2.3", "uvicorn app:application",
                capsys.readouterr().out)
    transport = httpx.ASGITransport(app=module.application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        document = await client.get("/")
        assert document.status_code == 200
        check_document(document.text, document.headers["content-security-policy"])
        logic = await client.get("/index.js")
        assert logic.headers["content-type"] == "text/javascript; charset=utf-8"
        assert "greeting(kwargs)" in logic.text
        main = await client.post("/gramlot/rpc", content=envelope(page_id(document.text)), headers=RPC_HEADERS)
        check_main(source_tags(rpc_source(main.text)))
