# 020 · Verification

Document ID: **GS-020**.

<a id="gs-020-005"></a>
## 005 · Automated checks

`pytest -q tests/test_asgi.py` checks the Python ASGI Page, runtime asset,
main/source/close requests and owner isolation.

<a id="gs-020-015"></a>

The Python/Uvicorn profile was introduced after the 0.1.0 core release; its
verification must be recorded separately from the historical exporter evidence.

Local verification, 2026-09-24: the `gramlot-minimal` Python wheel installs
without a Kajenn dependency; the generic ASGI protocol test passes from the
installed wheel.
