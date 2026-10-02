# SQLAlchemy: provisional SQLite profile

Document ID: **GF-035**.

[Expanded counterpart](../docs/035-sqlalchemy.md).

<a id="1-run-the-example"></a>
<a id="gf-035-005"></a>

## 005 · Run the example

Block ID: **GF-035-005**.

From checkout: install `.[sqlalchemy]`; run `python examples/sqlalchemy/serve.py`.
Open http://127.0.0.1:8000/page/index/. Python dbSelect, three synthetic customers,
temporary database, read-only runtime access, cleanup at shutdown.

<a id="2-configure-an-existing-database"></a>
<a id="gf-035-010"></a>

## 010 · Configure an existing database

Block ID: **GF-035-010**.

Core `SqliteDbHandler(path, {"customers": TableConfig("customer", "id", "name")})`.
Pass `db_handler=handler` to GramlotApplication or mount_gramlot.
Caller owns lifetime and closes handler in FastAPI lifespan. Host does not close
a shared handler. Only configured tables; no per-user row permissions.

<a id="3-declare-a-page"></a>
<a id="gf-035-015"></a>

## 015 · Declare a page

Block ID: **GF-035-015**.

`class Page(DbPageMixin, WebPage)`; declare
`root.dbSelect(dbtable="customers", value="^customer")`.
Core mixin registers dbhandler.dbselect. Host attaches handler to each fresh page.
Missing handler gives explicit configuration error. Plain pages are unaffected.
RPC executes in a worker; connection released per operation, including failure.
Do not make blocking database calls in async page methods.
No SQLAlchemy-specific page mixin: host uses generic DbHandler.

<a id="4-ownership-and-limits"></a>
<a id="gf-035-020"></a>

## 020 · Ownership and limits

Block ID: **GF-035-020**.

Core wheel supplies database contract/SQLite reader; FastAPI supplies wiring.
SQLAlchemy 2.x optional extra; no Genropy dependency.
Local core source was untracked at 2026-09-16 audit; no GitHub source claim.
Tests cover pinned package and development checkout.
Read-only identity lookup, prefix/contains fallback, bounded literal search,
Unicode casefold; single string/int primary key and text caption.
No writes, cross-call transactions, migrations, generated forms or other dialects.
