"""Checks shared by the gallery tests of every adapter."""
import re

from gramlot_py_server.gallery import environment_catalogs, examples_package, stage

# URL below the mount path, start of its media type.
EXPECTED = [
    ("/", "text/html"),
    ("/pages/00-html_svg/01-html_basics/01-hello_world", "text/html"),
    ("/pages/03-controllers/01-logic/03-named_logic_aux.js", "text/javascript"),
    ("/pages/03-controllers/01-logic/03-named_logic.js", "text/javascript"),
    ("/gallery/dist/gallery.js", "application/javascript"),
    ("/gallery/dist/frame.js", "application/javascript"),
    ("/gallery/gallery.css", "text/css"),
    ("/themes/gramlot-base/theme.css", "text/css"),
    ("/assets/branding/svg/gramlot-horizontal-primary.svg", "image/svg+xml"),
]


def staged(tmp_path, environment, prefix="/py"):
    """Stage the gallery of ``environment``; return the pages folder and the assets."""
    folder = tmp_path / "gallery"
    folder.mkdir()
    return folder, stage(folder, environment_catalogs(environment), prefix)


def gallery_collections():
    """The component collections of the gallery, as the gallery command passes them to the adapter."""
    return examples_package().build_gallery()["collections"]


def expected(environment, prefix="/py"):
    """The URLs the gallery serves, with the start of their media type."""
    return [(prefix + url.format(environment=environment), kind) for url, kind in EXPECTED]


def page_id(document):
    return re.search(r'"pageId":"([0-9a-f]+)"', document).group(1)


def check_index_main(source, prefix="/py"):
    """The Source carries the mounted logo and invokes the staged Logic lifecycle."""
    assert f"{prefix}/assets/branding/svg/gramlot-horizontal-primary.svg" in source
    assert "galleryInitialize" in source
    assert "galleryMount" in source
    assert "Quick start" not in source
