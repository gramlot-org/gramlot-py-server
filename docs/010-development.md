# 010 · Development

Document ID: **GFL-010**.

[Paired view](../docs_llm/010-development.md).

<a id="gfl-010-005"></a>

## 005 · Local checks

Block ID: **GFL-010-005**.

Use Python 3.11+. Run `uv sync --extra dev --extra docs`, then `uv run python scripts/check.py`. Enable hooks with `git config core.hooksPath hooks`. The checker runs Ruff, available tests, documentation pairing checks and Sphinx. No application tests exist in the scaffold; this is reported explicitly.

<a id="gfl-010-010"></a>

## 010 · Distribution verification

Block ID: **GFL-010-010**.

Run `uv run python -m build` and `uv run python -m twine check dist/*`. CI installs the wheel into an isolated environment and imports the namespace outside the checkout. Run `uv run mypy src/` for advisory typing. Package import checks do not establish Flask runtime compatibility.

<a id="gfl-010-015"></a>

## 015 · First implementation

Block ID: **GFL-010-015**.

Follow SPECIFICATION.md: select a documented runtime, define the Flask integration, implement a Python-authored Gramlot page and test WSGI delivery, resources, services, error handling, lifecycle and application isolation. Add SQLAlchemy as an independently tested optional profile. Add real behavior tests with implementation.
