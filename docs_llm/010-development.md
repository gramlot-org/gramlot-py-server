# 010 · Development

Document ID: **GFL-010**.

[Paired view](../docs/010-development.md).

<a id="gfl-010-005"></a>

## 005 · Local checks

Block ID: **GFL-010-005**.

Python 3.11+. Run `uv sync --extra dev --extra docs`, then `uv run python scripts/check.py`. Ruff, Flask/Microblog tests, paired guides and both Sphinx builds are required. Enable Git hooks with `git config core.hooksPath hooks`.

<a id="gfl-010-010"></a>

## 010 · Distribution verification

Block ID: **GFL-010-010**.

Build with `uv run python -m build`; validate with `uv run python -m twine check dist/*`. CI checks installed-wheel plain hosting without database/demo extras, then demo login, Source and assets outside the checkout. The experimental core wheel is checksummed; mypy is advisory.

<a id="gfl-010-015"></a>

## 015 · Demo operation

Block ID: **GFL-010-015**.

Run `uv run gramlot-flask` or `demo --data-dir /path/to/demo --port 8074`. Login demo / gramlot-demo, then Gramlot. New databases get six users, 24 posts, follows and six messages; relaunches preserve data. Ctrl+C releases resources. `serve DIRECTORY` runs plain pages. Browser QA covers selection, original profiles and login protection.
