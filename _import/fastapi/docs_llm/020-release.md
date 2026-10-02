# Native HTML release preparation

Document ID: **GF-020**.

[Expanded version and commands](../docs/020-release.md).

<a id="1-status-and-dependency"></a>
<a id="gf-020-005"></a>

## 005 · Status and dependency

Block ID: **GF-020-005**.

Native FastAPI uses clean Gramlot 0.1.0 through `NativeHtmlApplication` and
`mount_native_html`. The adapter has its own development version. Build and
install local wheels; neither core nor adapter is claimed published to a
registry. The older 0.1.5 wheel and CLI are historical PoC material.

<a id="2-build-and-verify"></a>
<a id="gf-020-010"></a>

## 010 · Build and verify

Block ID: **GF-020-010**.

Run native protocol/import checks, the installed Hello World launcher and strict
Sphinx through `scripts/check.py`. `verify_installation.py` remains a historical
PoC probe outside the native gate. Install the locally built core 0.1.0,
FastAPI, Flask, Genro ASGI and Hello World wheels in a clean Python 3.11+
environment, then launch `python -m gramlot_example_app.server.fastapi` and
open `/`. The old `verify_installation.py` checks PoC APIs, not native 0.1.0.
See expanded commands and Windows path.

<a id="3-manual-distribution-gate"></a>
<a id="gf-020-015"></a>

## 015 · Manual distribution gate

Block ID: **GF-020-015**.

Record wheel versions, checksums and source revisions across core, all adapters
and example. GitHub archive or registry delivery needs an owner decision; a
local build and source tag do not imply publication. No automatic publishing.

<a id="4-architecture-limits"></a>
<a id="gf-020-020"></a>

## 020 · Architecture limits

Block ID: **GF-020-020**.

Server/DB roles are independent. Native 0.1.0 has no database. SQLite and
Genropy are PoC experiments requiring separate migration and review.


Native release checks (2026-09-24): `python scripts/check.py` now runs Ruff,
the native protocol tests and documentation builds against the clean core. CI
builds core from its maintained main branch with floating dependencies. The
retained legacy tests and PoC installation probes remain separate historical
coverage; they are not executed as native 0.1.0 acceptance checks.

Native hooks use the active Python environment with the clean core and adapter
dev/docs dependencies installed. First-party dependency lockfiles are excluded;
missing native imports fail collection rather than skipping the protocol suite.
