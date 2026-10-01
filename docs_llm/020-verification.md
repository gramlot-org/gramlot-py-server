# 020 · Verification

Document ID: **GS-020**.

[Paired view](../docs/020-verification.md).

<a id="gs-020-005"></a>

## 005 · Automated checks

Block ID: **GS-020-005**.

`pytest -q tests/test_asgi.py` checks the Python ASGI Page, runtime asset,
main/source/close requests and owner isolation, the mount prefix `/py` on the
`PageBootstrap` document, companion and `Page.css` serving below the pages
folder, and the nonce in both Content Security Policy profiles.

The workflow `.github/workflows/tests.yml` runs the suite on Python 3.11 and
3.12 against the core released on PyPI (required job, coverage uploaded to
Codecov from the 3.12 run) and against the `main` branch of
`gramlot-org/gramlot` installed in editable mode (informational job). A third
job validates the paired guides and builds both documentation views.

<a id="gs-020-015"></a>

## 015 · Verification record

Block ID: **GS-020-015**.

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

Local verification, 2026-10-01, with `gramlot` 0.2.0 installed from PyPI in a
clean virtual environment on Python 3.12: the five tests pass; line coverage of
`gramlot_uvicorn` is 81%.
