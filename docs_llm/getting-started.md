# Getting started

[Expanded](../docs/getting-started.md).

Native 0.1.0: install local core, FastAPI, Flask, Genro ASGI and Hello World
wheels. Run `python -m gramlot_example_app.server.uvicorn` and open `/`, or
`python -m gramlot_example_app.server.kajenn` and open `/page/` on port 8000.
See [GA-010](010-native-html.md). The following setup is historical PoC work:

Python 3.11+, authorized sibling gramlot-poc. `uv sync --extra dev --extra docs`;
`uv run python -m gramlot_genro_asgi examples/plain --port 8065`; open
http://127.0.0.1:8065/page/hello/. Run scripts/check.py before commits. Legacy DB
check needs separately installed GenroPy or skips. Experimental, not accepted core.
See [contract](005-genro-asgi-legacy.md) for constraints and setup.


Native release checks (2026-09-24): `python scripts/check.py` now runs Ruff,
the native protocol tests and documentation builds against the clean core. CI
builds core from its maintained main branch with floating dependencies. The
retained legacy tests and PoC installation probes remain separate historical
coverage; they are not executed as native 0.1.0 acceptance checks.
