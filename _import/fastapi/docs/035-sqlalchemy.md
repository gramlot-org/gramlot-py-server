# SQLAlchemy: provisional SQLite profile

Document ID: **GF-035**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-fastapi/blob/main/docs_llm/035-sqlalchemy.md).

<a id="1-run-the-example"></a>
<a id="gf-035-005"></a>

## 005 · Run the example

Block ID: **GF-035-005**.

From this repository's checkout, in an activated virtual environment:

```sh
python -m pip install '.[sqlalchemy]'
python examples/sqlalchemy/serve.py
```

Open <http://127.0.0.1:8000/page/index/>. The Python-authored page shows a
`dbSelect` field with three synthetic customers. Search for Alice, Bruno or Carla;
press Arrow Down to open the results and Enter to select one. The bound identity
and caption update together. The initial identity
is resolved to its caption through the same database service.

The script creates a temporary database before starting the host. The running
application opens it read-only. Shutdown closes the handler and removes the
temporary directory. This is an experimental example, not a persistent database.

<a id="2-configure-an-existing-database"></a>
<a id="gf-035-010"></a>

## 010 · Configure an existing database

Block ID: **GF-035-010**.

```python
from contextlib import asynccontextmanager

from gramlot.contrib.sqlalchemy import SqliteDbHandler, TableConfig
from gramlot_fastapi import GramlotApplication

handler = SqliteDbHandler("customers.sqlite", {
    "customers": TableConfig("customer", "id", "name"),
})

@asynccontextmanager
async def lifespan(app):
    try:
        yield
    finally:
        handler.close()

app = GramlotApplication("my_app", db_handler=handler, lifespan=lifespan)
```

The database must already exist. Here the logical name `customers` maps to the
physical table `customer`, with primary-key column `id` and text column `name`.
Only configured tables are exposed. Use synthetic or appropriately authorized
data: this minimal profile does not implement user-specific row permissions.

For an existing FastAPI application, use
`mount_gramlot(app, "my_app", db_handler=handler)` and close the handler in that
application's lifespan. The caller owns the handler; mounting or stopping a
Gramlot page collection does not close a potentially shared handler.

<a id="3-declare-a-page"></a>
<a id="gf-035-015"></a>

## 015 · Declare a page

Block ID: **GF-035-015**.

In `my_app/pages/index.py`:

```python
from gramlot.database import DbPageMixin
from gramlot.page import WebPage

class Page(DbPageMixin, WebPage):
    def main(self, root):
        root.data("customer", None)
        root.dbSelect(dbtable="customers", value="^customer", lbl="Customer")
```

`DbPageMixin` precedes `WebPage` and registers `dbhandler.dbselect`.
FastAPI attaches the configured handler to each fresh page instance. Pages that
do not use this mixin are unaffected. A database page without a configured handler
fails with an explicit configuration error.

The browser calls the registered Data endpoint, which FastAPI dispatches to a
worker thread. The core handler acquires a connection for each operation and
returns it on success or failure. Results are ordinary records, not live cursors.
Synchronous page methods can also call `self.dbhandler.dbselect(...)`; do not
perform blocking database calls directly inside async page methods.

The host depends on the generic `DbHandler` contract, not on SQLAlchemy.
No separate SQLAlchemy page mixin is needed for this minimum interface.

<a id="4-ownership-and-limits"></a>
<a id="gf-035-020"></a>

## 020 · Ownership and limits

Block ID: **GF-035-020**.

The shared `DbHandler`, `DbPageMixin`, `SqliteDbHandler` and `TableConfig`
come from the pinned experimental Gramlot core wheel. Database logic remains in
`gramlot.contrib.sqlalchemy`; this repository supplies FastAPI wiring and examples.
The local core SQLAlchemy source directory was untracked at the 2026-09-16 audit;
wheel availability does not imply published GitHub source.

Plain installation requires neither SQLAlchemy nor Genropy. The `sqlalchemy`
extra installs SQLAlchemy 2.x. Tests verify the profile against the pinned core
package as well as the development checkout.

Supported operations are identity lookup and bounded prefix search, with substring
fallback if no prefix matches. Search text is literal; case-insensitive matching
uses Unicode casefold. Tables require a single string/integer primary key and a
text caption. Connections use SQLite read-only mode.

This is not a general CRUD or ORM interface: writes, transactions spanning calls,
migrations, model-derived forms and other database dialects are not supplied.
The broader Gramlot database contract remains provisional; see
[server/database direction](040-server-and-database-integration.md).
