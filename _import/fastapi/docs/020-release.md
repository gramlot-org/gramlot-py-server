# Native HTML release preparation

Document ID: **GF-020**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-fastapi/blob/main/docs_llm/020-release.md).

<a id="1-status-and-dependency"></a>
<a id="gf-020-005"></a>

## 005 · Status and dependency

Block ID: **GF-020-005**.

The native FastAPI implementation uses the clean Gramlot **0.1.0** wheel and
the adapter's `NativeHtmlApplication`/`mount_native_html` APIs. The adapter
currently has its own development version; it need not equal the core version.
Build adapter wheels locally and install them with the locally prepared core
wheel. Neither a FastAPI wheel nor the clean core 0.1.0 is claimed published to
a registry. The older 0.1.5 wheel and the `gramlot-fastapi serve` command belong
only to the historical PoC profile, outside this release.

<a id="2-build-and-verify"></a>
<a id="gf-020-010"></a>

## 010 · Build and verify

Block ID: **GF-020-010**.

Run focused native protocol tests, the native import/star-import check and a
strict Sphinx build against clean 0.1.0 using `scripts/check.py`.
`verify_installation.py` remains a historical PoC probe, outside the native gate. Build all three Python adapter wheels and the Hello World wheel; then create a
separate Python 3.11+ consumer environment:

```sh
python -m venv temp/consumer
temp/consumer/bin/python -m pip install \
  /path/to/gramlot-0.1.0-py3-none-any.whl \
  /path/to/gramlot_fastapi-*.whl /path/to/gramlot_flask-*.whl \
  /path/to/gramlot_genro_asgi-*.whl /path/to/gramlot_example_app-*.whl
temp/consumer/bin/python -m gramlot_example_app.server.fastapi
```

On Windows use `temp/consumer/Scripts/python.exe`. Open
<http://127.0.0.1:8000/>. Native protocol tests cover the bounded API; the
historical `verify_installation.py` probe exercises PoC APIs and is not a
0.1.0 acceptance check. Use the installed Hello World launcher for the native
page and browser path.

<a id="3-manual-distribution-gate"></a>
<a id="gf-020-015"></a>

## 015 · Manual distribution gate

Block ID: **GF-020-015**.

Record the exact wheel filenames, versions, checksums and source revisions of the
core, all adapters and example used in an acceptance run. Delivery by GitHub
archives or a registry is an owner decision, separate from local readiness.
Do not infer publication from a local wheel build or source tag. No automatic
publishing workflow is added here.

<a id="4-architecture-limits"></a>
<a id="gf-020-020"></a>

## 020 · Architecture limits

Block ID: **GF-020-020**.

Server and database adapters are independent responsibilities. The native 0.1.0
profile includes no database. SQLite and Genropy integrations remain PoC
experiments; they require separate migration and review.


Native release checks (2026-09-24): `python scripts/check.py` now runs Ruff,
the native protocol tests and documentation builds against the clean core. CI
builds core from its maintained main branch with floating dependencies. The
retained legacy tests and PoC installation probes remain separate historical
coverage; they are not executed as native 0.1.0 acceptance checks.

Native hooks use the active Python environment with the clean core and adapter
dev/docs dependencies installed. First-party dependency lockfiles are excluded;
missing native imports fail collection rather than skipping the protocol suite.
