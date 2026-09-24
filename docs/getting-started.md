# Getting started: native HTML

For the clean Gramlot 0.1.0 profile, install the locally built core wheel and
all three adapter wheels, then the Hello World wheel. Run
`python -m gramlot_example_app.server.uvicorn` and open
<http://127.0.0.1:8000/>. Alternatively run
`python -m gramlot_example_app.server.kajenn` and open
<http://127.0.0.1:8000/page/>. These launchers use `create_asgi_application`
and `KajennNativeHtmlApplication`. See [GA-010](010-native-html.md).

## Historical PoC setup

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
This older PoC setup is outside native 0.1.0 compatibility.


Native release checks (2026-09-24): `python scripts/check.py` now runs Ruff,
the native protocol tests and documentation builds against the clean core. CI
builds core from its maintained main branch with floating dependencies. The
retained legacy tests and PoC installation probes remain separate historical
coverage; they are not executed as native 0.1.0 acceptance checks.

Native hooks use the active Python environment with the clean core and adapter
dev/docs dependencies installed. First-party dependency lockfiles are excluded;
missing native imports fail collection rather than skipping the protocol suite.
