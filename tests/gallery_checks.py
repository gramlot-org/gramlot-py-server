"""Checks shared by the gallery tests of every adapter."""
import re

from gramlot_py_server.gallery import environment_catalogs, stage

# URL below the mount path, start of its media type.
EXPECTED = [
    ("/", "text/html"),
    ("/e01", "text/html"),
    ("/{environment}-01", "text/html"),
    ("/c03_aux.js", "text/javascript"),
    ("/pages/controllers/03_named_logic.js", "text/javascript"),
    ("/gallery/dist/gallery.js", "application/javascript"),
    ("/gallery/dist/frame.js", "application/javascript"),
    ("/gallery/gallery.css", "text/css"),
    ("/themes/gramlot-base/theme.css", "text/css"),
    ("/assets/branding/gramlot-logo-dark.svg", "image/svg+xml"),
]


def staged(tmp_path, environment, prefix="/py"):
    """Stage the gallery of ``environment``; return the pages folder and the assets."""
    folder = tmp_path / "gallery"
    folder.mkdir()
    return folder, stage(folder, environment_catalogs(environment), prefix)


def expected(environment, prefix="/py"):
    """The URLs the gallery serves, with the start of their media type."""
    return [(prefix + url.format(environment=environment), kind) for url, kind in EXPECTED]


def page_id(document):
    return re.search(r'"pageId":"([0-9a-f]+)"', document).group(1)


def check_index_main(source, prefix="/py"):
    """The Source of the gallery page carries the logo and the script under the mount path."""
    assert f"{prefix}/assets/branding/gramlot-logo-dark.svg" in source
    assert f"{prefix}/gallery/dist/gallery.js" in source
