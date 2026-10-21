"""The staging of the gallery and the catalogues of the five environments."""
import json
import shutil
import subprocess
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
    assert f'{prefix}/gallery/dist/gallery.js' in (tmp_path / "index_aux.js").read_text()
    assert "catalogs = []" in index
    assert f"root.script(src='{prefix}/gallery/dist/frame.js')" in (tmp_path / "pages/01-html_elements/01-html_basics/01-hello_world.py").read_text()
    stub = (tmp_path / "pages/03-controllers/01-logic/03-named_logic_aux.js").read_text()
    assert stub == f'export * from "{prefix}/pages/03-controllers/01-logic/03-named_logic.js";\n'
    assert assets["/pages/03-controllers/01-logic/03-named_logic.js"]["type"] == "text/javascript; charset=utf-8"
    assert not (tmp_path / "uvicorn-01.py").exists()
    assert not (tmp_path / "uvicorn-01_aux.js").exists()
    assert assets["/pages/03-controllers/01-logic/03-named_logic.py"]["type"] == "text/plain"
    routes = build_gallery(environment_catalogs("uvicorn"))["routes"]
    for key, route in routes.items():
        key = "index" if key == "index" else route["url"]
        assert (tmp_path / f"{key}.py").is_file()
        assert (tmp_path / f"{key}.css").is_file() == (route["stylesheet"] is not None)
        assert (tmp_path / f"{key}_aux.js").is_file() == (key == "index" or route["logic"] is not None)


def logic_catalog(tmp_path):
    """A catalogue of two examples: ``extra-01`` with a JS module without ``Logic``, ``extra-02`` with one."""
    folder = tmp_path / "pages" / "logic"
    folder.mkdir(parents=True)
    for name in ("01_plain", "02_logic"):
        (folder / f"{name}.py").write_text("from gramlot import Page as BasePage\n\n\nclass Page(BasePage):\n    pass\n")
    (folder / "01_plain.js").write_text("export const note = 'a page module without Logic';\n")
    (folder / "02_logic.js").write_text("export class Logic {\n    twice(value) { return value * 2; }\n}\n")
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"environment": "extra", "families": [{"key": "logic", "folder": "logic", "title": "Logic", "examples": [
        {"key": f"extra-0{number}", "title": name, "folder": name, "description": name, "explanation": name}
        for number, name in ((1, "01_plain"), (2, "02_logic"))]}]}))
    return [(catalog, tmp_path / "pages")]


def test_stage_accepts_logic_modules_with_and_without_logic(tmp_path):
    pages = tmp_path / "staged"
    pages.mkdir()
    assets = stage(pages, logic_catalog(tmp_path), "/py")
    for key, name in (("extra-01", "01_plain"), ("extra-02", "02_logic")):
        assert (pages / f"pages/logic/{name}_aux.js").read_text() == f'export * from "/py/pages/logic/{name}.js";\n'
        assert assets[f"/pages/logic/{name}.js"]["type"] == "text/javascript; charset=utf-8"


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node to import the staged modules")
def test_staged_companions_import_with_and_without_logic(tmp_path):
    (tmp_path / "package.json").write_text('{"type": "module"}')
    pages = tmp_path / "staged"
    pages.mkdir()
    stage(pages, logic_catalog(tmp_path), tmp_path.as_uri())
    script = (
        f"const plain = await import({(pages / 'pages/logic/01_plain_aux.js').as_uri()!r});\n"
        f"const logic = await import({(pages / 'pages/logic/02_logic_aux.js').as_uri()!r});\n"
        "console.log(JSON.stringify([plain.Logic === undefined, typeof logic.Logic, new logic.Logic().twice(4)]));\n"
    )
    result = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == [True, "function", 8]


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
    options = parser.parse_args(["gallery", "--port", "9001", "--mount", "py/",
                                 "--catalog", str(catalog), str(tmp_path), "--serverless-download", "/downloads/gallery.zip"])
    assert options.run(options) == 0
    assert served["host"] == "127.0.0.1" and served["port"] == 9001
    assert served["mount_path"] == "/py"
    assert "serverless_download_url = '/downloads/gallery.zip'" in served["index"]
    assert served["assets"]["/gallery/dist/gallery.js"]["type"] == "application/javascript"
    defaults = parser.parse_args(["gallery"])
    assert (defaults.host, defaults.port, defaults.mount, defaults.catalog) == ("127.0.0.1", 8080, "", [])
