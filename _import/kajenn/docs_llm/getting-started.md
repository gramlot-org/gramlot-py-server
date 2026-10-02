# Getting started: Kajenn native HTML

[Expanded](../docs/getting-started.md).

Install local Gramlot, gramlot-minimal and gramlot-kajenn wheels and the Hello
World Python host dependencies. Run
`python -m gramlot_example_app.server.kajenn`; open `/page/` on port 8000.
This uses `KajennNativeHtmlApplication` on `genro_asgi.BaseServer`;
see [GA-010](010-native-html.md). Generic Uvicorn hosting belongs to
`gramlot-minimal`.

Run `python scripts/check.py` with current dependencies installed. Native
imports must pass; old PoC tests/CLI remain historical and require absent
clean-core APIs. See [GA-005](005-genro-asgi-legacy.md). First-party
requirements are unconstrained.
