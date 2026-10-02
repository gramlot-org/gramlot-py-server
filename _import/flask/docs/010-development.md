# 010 · Development

Document ID: **GFL-010**.

[Paired view](../docs_llm/010-development.md).

<a id="gfl-010-005"></a>

## 005 · Local checks

Block ID: **GFL-010-005**.

For native 0.1.0, run `python -m pytest -q tests/test_native_html.py` against
the clean core, or `python scripts/check.py` for native tests, Ruff and strict
Sphinx builds. Historical Microblog/PoC tests remain separate. Enable hooks with `git config core.hooksPath hooks`.

<a id="gfl-010-010"></a>

## 010 · Distribution verification

Block ID: **GFL-010-010**.

Build and inspect the native adapter wheel, then install it alongside clean
Gramlot 0.1.0 and the other local host wheels in an isolated consumer. Launch
the Hello World Flask profile and verify `/`. Older CI checks of demo login,
PoC Source and assets cover the historical profile. Mypy is advisory.

<a id="gfl-010-015"></a>

## 015 · Demo operation

Block ID: **GFL-010-015**.

Historical PoC only: run `uv run gramlot-flask` or `uv run gramlot-flask demo --data-dir /path/to/demo --port 8074`. Open the printed Microblog URL, sign in as demo / gramlot-demo and follow Gramlot. A new database receives six users, 24 posts, follows and six messages; existing data is preserved. Ctrl+C closes host and database resources. Use `serve DIRECTORY` for PoC pages. Test browser selection, original-profile navigation and login protection when changing that integration.


Native release checks (2026-09-24): `python scripts/check.py` now runs Ruff,
the native protocol tests and documentation builds against the clean core. CI
builds core from its maintained main branch with floating dependencies. The
retained legacy tests and PoC installation probes remain separate historical
coverage; they are not executed as native 0.1.0 acceptance checks.

Native hooks use the active Python environment with the clean core and adapter
dev/docs dependencies installed. First-party dependency lockfiles are excluded;
missing native imports fail collection rather than skipping the protocol suite.
