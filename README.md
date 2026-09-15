# gramlot-genro-asgi

Gramlot applications hosted by Genro ASGI.

**Status: Pre-Alpha — repository boilerplate, no application implementation yet.**

## Scope

Genro ASGI hosting without a database, followed by an optional Genropy database profile.

Keep Genro ASGI hosting in this consumer repository or its host integration. Do not introduce a Genro ASGI dependency into the Gramlot core. Review the existing genro-asgi[gui] integration before designing application hosting.

The package currently contains only its namespace. Installing it does not start
a server or provide a working demo. Adapter extraction, runtime dependencies,
page migration and host commands are future implementation work described in
[SPECIFICATION.md](SPECIFICATION.md).

## Development

```sh
git clone https://github.com/gramlot-org/gramlot-genro-asgi.git
cd gramlot-genro-asgi
uv sync --extra dev --extra docs
uv run python scripts/check.py
uv run python -m build
uv run python -m twine check dist/*
git config core.hooksPath hooks
```

Python 3.11+; Hatchling build backend; pytest, Ruff and advisory mypy; Sphinx
with Markdown support. These conventions follow `genro-asgi`. `uv.lock` records
the development environment. A pip-based setup is also supported:
`python -m pip install -e '.[dev,docs]'`.

## Layout

- `src/gramlot_genro_asgi/`: future implementation package.
- `tests/`: behavior tests added with the first implementation.
- `examples/`: future runnable, Python-authored Gramlot examples.
- `docs/`: Sphinx documentation.
- `hooks/`: pre-commit lint/advisory typing and pre-push checks.
- `.github/workflows/`: package and documentation checks.

`main` holds the initial baseline; use `develop` for new work. No automatic
package publication or deployment is configured. Read the Docs configuration
is provided, but its external service has not been connected.

## Checks

```sh
uv run python scripts/check.py
uv run mypy src/  # advisory
uv run python -m sphinx -W --keep-going -b html docs docs/_build/html
```

The check script explicitly reports that no application tests exist in the
initial scaffold. Once `tests/test_*.py` files are added, pytest is mandatory
and failures block the checks. CI also builds and installs the wheel in a
separate environment to verify packaging.

## License

Apache License 2.0. Copyright 2026 Softwell S.r.l. See LICENSE and NOTICE.
