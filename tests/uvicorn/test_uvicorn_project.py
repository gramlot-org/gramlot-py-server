"""``gramlot uvicorn new`` creates the quick start project, which serves its page."""
import httpx
import pytest
from project_checks import check_document, check_files, check_main


@pytest.mark.asyncio
async def test_new_project_serves_the_page_and_its_logic(new_project, capsys, source_tags, page_id):
    folder, module = new_project("uvicorn", "app.py")
    check_files(folder, "app.py", "gramlot-py-server[uvicorn]>=0.2.2", "uvicorn app:application",
                capsys.readouterr().out)
    transport = httpx.ASGITransport(app=module.application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        document = await client.get("/")
        assert document.status_code == 200
        check_document(document.text, document.headers["content-security-policy"])
        logic = await client.get("/index.js")
        assert logic.headers["content-type"] == "text/javascript; charset=utf-8"
        assert "greet(kwargs)" in logic.text
        main = await client.post("/gramlot/main", json={"pageId": page_id(document.text)})
        check_main(source_tags(main.text))
