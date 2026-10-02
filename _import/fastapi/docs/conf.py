# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Build the guides without installing FastAPI or the experimental core."""
from pathlib import Path
import os
import tomllib

project = "Gramlot FastAPI"
author = "Genropy Team"
copyright = "2026, Softwell S.r.l."
release = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text())["project"]["version"]
version = release
language = "en"
extensions = ["myst_parser"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
root_doc = "index"
exclude_patterns = ["_build", ".DS_Store"]
nitpicky = True
html_theme = "sphinx_rtd_theme"
html_title = f"Gramlot FastAPI {release} — POC documentation"
html_logo = "_static/gramlot-logo.png"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_theme_options = {"style_nav_header_background": "#2980b9"}
html_baseurl = os.environ.get("READTHEDOCS_CANONICAL_URL", "")

templates_path = ["_templates"]
