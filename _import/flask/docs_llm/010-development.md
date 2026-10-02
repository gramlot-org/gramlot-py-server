# 010 · Development

Document ID: **GFL-010**.

[Paired view](../docs/010-development.md).

<a id="gfl-010-005"></a>

## 005 · Local checks

Block ID: **GFL-010-005**.

Native 0.1.0: run `python -m pytest -q tests/test_native_html.py` against clean
core and strict Sphinx. `python scripts/check.py` runs the complete native gate;
historical Microblog/PoC tests remain separate. Git hooks are optional for local development.

<a id="gfl-010-010"></a>

## 010 · Distribution verification

Block ID: **GFL-010-010**.

Build the adapter wheel and install it with clean core 0.1.0 and the other
local host wheels in an isolated consumer. Launch Hello World Flask and verify
`/`. Older demo CI checks cover historical PoC APIs; mypy is advisory.

<a id="gfl-010-015"></a>

## 015 · Demo operation

Block ID: **GFL-010-015**.

Historical PoC only: run `uv run gramlot-flask` or `demo --data-dir /path/to/demo --port 8074`. Login demo / gramlot-demo, then Gramlot. New databases get six users, 24 posts, follows and six messages; relaunches preserve data. Ctrl+C releases resources. `serve DIRECTORY` runs PoC pages. Browser QA covers selection, original profiles and login protection.


Native release checks (2026-09-24): `python scripts/check.py` now runs Ruff,
the native protocol tests and documentation builds against the clean core. CI
builds core from its maintained main branch with floating dependencies. The
retained legacy tests and PoC installation probes remain separate historical
coverage; they are not executed as native 0.1.0 acceptance checks.

Native hooks use the active Python environment with the clean core and adapter
dev/docs dependencies installed. First-party dependency lockfiles are excluded;
missing native imports fail collection rather than skipping the protocol suite.
