"""The FastAPI example serves the pages of the README and the tutorial."""
from fastapi.testclient import TestClient


def test_example_serves_the_quick_start_page_and_the_companions(load_example, source_tags, page_id):
    with TestClient(load_example("fastapi/app.py").app) as client:
        document = client.get("/hello")
        assert document.status_code == 200
        assert "<title>Hello</title>" in document.text
        assert "'unsafe-eval'" in document.headers["content-security-policy"]
        main = client.post("/gramlot/main", json={"pageId": page_id(document.text)})
        tags = source_tags(main.text)
        assert tags["input"]["value"] == "^.name"
        assert tags["dataFormula"]["formula"] == "'Hello, ' + name"
        assert client.get("/greeting").status_code == 200
        assert client.get("/greeting.css").headers["content-type"] == "text/css; charset=utf-8"
        assert "greet(kwargs)" in client.get("/greeting_aux.js").text
