"""Documentation builds independently of the adapter tests."""
from pathlib import Path
import tomllib

project = "gramlot-uvicorn"
author = "Genropy Team"
copyright = "2026, Softwell S.r.l."
release = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text())["project"]["version"]
version = release
extensions = ["myst_parser"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build", ".DS_Store"]
html_theme = "sphinx_rtd_theme"
html_logo = "_static/gramlot-logo.png"


def paired_view_links(app, docname, source):
    """Offer the paired Markdown guide as a download in standalone documentation builds."""
    import re

    source[0] = re.sub(r'\[Paired view\]\((\.\./docs(?:_llm)?/[^)]+\.md)\)', r'{download}`Paired view <\1>`', source[0])


def setup(app):
    app.connect("source-read", paired_view_links)
