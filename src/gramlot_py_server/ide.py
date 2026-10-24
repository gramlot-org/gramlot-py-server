"""Stage the reusable IDE with explicitly bounded filesystem access."""
from pathlib import Path


def stage_ide(pages, *, roots, remote_edit=False):
    """Write a page and Logic companion using the verified built-in collections.

    Only the configured roots are readable. Remote Edit permits explicit saves;
    it does not enable executing edited Python or native document compilers.
    """
    pages = Path(pages)
    pages.mkdir(parents=True, exist_ok=True)
    roots = tuple(str(Path(root).resolve(strict=True)) for root in roots)
    if not roots or any(not Path(root).is_dir() for root in roots):
        raise ValueError("The IDE requires at least one allowed directory")
    if any((pages / name).exists() for name in ("index.py", "index_aux.js")):
        raise FileExistsError("IDE staging would overwrite an existing page")
    (pages / "index.py").write_text(
        'from gramlot.page import IdePage\n'
        'from gramlot.collections.inputs import mygramlot as inputs\n'
        'from gramlot.collections.layout import mygramlot as layout\n'
        'from gramlot.collections.tree import mygramlot as tree\n'
        'from gramlot.collections.editors import mygramlot as editors\n'
        'from gramlot.collections.typst import mygramlot as typst\n'
        'from gramlot_py_server.filesystem import FileSystemPageMixin\n\n'
        'class Page(FileSystemPageMixin, IdePage):\n'
        '    gramlots = [inputs, layout, tree, editors, typst]\n'
        f'    filesystem_roots = {roots!r}\n'
        f'    remote_edit = {bool(remote_edit)!r}\n', encoding="utf-8")
    (pages / "index_aux.js").write_text(
        'export {IdeLogic as Logic} from "@gramlot/gramlot";\n', encoding="utf-8")
