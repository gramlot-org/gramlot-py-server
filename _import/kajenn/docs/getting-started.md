# Getting started: Kajenn native HTML

Install locally built Gramlot, gramlot-minimal and gramlot-kajenn wheels plus
the Hello World application's Python host dependencies. Run
`python -m gramlot_example_app.server.kajenn` and open
<http://127.0.0.1:8000/page/>. It mounts `KajennNativeHtmlApplication` on
`genro_asgi.BaseServer`. See [GA-010](010-native-html.md).

The generic Uvicorn launcher uses `gramlot-minimal` and is documented there.
For the old PoC setup and GenroPy database experiment, consult
[GA-005](005-genro-asgi-legacy.md). Its old CLI and page APIs are historical
and incompatible with clean Gramlot core.

Run `python scripts/check.py` in an environment with current core, minimal,
Kajenn and development/documentation dependencies installed. The native suite
fails on missing imports; legacy tests are retained separately. First-party
dependencies are unconstrained and refreshed during setup.
