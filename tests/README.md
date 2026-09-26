# Tests

`scripts/check.py` runs `test_native_html.py` against clean Gramlot,
`gramlot-minimal` and a real `genro_asgi.BaseServer`. It also checks Ruff and
builds the documentation with warnings as errors. Native imports must succeed;
the suite does not skip missing dependencies.
