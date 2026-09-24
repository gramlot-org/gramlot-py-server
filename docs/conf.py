# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Sphinx configuration for gramlot-kajenn."""
from importlib.metadata import version as package_version

project = "gramlot-kajenn"
author = "Genropy Team"
copyright = "2026, Softwell S.r.l."
release = package_version(project)
version = release
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon", "myst_parser"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
