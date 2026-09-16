# 010 · Development

Document ID: **GFL-010**.

[Paired view](../docs/010-development.md).

<a id="gfl-010-005"></a>

## 005 · Local checks

Block ID: **GFL-010-005**.

Python 3.11+ is required. Run `uv sync --extra dev --extra docs` and `uv run python scripts/check.py`; enable `hooks` with Git. Ruff, available tests, paired-guide checks and Sphinx must pass. The scaffold explicitly reports absent application tests.

<a id="gfl-010-010"></a>

## 010 · Distribution verification

Block ID: **GFL-010-010**.

Run `uv run python -m build` and `uv run python -m twine check dist/*`. CI imports the installed wheel in isolation outside the checkout. Mypy is advisory. Import success is not Flask compatibility.

<a id="gfl-010-015"></a>

## 015 · First implementation

Block ID: **GFL-010-015**.

Follow SPECIFICATION.md: choose a runtime, define Flask integration and test a Python-authored Gramlot page, WSGI delivery, resources, services, errors, lifecycle and isolation. Add behavior tests with implementation and verify SQLAlchemy separately.
