# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""The verb ``new`` of every environment: a project from the quick start templates.

``templates/<environment>/`` holds the files of the framework and the
``requirements.txt`` with the extra; ``templates/pages/`` holds the page
``index.py`` and its page module ``index.js``, which exports ``Logic``. The
templates are the quick start of the README.
"""

from __future__ import annotations

import shutil
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent / "templates"


def project_files(environment: str) -> dict[str, Path]:
    """The files of a new project: relative path → template file."""
    files = {}
    for relative, folder in (("", TEMPLATES / environment), ("pages/", TEMPLATES / "pages")):
        for template in sorted(folder.iterdir()):
            if template.is_file() and not template.name.startswith("."):
                files[relative + template.name] = template
    return files


def add_new(verbs, environment: str, *, start: str, url: str) -> None:
    """Add ``new <folder>`` to the verbs of ``environment``."""
    parser = verbs.add_parser("new", help=f"create a project served by {environment}")
    parser.add_argument("folder", type=Path, help="the project folder, new or empty")
    parser.set_defaults(run=lambda options: new_project(environment, options.folder, start=start, url=url))


def new_project(environment: str, folder: Path, *, start: str, url: str) -> int:
    """Write the project of ``environment`` into ``folder`` and print how to start it."""
    if folder.exists() and (not folder.is_dir() or any(folder.iterdir())):
        raise SystemExit(f"gramlot {environment} new: {folder} exists and is not an empty folder")
    files = project_files(environment)
    for relative, template in files.items():
        target = folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(template, target)
    print(f"Created {folder} for {environment}:")
    for relative in files:
        print(f"  {relative}")
    print("Start it:")
    print(f"  cd {folder}")
    print("  python -m pip install -r requirements.txt")
    print(f"  {start}")
    print(f"Then open {url}")
    return 0


__all__ = ["add_new", "new_project", "project_files"]
