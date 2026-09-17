# Getting started

Use Python 3.11+ with an authorized sibling `gramlot-poc` checkout. Install the
locked development environment and launch the plain example:

```sh
uv sync --extra dev --extra docs
uv run python -m gramlot_genro_asgi examples/plain --port 8065
```

Open `http://127.0.0.1:8065/page/hello/`. The page uses Gramlot Data, bindings and
RPC declarations. See [the integration contract](005-genro-asgi-legacy.md) for
legacy setup, dependency constraints, database ownership and verification.

Run `uv run python scripts/check.py` before committing. Legacy database checks
require a separate GenroPy installation; without it that integration test skips.
The package is experimental and is not an accepted clean-core port.
