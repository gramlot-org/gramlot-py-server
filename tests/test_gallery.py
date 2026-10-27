"""The staging of the gallery and the catalogues of the five environments."""
import json
import sys

import pytest
from gramlot_examples import build_gallery

from gramlot_py_server import cli
from gramlot_py_server.gallery import environment_catalogs, examples_package, stage

ENVIRONMENTS = {
    "uvicorn": ["app.py"],
    "django": ["settings.py", "urls.py"],
    "flask": ["app.py"],
    "fastapi": ["app.py"],
    "kajenn": ["config.py"],
}


@pytest.mark.parametrize("environment", sorted(ENVIRONMENTS))
def test_environment_gallery_contains_common_examples_without_quick_start(environment):
    catalogs = environment_catalogs(environment)
    assert catalogs == []
    gallery = build_gallery(catalogs)
    assert gallery["routes"].keys() == build_gallery()["routes"].keys()
    assert f"{environment}-01" not in gallery["routes"]
    assert all(example["title"] != "Quick start"
               for family in gallery["families"] for example in family["examples"])


@pytest.mark.parametrize("prefix", ["/py", ""])
def test_stage_writes_one_page_per_route(tmp_path, prefix):
    assets = stage(tmp_path, environment_catalogs("uvicorn"), prefix)
    index = (tmp_path / "index.py").read_text()
    assert f"logoUrl = '{prefix}/assets/branding/gramlot-logo-dark.svg'" in index
    assert f"galleryScript = '{prefix}/gallery/dist/gallery.js'" in index
    assert "catalogs = []" in index
    assert (tmp_path / "index_aux.js").read_text() == f'export {{Logic}} from "{prefix}/gallery/dist/gallery.js";\n'
    routes = build_gallery(environment_catalogs("uvicorn"))["routes"]
    first = tmp_path / (routes["e01"]["url"] + ".py")
    assert f"root.script(src='{prefix}/gallery/dist/frame.js')" in first.read_text()
    assert not (tmp_path / "e01.py").exists()
    for key, route in routes.items():
        if key == "index":
            continue
        key = route["url"]
        assert (tmp_path / f"{key}.py").is_file()
        assert (tmp_path / f"{key}.css").is_file() == (route["stylesheet"] is not None)
        assert (tmp_path / f"{key}_aux.js").is_file() == (route["logic"] is not None)
        if route["logic"] is not None:
            url = next(url for url, asset in assets.items() if asset["file"] == route["logic"])
            assert assets[url]["type"] == "text/javascript; charset=utf-8"
            assert (tmp_path / f"{key}_aux.js").read_text() == f'export {{Logic}} from "{prefix}{url}";\n'


def test_gallery_without_gramlot_examples_names_the_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "gramlot_examples", None)
    with pytest.raises(SystemExit) as raised:
        examples_package()
    assert str(raised.value) == (
        'The gallery needs gramlot-examples: python -m pip install "gramlot-py-server[gallery]"')


def test_gallery_options(tmp_path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"environment": "extra", "families": []}))
    served = {}

    def serve(pages, **options):
        served.update(options, staged=sorted(path.name for path in pages.iterdir())[:3], index=(pages / "index.py").read_text())

    parser = cli.argparse.ArgumentParser()
    verbs = parser.add_subparsers(dest="verb", required=True)
    from gramlot_py_server.gallery import add_gallery

    add_gallery(verbs, "uvicorn", serve)
    options = parser.parse_args(["gallery", "--websocket", "--port", "9001", "--mount", "py/",
                                 "--catalog", str(catalog), str(tmp_path), "--serverless-download", "/downloads/gallery.zip"])
    assert options.run(options) == 0
    assert served["host"] == "127.0.0.1" and served["port"] == 9001
    assert served["mount_path"] == "/py"
    assert served["websocket"] is True
    assert "serverless_download_url = '/downloads/gallery.zip'" in served["index"]
    assert served["assets"]["/gallery/dist/gallery.js"]["type"] == "application/javascript"
    defaults = parser.parse_args(["gallery"])
    assert defaults.websocket is False
    assert (defaults.host, defaults.port, defaults.mount, defaults.catalog) == ("127.0.0.1", 8080, "", [])


@pytest.mark.asyncio
async def test_staged_page_keeps_its_server_recipe(tmp_path):
    from gramlot.server import GramlotFileServer
    catalog = tmp_path / "catalog.json"
    pages = tmp_path / "original"
    (pages / "stores").mkdir(parents=True)
    (pages / "stores/01_example.py").write_text('''from gramlot import Page as BasePage, PageStore as BaseStore
class Page(BasePage):
    def main(self, root):
        root.div().dataBinder("client", "record")
class PageStore(BaseStore):
    def main(self, root):
        self.data.set_item("record", "initial")
        root.dataController(func="receive", subscribe_load=True)
    def receive(self, node, value):
        self.data.set_item("record", value)
''')
    catalog.write_text(json.dumps({"environment": "stores", "families": [{
        "key": "stores-family", "folder": "stores", "title": "Stores", "examples": [{
            "key": "stores-01", "folder": "01_example", "title": "Example",
            "description": "Example", "explanation": "Example"}]}]}))
    staged = tmp_path / "staged"
    staged.mkdir()
    stage(staged, [(catalog, pages)], "")
    server = GramlotFileServer(staged, css_theme=False)
    try:
        opened = await server.open_page("/pages/stores/01_example", owner="alice")
        store = server.page_store(opened.page_id, owner="alice")
        assert store.data.get_item("record") == "initial"
        store.publish("load", {"value": "loaded"})
        assert store.data.get_item("record") == "loaded"
    finally:
        server.close_all()
