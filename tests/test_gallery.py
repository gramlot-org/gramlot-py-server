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
    assert f"root.script(src='{prefix}/gallery/dist/frame.js')" in (tmp_path / "e01.py").read_text()
    stub = (tmp_path / "c03_aux.js").read_text()
    assert stub == f'export {{Logic}} from "{prefix}/pages/controllers/03_named_logic.js";\n'
    assert assets["/pages/controllers/03_named_logic.js"]["type"] == "text/javascript; charset=utf-8"
    assert not (tmp_path / "uvicorn-01.py").exists()
    assert not (tmp_path / "uvicorn-01_aux.js").exists()
    assert assets["/pages/controllers/03_named_logic.py"]["type"] == "text/plain"
    routes = build_gallery(environment_catalogs("uvicorn"))["routes"]
    for key, route in routes.items():
        assert (tmp_path / f"{key}.py").is_file()
        assert (tmp_path / f"{key}.css").is_file() == (route["stylesheet"] is not None)
        assert (tmp_path / f"{key}_aux.js").is_file() == (route["logic"] is not None)


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
        served.update(options, staged=sorted(path.name for path in pages.iterdir())[:3])

    parser = cli.argparse.ArgumentParser()
    verbs = parser.add_subparsers(dest="verb", required=True)
    from gramlot_py_server.gallery import add_gallery

    add_gallery(verbs, "uvicorn", serve)
    options = parser.parse_args(["gallery", "--port", "9001", "--mount", "py/",
                                 "--catalog", str(catalog), str(tmp_path)])
    assert options.run(options) == 0
    assert served["host"] == "127.0.0.1" and served["port"] == 9001
    assert served["mount_path"] == "/py"
    assert served["assets"]["/gallery/dist/gallery.js"]["type"] == "application/javascript"
    defaults = parser.parse_args(["gallery"])
    assert (defaults.host, defaults.port, defaults.mount, defaults.catalog) == ("127.0.0.1", 8080, "", [])
