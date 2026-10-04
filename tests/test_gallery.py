"""The staging of the gallery and the catalogues of the five environments."""
import json
import sys

import pytest
from gramlot_examples import build_gallery

from gramlot_py_server import cli
from gramlot_py_server.gallery import CATALOGS, environment_catalogs, examples_package, stage
from gramlot_py_server.scaffold import TEMPLATES

ENVIRONMENTS = {
    "uvicorn": ["app.py"],
    "django": ["settings.py", "urls.py"],
    "flask": ["app.py"],
    "fastapi": ["app.py"],
    "kajenn": ["config.py"],
}


@pytest.mark.parametrize("environment", sorted(ENVIRONMENTS))
def test_catalogue_of_each_environment_is_the_quick_start(environment):
    catalogs = environment_catalogs(environment)
    assert catalogs == [(CATALOGS / environment / "catalog.json", CATALOGS / environment / "pages")]
    families = build_gallery(catalogs)["families"]
    family = families[-1]
    assert family["key"] == f"{environment}_pages"
    assert [example["key"] for example in family["examples"]] == [f"{environment}-01"]
    folder = family["path"]
    assert (folder / "01_quick_start.py").read_text() == (TEMPLATES / "pages" / "index.py").read_text()
    assert (folder / "01_quick_start.js").read_text() == (TEMPLATES / "pages" / "index.js").read_text()
    readme = (folder / "01_quick_start.md").read_text()
    for name in ENVIRONMENTS[environment]:
        assert f"```python\n{(TEMPLATES / environment / name).read_text()}```" in readme
    assert f"gramlot {environment} new my-site" in readme


@pytest.mark.parametrize("prefix", ["/py", ""])
def test_stage_writes_one_page_per_route(tmp_path, prefix):
    assets = stage(tmp_path, environment_catalogs("uvicorn"), prefix)
    index = (tmp_path / "index.py").read_text()
    assert f"logoUrl = '{prefix}/assets/branding/gramlot-logo-dark.svg'" in index
    assert f"galleryScript = '{prefix}/gallery/dist/gallery.js'" in index
    assert str(CATALOGS / "uvicorn" / "catalog.json") in index
    assert f"root.script(src='{prefix}/gallery/dist/frame.js')" in (tmp_path / "e01.py").read_text()
    stub = (tmp_path / "c03_aux.js").read_text()
    assert stub == f'export {{Logic}} from "{prefix}/pages/controllers/03_named_logic.js";\n'
    assert assets["/pages/controllers/03_named_logic.js"]["type"] == "text/javascript; charset=utf-8"
    assert (tmp_path / "uvicorn-01_aux.js").read_text() == (
        f'export {{Logic}} from "{prefix}/pages/uvicorn_pages/01_quick_start.js";\n')
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
