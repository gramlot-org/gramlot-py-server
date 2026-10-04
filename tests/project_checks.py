"""Checks shared by the tests of the projects that ``gramlot <environment> new`` creates."""
import re

STRICT_CSP = "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"


def check_files(folder, framework_file, requirement, start, printed):
    """The project has its files, its requirement and the start command in the docstring and output."""
    assert (folder / "requirements.txt").read_text() == f"{requirement}\n"
    assert (folder / "pages" / "index.py").is_file()
    assert "export class Logic" in (folder / "pages" / "index.js").read_text()
    assert f"``{start}``" in (folder / framework_file).read_text().split("\n", 1)[0]
    assert f"  {start}\n" in printed


def check_document(text, policy, prefix=""):
    """The bootstrap document of ``index``: title, strict policy, page module as its logic."""
    nonce = re.search(r'nonce="([^"]+)"', text).group(1)
    assert "<title>Hello</title>" in text
    assert policy == STRICT_CSP.replace("{nonce}", nonce)
    assert f'{{"url":"{prefix}/index.js","group":null}}' in text


def check_main(tags):
    """The Source of ``main``: the bound field and the formula named in ``Logic``."""
    assert tags["input"]["value"] == "^.name"
    assert tags["input"]["live"] is True
    assert tags["dataFormula"]["func"] == "greeting"
    assert "formula" not in tags["dataFormula"]
    assert tags["dataSetter"]["value"] == "Ada"
