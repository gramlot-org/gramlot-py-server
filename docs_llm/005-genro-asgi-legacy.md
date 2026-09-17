# 005 · Genro ASGI and GenroPy legacy

Document ID: **GA-005**.

[Expanded counterpart](../docs/005-genro-asgi-legacy.md).

<a id="ga-005-005"></a>

## 005 · Scope and evidence

Block ID: **GA-005-005**.

Owner 2026-09-16: PoC private; implement Genro ASGI + optional legacy GnrApp first;
SQLAlchemy deferred. Clean core is not installable. Reviewed genro-asgi GUI runtime,
genropy-asgi proxy cleanup, FastAPI legacy bridge. genro-legacy-genropy 0.1.0 is only
a namespace. Shared PageRegistry/RuntimeAssets use PoC e2127a1 plus local changes;
experimental, not an accepted core API.

<a id="ga-005-010"></a>

## 010 · Installation and startup

Block ID: **GA-005-010**.

Locked host 0.45.0 / PoC 0.1.5 / Bag 0.21.1. Host 0.46.3 needs Bag >=0.22 while
PoC requires <0.22; no override. Authorized sibling private PoC required through
uv.sources. No anonymous install promise. `uv sync --extra dev --extra docs`, then
`uv run python -m gramlot_genro_asgi examples/plain`. Legacy: separately install
GenroPy; `.venv/bin/python -m gramlot_genro_asgi examples/genropy --instance NAME`.
CLI localhost:8065, /page/hello/ or /page/database/. Legacy runs only SELECT 1.
uv sync may remove unlocked legacy dependencies. Direct composition uses
GenropyApplication(directory, genropy_application=initialized_app) on BaseServer.

<a id="ga-005-015"></a>

## 015 · Contract and ownership

Block ID: **GA-005-015**.

1. Shared flat page discovery; fresh invocations; main/decorated services only;
   Data/Source roles checked.
2. GET HTML/recipes/assets; POST TYTX RPC, one-MiB maximum. Confined assets,
   immutable caching, generic client errors/detailed server logs.
3. Lazy sync-only self.db; init/query/serialization/close/reset in same worker,
   including failures. Return materialized TYTX values, no cursors/lazy Bags.
4. Caller owns GnrApp; no implicit commit/shutdown/migration/instance selection.
   Application owns queries, transactions, permissions and user environment.
5. Plain host imports no GenroPy. Generic database contracts belong in Gramlot;
   this is host lifecycle, not dbSelect/dataRecord. No auth/legacy permissions
   inherited; nonlocal/private access requires host authorization controls.

<a id="ga-005-020"></a>

## 020 · Verification and remaining work

Block ID: **GA-005-020**.

scripts/check.py: lint/tests/strict docs. Tests: BaseServer HTTP, recipes/RPC,
roles/validation/assets, same-thread success/error cleanup, concurrency, async DB
rejection. Optional real GnrApp + temporary SQLite read test (skips without gnr).
No PostgreSQL/model compatibility, inherited permissions, WebSocket RPC,
subscriptions, multiworker, shared DB contracts or SQLAlchemy claimed. No release,
public visibility change or deployment. Classic RTD theme, GA paired IDs/anchors;
legacy getting-started/architecture now mirrored, naming migration pending.
