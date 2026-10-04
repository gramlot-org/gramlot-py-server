"""``gramlot flask new`` creates the quick start project, which serves its page."""
from project_checks import check_document, check_files, check_main


def test_new_project_serves_the_page_and_its_logic(new_project, capsys, source_tags, page_id):
    folder, module = new_project("flask", "app.py")
    check_files(folder, "app.py", "gramlot-py-server[flask]>=0.2.2", "flask --app app run",
                capsys.readouterr().out)
    client = module.app.test_client()
    document = client.get("/")
    assert document.status_code == 200
    check_document(document.text, document.headers["Content-Security-Policy"])
    logic = client.get("/index.js")
    assert logic.headers["Content-Type"] == "text/javascript; charset=utf-8"
    assert "greeting(kwargs)" in logic.text
    main = client.post("/gramlot/main", json={"pageId": page_id(document.text)})
    check_main(source_tags(main.text))
