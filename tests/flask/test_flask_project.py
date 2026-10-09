"""``gramlot flask new`` creates the quick start project, which serves its page."""
from project_checks import check_document, check_files, check_main
from rpc_checks import envelope, rpc_source


def test_new_project_serves_the_page_and_its_logic(new_project, capsys, source_tags, page_id):
    folder, module = new_project("flask", "app.py")
    check_files(folder, "app.py", "gramlot-py-server[flask]>=0.2.3", "flask --app app run --port 8000",
                capsys.readouterr().out)
    client = module.app.test_client()
    document = client.get("/")
    assert document.status_code == 200
    check_document(document.text, document.headers["Content-Security-Policy"])
    logic = client.get("/index.js")
    assert logic.headers["Content-Type"] == "text/javascript; charset=utf-8"
    assert "greeting(kwargs)" in logic.text
    main = client.post("/gramlot/rpc", data=envelope(page_id(document.text)), content_type="application/json")
    check_main(source_tags(rpc_source(main.text)))
