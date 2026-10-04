"""The Flask example serves the pages of the README and the tutorial."""


def test_example_serves_the_quick_start_page_and_the_companions(load_example, source_tags, page_id):
    client = load_example("flask/app.py").app.test_client()
    document = client.get("/hello")
    assert document.status_code == 200
    assert "<title>Hello</title>" in document.text
    assert "'unsafe-eval'" in document.headers["Content-Security-Policy"]
    main = client.post("/gramlot/main", json={"pageId": page_id(document.text)})
    tags = source_tags(main.text)
    assert tags["input"]["value"] == "^.name"
    assert tags["dataFormula"]["formula"] == "'Hello, ' + name"
    assert client.get("/greeting").status_code == 200
    assert client.get("/greeting.css").headers["Content-Type"] == "text/css; charset=utf-8"
    assert "greet(kwargs)" in client.get("/greeting_aux.js").text
