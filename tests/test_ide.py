"""The IDE uses ordinary authenticated page RPC across all Python hosts."""
import json
import re
from http.cookiejar import CookieJar
from urllib.request import HTTPCookieProcessor, Request, build_opener

import pytest
from genro_tytx import from_tytx
from gramlot.server import GramlotFileServer
from gramlot_py_server.gallery import stage_tools
from gramlot_py_server.ide import stage_ide
from conformance_checks import served
from rpc_checks import envelope


@pytest.mark.parametrize("framework", ["uvicorn", "django", "flask", "fastapi", "kajenn"])
@pytest.mark.parametrize("remote_edit", [False, True])
def test_document_rpc_enforces_root_and_remote_edit(tmp_path, framework, remote_edit):
    pages = tmp_path / "pages"
    documents = tmp_path / "documents"
    documents.mkdir()
    sample = documents / "sample.py"
    sample.write_text("value = 1\n")
    stage_ide(pages, roots=[documents], remote_edit=remote_edit)
    with served(framework, pages, "/demo", None) as url:
        client = build_opener(HTTPCookieProcessor(CookieJar()))
        html = client.open(url + "/").read().decode()
        bootstrap = json.loads(re.search(r"new PageBootstrap\((.+)\)\.run", html)[1])
        page_id = bootstrap["config"]["pageId"]
        def call(method, **params):
            request = Request(url + "/gramlot/rpc", data=envelope(page_id, method, params, "data").encode(),
                              headers={"Content-Type": "application/json"})
            return from_tytx(client.open(request).read().decode())
        document = call("document_read", root=str(documents), path="sample.py")["value"]
        assert document["writable"] is remote_edit
        assert call("workspace_open", root=str(tmp_path))["error"]["name"] == "PermissionError"
        assert "error" in call("document_read", root=str(documents), path="../outside.py")
        result = call("document_save", root=str(documents), path="sample.py",
                      content="value = 2\n", revision=document["revision"])
        if remote_edit:
            assert "error" not in result
            assert sample.read_text() == "value = 2\n"
            assert "error" in call("document_save", root=str(documents), path="sample.py",
                                   content="value = 3\n", revision=document["revision"])
        else:
            assert result["error"]["name"] == "PermissionError"
            assert sample.read_text() == "value = 1\n"
            assert call("document_create", root=str(documents), path="new.txt", content="draft")["error"]["name"] == "PermissionError"
        assert "error" in call("document_render_typst", content="raise RuntimeError('must not execute')")


def test_gallery_workspace_is_disposable_and_not_a_page_root(tmp_path):
    catalog, sources = stage_tools(tmp_path)
    page = GramlotFileServer(sources / "07-tools").resolve_page("index")()
    root = tmp_path / ".gallery-documents"
    assert page.filesystem_roots == (str(root.resolve()),)
    assert not page.remote_edit
    assert "notes.py" in [node.attr["caption"] for node in page.directory_tree(str(root)).nodes]
    assert len(json.loads(catalog.read_text())["families"]) == 1
    assert list(GramlotFileServer(root.parent).iter_page_classes()) == [], "sample Python documents must not become executable pages"


def test_ide_staging_rejects_invalid_roots_and_existing_pages(tmp_path):
    pages = tmp_path / "pages"
    with pytest.raises(ValueError, match="at least one"):
        stage_ide(pages, roots=[])
    documents = tmp_path / "docs"
    documents.mkdir()
    stage_ide(pages, roots=[documents])
    with pytest.raises(FileExistsError):
        stage_ide(pages, roots=[documents])
