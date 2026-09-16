<p align="center">
  <img src="docs/_static/gramlot-logo.png" alt="Gramlot logo" width="160">
</p>

# gramlot-flask

Flask host integration for Gramlot.

**Status: Pre-Alpha — repository scaffold; no Flask runtime integration yet.**

This repository follows the development layout of `gramlot-genro-asgi` and the
host ownership boundary of `gramlot-fastapi`. It contains package metadata, an
empty Python namespace, quality tooling, CI, paired documentation and examples/test
locations. Installation does not provide a server, page API or runnable demo.

Flask will own request/response and application lifecycle integration. Gramlot
owns Source, Data Bags, bindings, controllers, resolvers, components and shared
server contracts. Database selection is independent: plain Flask hosting will
require no database, and an optional SQLAlchemy example will reuse the database
adapter rather than implement one here.

The clean Gramlot repository currently records architecture and port review, not
an executable runtime. Runtime dependency versions will be selected with the first
bounded integration. No Flask, core or database compatibility is claimed yet.

Read [SPECIFICATION.md](SPECIFICATION.md), the [overview](docs/005-overview.md)
and the [concise index](docs_llm/index.md).

## Development

From this checkout with Python 3.11+ and uv:

```sh
uv sync --extra dev --extra docs
uv run python scripts/check.py
uv run python -m build
uv run python -m twine check dist/*
git config core.hooksPath hooks
```

The checker runs Ruff, any available behavior tests, paired-document validation
and Sphinx with warnings treated as errors. Until implementation starts it reports
that application tests do not exist. Mypy is advisory. CI also installs the wheel
in isolation outside the checkout. `uv.lock` records development dependencies.

## Layout

- `src/gramlot_flask/`: package namespace; future Flask adapter.
- `tests/`: future behavior tests, with the required coverage described today.
- `examples/`: scope for the first Python-authored Gramlot example.
- `docs/` and `docs_llm/`: expanded and concise Sphinx documentation, namespace GFL.
- `scripts/`, `hooks/`, `.github/workflows/`: local and CI checks.

`develop` carries new work; `main` is the consolidated public reference after
verification and owner acceptance. Read the Docs configuration is provided; its
external service is not connected. No automatic publication or deployment exists.

## License

Apache License 2.0. Copyright 2026 Softwell S.r.l. See LICENSE and NOTICE.
