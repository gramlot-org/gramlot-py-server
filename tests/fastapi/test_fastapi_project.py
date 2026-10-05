"""``gramlot fastapi new`` creates the quick start project, which serves its page."""
from fastapi.testclient import TestClient
from project_checks import check_document, check_files, check_main


def test_new_project_serves_the_page_and_its_logic(new_project, capsys, source_tags, page_id):
    folder, module = new_project("fastapi", "app.py")
    check_files(folder, "app.py", "gramlot-py-server[fastapi,uvicorn]>=0.2.3", "uvicorn app:app",
                capsys.readouterr().out)
    with TestClient(module.app) as client:
        document = client.get("/")
        assert document.status_code == 200
        check_document(document.text, document.headers["content-security-policy"])
        logic = client.get("/index.js")
        assert logic.headers["content-type"] == "text/javascript; charset=utf-8"
        assert "greeting(kwargs)" in logic.text
        main = client.post("/gramlot/main", json={"pageId": page_id(document.text)})
        check_main(source_tags(main.text))
