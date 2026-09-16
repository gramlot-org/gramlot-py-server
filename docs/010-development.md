# 010 · Development

Document ID: **GFL-010**.

[Paired view](../docs_llm/010-development.md).

<a id="gfl-010-005"></a>

## 005 · Local checks

Block ID: **GFL-010-005**.

Use Python 3.11+. Run `uv sync --extra dev --extra docs`, then `uv run python scripts/check.py`. The checker runs Ruff, real Flask and Microblog behavior tests, paired-guide checks and both Sphinx builds. Enable hooks with `git config core.hooksPath hooks`.

<a id="gfl-010-010"></a>

## 010 · Distribution verification

Block ID: **GFL-010-010**.

Run `uv run python -m build` and `uv run python -m twine check dist/*`. CI installs the wheel outside the checkout, verifies plain hosting without database/demo dependencies, then installs demo extras and verifies login, Gramlot Source and assets. Runtime/core dependencies remain pinned to a checksummed experimental wheel. Mypy is advisory.

<a id="gfl-010-015"></a>

## 015 · Demo operation

Block ID: **GFL-010-015**.

Run `uv run gramlot-flask` or `uv run gramlot-flask demo --data-dir /path/to/demo --port 8074`. Open the printed Microblog URL, sign in as demo / gramlot-demo and follow Gramlot. A new database receives six users, 24 posts, follows and six messages; existing data is preserved. Ctrl+C closes host and database resources. Use `serve DIRECTORY` for plain pages. Test browser selection, original-profile navigation and login protection when changing the integration.
