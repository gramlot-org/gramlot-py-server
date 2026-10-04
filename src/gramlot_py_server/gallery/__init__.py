# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""The verb ``gallery`` of every environment: the gallery of ``gramlot-examples``.

The environment serves the gallery with its own adapter (GE-010 section 025 of
``gramlot-examples``). A temporary pages folder holds one page per route:
``index.py``, the gallery page with the catalogues and its URLs under the mount
path, and for each example ``<key>.py``, which appends ``frame.js``, its
stylesheet ``<key>.css`` and ``<key>_aux.js``, which re-exports ``Logic`` from
the URL of the logic module. The adapter serves the ``assets`` of
``build_gallery`` under the same mount path, each logic module as JavaScript.

``gallery/<environment>/`` holds the catalogue of the environment, whose first
family is the quick start of ``gramlot <environment> new``.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

CATALOGS = Path(__file__).resolve().parent
JAVASCRIPT = "text/javascript; charset=utf-8"


def examples_package():
    """The ``gramlot_examples`` module, or the error that names the extra ``gallery``."""
    try:
        import gramlot_examples
    except ModuleNotFoundError as error:
        if error.name != "gramlot_examples":
            raise
        raise SystemExit(
            "The gallery needs gramlot-examples: "
            'python -m pip install "gramlot-py-server[gallery]"'
        ) from error
    return gramlot_examples


def environment_catalogs(environment: str) -> list[tuple[Path, Path]]:
    """The catalogue of this package for ``environment``, as a (catalog.json, pages) pair."""
    folder = CATALOGS / environment
    return [(folder / "catalog.json", folder / "pages")] if (folder / "catalog.json").is_file() else []


def subclass_module(original: Path, name: str, body: str) -> str:
    """The source of a page module that loads ``original`` and subclasses its ``Page``."""
    return (
        "import importlib.util\n\n"
        f"spec = importlib.util.spec_from_file_location({name!r}, {str(original)!r})\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(module)\n\n\n"
        f"class Page(module.Page):\n{body}"
    )


def stage(folder: Path, catalogs: list[tuple[Path, Path]], prefix: str) -> dict:
    """Write the pages of the gallery into ``folder``; return the assets to serve."""
    examples = examples_package()
    gallery = examples.build_gallery(catalogs)
    routes = gallery["routes"]
    assets: dict = gallery["assets"]
    url_of = {Path(asset["file"]).resolve(): url for url, asset in assets.items()}
    gallery_page = Path(examples.__file__).resolve().parent / "gallery" / "page.py"
    listed = [(str(catalog), str(pages)) for catalog, pages in catalogs]
    (folder / "index.py").write_text(subclass_module(gallery_page, "gramlot_gallery_index", (
        f"    catalogs = {listed!r}\n"
        f"    logoUrl = {prefix + '/assets/branding/gramlot-logo-dark.svg'!r}\n"
        f"    galleryScript = {prefix + '/gallery/dist/gallery.js'!r}\n"
    )))
    for key, route in routes.items():
        if key == "index":
            continue
        (folder / f"{key}.py").write_text(subclass_module(route["page"], f"gramlot_gallery_{key}", (
            "    def main(self, root):\n"
            "        super().main(root)\n"
            f"        root.script(src={prefix + '/gallery/dist/frame.js'!r})\n"
        )))
        if route["stylesheet"] is not None:
            shutil.copyfile(route["stylesheet"], folder / f"{key}.css")
        if route["logic"] is not None:
            url = url_of.get(Path(route["logic"]).resolve())
            if url is None:
                raise ValueError(f"The logic module of {key} is not a gallery asset: {route['logic']}")
            assets[url] = {**assets[url], "type": JAVASCRIPT}
            (folder / f"{key}_aux.js").write_text(f"export {{Logic}} from {json.dumps(prefix + url)};\n")
    return assets


def add_gallery(verbs, environment: str, serve) -> None:
    """Add ``gallery`` to the verbs of ``environment``; ``serve`` runs its server."""
    parser = verbs.add_parser("gallery", help=f"serve the example gallery with {environment}")
    parser.add_argument("--host", default="127.0.0.1", help="the address to listen on (127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="the port to listen on (8080)")
    parser.add_argument("--mount", default="", help="the prefix of every URL, for example /py")
    parser.add_argument("--catalog", nargs=2, action="append", default=[], metavar=("CATALOG", "PAGES"),
                        help="add the families of a catalog.json and its pages folder; repeatable")
    parser.set_defaults(run=lambda options: run_gallery(environment, serve, options))


def run_gallery(environment: str, serve, options) -> int:
    """Stage the gallery in a temporary folder and serve it until the server stops."""
    prefix = "/" + options.mount.strip("/") if options.mount.strip("/") else ""
    catalogs = environment_catalogs(environment) + [
        (Path(catalog).resolve(), Path(pages).resolve()) for catalog, pages in options.catalog
    ]
    with TemporaryDirectory(prefix="gramlot-gallery-") as folder:
        assets = stage(Path(folder), catalogs, prefix)
        print(f"Gramlot gallery ({environment}): http://{options.host}:{options.port}{prefix}/", flush=True)
        try:
            serve(Path(folder), host=options.host, port=options.port, mount_path=prefix, assets=assets)
        except ModuleNotFoundError as error:
            if error.name != "uvicorn":
                raise
            raise SystemExit(
                f"gramlot {environment} gallery: uvicorn is not installed: "
                'python -m pip install "gramlot-py-server[uvicorn]"'
            ) from error
    return 0


__all__ = ["add_gallery", "environment_catalogs", "run_gallery", "stage"]
