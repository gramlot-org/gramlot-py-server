# 020 · Verification

Document ID: **GS-020**.

<a id="gs-020-005"></a>
## 005 · Automated checks

`pytest -q tests/test_asgi.py` checks the Python ASGI Page, runtime asset,
main/source/close requests and owner isolation, the mount prefix `/py` on the
`PageBootstrap` document, companion and `Page.css` serving below the pages
folder, and the nonce in both Content Security Policy profiles.

<a id="gs-020-015"></a>

The Python/Uvicorn profile was introduced after the 0.1.0 core release; its
verification must be recorded separately from the historical exporter evidence.

Local verification, 2026-09-24: the `gramlot-minimal` Python wheel installs
without a Kajenn dependency; the generic ASGI protocol test passes from the
installed wheel.

Local verification, 2026-09-30, with the core of branch
`wf/gramlot-0-2-0-binding` installed in editable mode: the core fixture `avvio`
with `avvio_aux.js` and the example `03_lists` with `Page.css`, mounted at
`/py`, reach `state: 'started'` without console errors under both profiles in
Chromium. An inline-only page runs under the permissive profile and fails under
the strict one.
