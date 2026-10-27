# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""The verb ``gallery`` of every environment: the gallery of ``gramlot-examples``.

The environment serves the gallery with its own adapter (GE-010 section 025 of
``gramlot-examples``). A temporary pages folder holds one page per route:
``index.py``, the gallery page with the catalogues and its URLs under the mount
path, and for each example ``<key>.py``, which appends ``frame.js``, its
stylesheet ``<key>.css`` and ``<key>_aux.js``, which re-exports every name of the
logic module from its URL (``export *``): ``Logic`` when the module exports it, nothing
when it does not, as the core allows. The adapter serves the ``assets`` of
``build_gallery`` under the same mount path, each logic module as JavaScript.

Environment catalogues, when supplied, extend the common examples. Setup and
quick-start instructions stay in the server documentation and project templates.
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
        "spec.loader.exec_module(module)\n"
        "if 'PageStore' in vars(module):\n"
        "    PageStore = module.PageStore\n\n\n"
        f"class Page(module.Page):\n{body}"
    )


def stage_tools(folder, *, remote_edit=False):
    """Expose only a disposable sample workspace through the Python IDE."""
    from gramlot_py_server.ide import stage_ide
    examples = examples_package()
    documents = folder / ".gallery-documents"
    shutil.copytree(Path(examples.__file__).parent / "documents", documents,
                    ignore=shutil.ignore_patterns("__pycache__", ".*", "*.pyc", "*.pyo"))
    source = folder / ".gallery-tools"
    tools = source / "07-tools"
    stage_ide(tools, roots=[documents], remote_edit=remote_edit)
    page = tools / "index.py"
    page.write_text(page.read_text(encoding="utf-8") + f'''    title = "IDE: edit sample documents"
    def top(self, pane):
        pane.set_attr(dict(height="80px", padding="8px 12px"))
        pane.h2(self.title, margin="0 0 4px")
        pane.p("Open a file, edit its draft and try Undo or Revert. "
               "Save requires Remote Edit on the host. The gallery restores these samples on restart.", margin="0")
    def behavior(self, shell):
        super().behavior(shell)
        shell.dataController("this.SET('.browser.requestedRoot', root)",
                             root={str(documents)!r}, _onStart=True)
''', encoding="utf-8")
    (tools / "02-directory_tree.py").write_text(
        'from gramlot import Page as BasePage\n'
        'from gramlot.page import file_system_tree\n'
        'from gramlot.collections.tree import mygramlot as tree\n'
        'from gramlot_py_server.filesystem import FileSystemPageMixin\n\n'
        'class Page(FileSystemPageMixin, BasePage):\n'
        '    title = "Browse a directory on disk"\n'
        '    gramlots = [tree]\n'
        f'    filesystem_roots = ({str(documents)!r},)\n'
        '    def main(self, root):\n'
        '        pane = root.main(padding="16px", datapath="filesDemo")\n'
        '        pane.h2(self.title)\n'
        '        pane.p("These are real files in the gallery sample directory on the server. "\n'
        '               "Expand a folder to load its contents on demand. This view does not modify files.")\n'
        '        file_system_tree(pane, datapath=".browser")\n'
        '        pane.dataController("this.SET(\'.browser.requestedRoot\', root)",\n'
        f'                            root={str(documents)!r}, _onStart=True)\n', encoding="utf-8")
    (tools / "02-directory_tree_aux.js").write_text(
        'export {FileSystemLogic as Logic} from "@gramlot/gramlot";\n', encoding="utf-8")
    introduction = (
        "# Tools and IDE\n\n"
        "Open **Live Source playground** to create, update and remove Source nodes.\n\n"
        "Open **Browse a directory on disk** to expand real folders on demand.\n\n"
        "Open **IDE: edit sample documents** to browse a small document workspace. "
        "Edit drafts, compare previews, undo changes or revert to the saved text. "
        "Saving is disabled unless the host enables Remote Edit.\n\n"
        "The Inspector is available from the gallery rail: inspect the Source and Data "
        "of the current lesson without leaving it.\n"
    )
    for name in ("00-index.md", "README.md", "index.md"):
        (tools / name).write_text(introduction, encoding="utf-8")
    catalog = source / "catalog.json"
    catalog.write_text(json.dumps({"environment": "python", "families": [{
        "key": "python_tools", "title": "Tools and IDE", "folder": "07-tools",
        "examples": []
    }]}), encoding="utf-8")
    return catalog, source


def stage(folder: Path, catalogs: list[tuple[Path, Path]], prefix: str, serverless_download_url: str | None = None, *, remote_edit=False, modules=()) -> dict:
    """Write the pages of the gallery into ``folder``; return the assets to serve."""
    examples = examples_package()
    catalogs = [*catalogs, stage_tools(folder, remote_edit=remote_edit)]
    from gramlot_examples.gallery.modules import registered_modules
    registered_modules(modules)  # Fail before creating a partially configured gallery.
    gallery = examples.build_gallery(catalogs)
    routes = gallery["routes"]
    assets: dict = gallery["assets"]
    # Tools open as workspace pages, without the lesson's explanation/code split.
    for name in ("index", "02-directory_tree"):
        tool = routes[f"pages/07-tools/{name}"]
        tool["logic"] = tool["page"].with_name(f"{name}_aux.js")
        assets[f"/pages/07-tools/{name}_aux.js"] = {"file": tool["logic"], "type": JAVASCRIPT}
    url_of = {Path(asset["file"]).resolve(): url for url, asset in assets.items()}
    gallery_page = Path(examples.__file__).resolve().parent / "gallery" / "page.py"
    listed = [(str(catalog), str(pages)) for catalog, pages in catalogs]
    (folder / "index.py").write_text(subclass_module(gallery_page, "gramlot_gallery_index", (
        f"    catalogs = {listed!r}\n"
        f"    gallery_modules = {modules!r}\n"
        f"    serverless_download_url = {serverless_download_url!r}\n"
        f"    logoUrl = {prefix + '/assets/branding/svg/gramlot-horizontal-primary.svg'!r}\n"
    )))
    (folder / "index_aux.js").write_text(f"export {{Logic}} from {json.dumps(prefix + '/gallery/dist/gallery.js')};\n")
    gallery_urls = {key: prefix + "/" + route["url"] for key, route in routes.items() if key != "index"}
    for key, route in routes.items():
        if key == "index":
            continue
        key = route["url"]
        (folder / f"{key}.py").parent.mkdir(parents=True, exist_ok=True)
        (folder / f"{key}.py").write_text(subclass_module(route["page"], f"gramlot_gallery_{key}", (
            f"    gallery_urls = {gallery_urls!r}\n"
            "    def main(self, root):\n"
            "        super().main(root)\n"
            f"        root.script(src={prefix + '/gallery/dist/frame.js'!r})\n"
        )))
        if route["data"] is not None:
            shutil.copyfile(route["data"], folder / f"{key}_data.tytx")
        if route["stylesheet"] is not None:
            shutil.copyfile(route["stylesheet"], folder / f"{key}.css")
        if route["logic"] is not None:
            url = url_of.get(Path(route["logic"]).resolve())
            if url is None:
                raise ValueError(f"The logic module of {key} is not a gallery asset: {route['logic']}")
            assets[url] = {**assets[url], "type": JAVASCRIPT}
            (folder / f"{key}_aux.js").write_text(f"export * from {json.dumps(prefix + url)};\n")
    return assets


def add_gallery(verbs, environment: str, serve) -> None:
    """Add ``gallery`` to the verbs of ``environment``; ``serve`` runs its server."""
    parser = verbs.add_parser("gallery", help=f"serve the example gallery with {environment}")
    parser.add_argument("--host", default="127.0.0.1", help="the address to listen on (127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="the port to listen on (8080)")
    parser.add_argument("--mount", default="", help="the prefix of every URL, for example /py")
    parser.add_argument("--catalog", nargs=2, action="append", default=[], metavar=("CATALOG", "PAGES"),
                        help="add the families of a catalog.json and its pages folder; repeatable")
    parser.add_argument("--serverless-download", help="URL of an offline gallery ZIP served by the deployment")
    if environment == "uvicorn":
        parser.add_argument("--websocket", action="store_true", help="enable the shared PageStore channel")
    parser.add_argument("--remote-edit", action="store_true", help="allow saving in the disposable IDE sample workspace")
    parser.set_defaults(run=lambda options: run_gallery(environment, serve, options))


def run_gallery(environment: str, serve, options) -> int:
    """Stage the gallery in a temporary folder and serve it until the server stops."""
    prefix = "/" + options.mount.strip("/") if options.mount.strip("/") else ""
    catalogs = environment_catalogs(environment) + [
        (Path(catalog).resolve(), Path(pages).resolve()) for catalog, pages in options.catalog
    ]
    with TemporaryDirectory(prefix="gramlot-gallery-") as folder:
        assets = stage(Path(folder), catalogs, prefix, options.serverless_download, remote_edit=options.remote_edit)
        print(f"Gramlot gallery ({environment}): http://{options.host}:{options.port}{prefix}/", flush=True)
        try:
            serve(Path(folder), host=options.host, port=options.port, mount_path=prefix, assets=assets,
                  **({"websocket": options.websocket} if environment == "uvicorn" else {}))
        except ModuleNotFoundError as error:
            if error.name != "uvicorn":
                raise
            raise SystemExit(
                f"gramlot {environment} gallery: uvicorn is not installed: "
                'python -m pip install "gramlot-py-server[uvicorn]"'
            ) from error
    return 0


__all__ = ["add_gallery", "environment_catalogs", "run_gallery", "stage"]
