# test_invoice_pg: read-only Kajenn / Asqueel qualification

Prepared 2026-10-28; verification completed 2026-10-29. This folder models the
existing local PostgreSQL database. It neither creates nor migrates that database.

## Coverage

All 76 physical tables (40 adm, 19 invc, 17 sys), 808 columns, 76 primary keys,
59 foreign keys and 18 unique constraints are represented in `packages/`.
`catalog.json` preserves the inspected catalog, including all 642 indexes.
Of these, 94 support constraints; the 548 ordinary indexes contain 247 exact
structural duplicates. Asqueel accepts one declaration per equivalent index
structure, so the model declares 301 ordinary indexes; `equivalent_indexes.json`
preserves the other names. No indexes in PostgreSQL were removed or changed.
This model is intended for querying, not an exact DDL round-trip or migration.

The customer model is `packages/invc/model/customer.py`: 20 physical columns and
19 virtual fields, including relation aliases, correlated invoice aggregates,
formula captions and conditional expressions. Other tables have their complete
physical model; their full application methods and virtual fields are not ported.

Labels and customer virtual declarations originate from the native Asqueel
`examples/test_invoice_pg/{adm,invc,sys}.py` declarations. The original customer
Python score method adds 5 to 10 when email is nonempty. Since the inspected
Asqueel runtime does not execute pyColumn, this local customer model expresses
that same rule as a SQL CASE formula. No Asqueel source was modified. This is a
bounded local integration adaptation under the owner's authorization, not a claim
that Asqueel supports every legacy model behavior.

## Run

Use the dedicated adapter environment paired with the selector core worktree.
Install the PostgreSQL driver with `python -m pip install 'asqueel[postgresql]'`
if it is absent. From the adapter root:

```sh
.venv/bin/python -m gramlot_py_server.gallery.application.test_invoice_pg.verify
.venv/bin/python -m gramlot_py_server.gallery.application --port 61404
```

Open `http://127.0.0.1:61404/`. The Python page uses Gramlot dbSelect and dbComboBox,
Kajenn RPC and AsqueelSelect querying the existing customer table. Selection state
is local to the page. Search uses account_name and displays display_name, suburb
and state_name; selected fields also include the invoice count. The provider only
exposes its declared fields, not access tokens or banking fields.

The page is owned by gramlot-examples/application; this adapter owns the model and service. `configure.py` uses local PostgreSQL authentication with dbname=test_invoice_pg.
Every connection sets default_transaction_read_only=on and statement_timeout=15000.
The service and verification check PostgreSQL's read-only setting. There is no
seed, DDL setup, migration or mutation endpoint. Do not run schema alignment tools
against this existing database as part of this example.

## Evidence

`verification.json` contains counts and statuses, not customer record values:

- All 76 table models build; every physical column is selected with a false
  predicate through Asqueel, verifying the mapping without fetching table data.
- All 39 customer fields execute individually, and a single combined projection
  returns all 39 named fields. One row is inspected in memory; no values are saved.
- 3,200 customers are eligible under the model's normal query policies.
- Real PostgreSQL provider search for b, identity lookup and rejection of an
  unexposed access_token projection pass.
- In-app browser: dbSelect b returns real customers and selection populates locality,
  state and invoice count. dbComboBox preserves Arch after Enter/Tab and accepts
  an explicitly chosen customer. This is not a full browser/engine matrix.

Broader selector semantics and automatic legacy metadata remain tracked in GC-315
and Asqueel issue #63. This qualification does not assert production performance,
full legacy parity or owner visual acceptance.

## Reproduce the local model

`tools/build_from_catalog.py` reads the saved catalog and native declarations;
it does not connect to PostgreSQL. It overwrites the generated model/configuration
files in this folder, preserving the read-only connection configuration:

```sh
.venv/bin/python src/gramlot_py_server/gallery/application/test_invoice_pg/tools/build_from_catalog.py \
  --native-source /path/to/asqueel/examples/test_invoice_pg
```

`provenance.json` records source hashes for this snapshot. Catalog files contain
schema metadata only; no database row export is included.
