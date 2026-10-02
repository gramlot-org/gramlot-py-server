# Integration architecture

Document ID: **GF-010**.

[Expanded version](../docs/010-architecture.md).

<a id="1-product-boundary"></a>
<a id="gf-010-005"></a>

## 005 · Product boundary

Block ID: **GF-010-005**.

Gramlot constitution separates host/DB adaptation. FastAPI owns HTTP, context,
invocation and asset delivery. Core owns declarations, hosting contracts,
transport and JS. Applications use Source/Data/bindings/services; no local bypasses.

<a id="2-current-implementation"></a>
<a id="gf-010-010"></a>

## 010 · Current implementation

Block ID: **GF-010-010**.

`native_html` adapts FastAPI requests to clean `gramlot.server.Host`, serving
packaged runtime plus page/main/source/close routes. Historical `application`,
`runtime` and `genropy` modules use PoC hosting/transport APIs and are outside
native 0.1.0. The native host has no database dependency.

<a id="3-database-ownership-and-open-work"></a>
<a id="gf-010-015"></a>

## 015 · Database ownership and open work

Block ID: **GF-010-015**.

Areas: common/fake/genropy/sqlalchemy; SQLite is a SQLAlchemy backend. Shared code
belongs in core/POC. SQLite exists in POC's `contrib/sqlalchemy/sqlite.py`, not here.
Temporary legacy placement is acceptable for preview. FastAPI Genropy separation,
portable operations/capabilities/lifecycles remain open. Prior design is not a final
API; passing POC tests does not establish all host/backend compatibility.

See [SQLAlchemy scope and status](035-sqlalchemy.md) for the current read-only SQLite
experiment, its location in the core POC, and the difference between checkout
capabilities and the installed preview wheel.
