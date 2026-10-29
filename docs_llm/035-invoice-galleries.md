# 035 · Base database gallery

Document ID: **GP-035**.

> Local integration candidate. These changes are not a published release.

<a id="gp-035-005"></a>
## 005 · Responsibilities

Block ID: **GP-035-005**.

Base pages, catalog and dataset specification belong to
gramlot-examples. This package supplies native Asqueel, SQLAlchemy and Django
providers, models and launchers. Core supplies the selector widgets and endpoint
contract; it does not import an ORM. The Base gallery uses the current shared HTTP
adapters and gallery staging, including collection caching and PageStore exports.
Only the collections declared by each page are activated.

The provider's register/select contract is separate from host database lifecycle
management. Applications own the shared database/engine; each request owns its
session/connection. Django runs synchronous page/ORM methods through the existing
thread-sensitive invocation seam. It does not disable Django async-safety checks.

<a id="gp-035-010"></a>
## 010 · Install the local candidate

Block ID: **GP-035-010**.

Build the matching core and examples browser assets first, then wheels for core,
examples and this package. Install those three local wheels into one fresh Python
environment. Install the adapter extras kajenn, uvicorn, django, gallery and
postgresql there. Do not use old editable checkouts as a substitute for package
qualification. No package is published by this procedure.

First-party dependencies are refreshed without pins. PostgreSQL uses normal
libpq environment/service configuration; do not put credentials in these files.
The postgresql extra supplies the three ORMs/drivers used by this local trial.
It is not a core dependency or a claim of equivalent behavior across all engines.

<a id="gp-035-015"></a>
## 015 · Prepare and verify Base data

Block ID: **GP-035-015**.

The source test_invoice_pg remains database-enforced read-only. Base retains all
rows but only 21 physical columns across state, customer, invoice, product and
invoice_row. Its fixed specification is gramlot_examples/base/model.json.

For a missing copy only, run the following with the selected backend (asqueel,
sqlalchemy or django):

```sh
python -m gramlot_py_server.gallery.base.copy_dataset --backend asqueel
```

This creates only gramlot_base_asqueel, gramlot_base_sqlalchemy or
gramlot_base_django. It refuses an existing target and never drops a database.
The source is read in one repeatable snapshot. Selected values stream directly
between connections; no record dumps are written. Counts, ordered value digests
and foreign-key relations are checked before committing the copy.

For existing copies, use only verification:

```sh
python -m gramlot_py_server.gallery.base.copy_dataset --backend asqueel --verify-only
python -m gramlot_py_server.gallery.base.verify --backend asqueel
```

Repeat for sqlalchemy and django. All runtime connections are read-only too.

<a id="gp-035-020"></a>
## 020 · Open the galleries

Block ID: **GP-035-020**.

Run each command in its own terminal in the installed environment:

```sh
python -m gramlot_py_server.gallery.base --backend asqueel --port 61401
python -m gramlot_py_server.gallery.base --backend sqlalchemy --port 61402
python -m gramlot_py_server.gallery.base --backend django --port 61403
```

Open the corresponding localhost port. Base adds its customer lesson to the
ordinary gallery. Open the lesson
in the existing gallery shell with Example, Explanation and Code tabs.
The launchers bind to loopback; Remote Edit is disabled. They do not deploy a site.

Base uses Kajenn/Asqueel, Uvicorn/SQLAlchemy or Django/Django ORM respectively.
No PYTHONPATH override to another checkout is needed.

<a id="gp-035-025"></a>
## 025 · Coverage and limits

Block ID: **GP-035-025**.

The three Base copies contain 8 states, 3,200 customers, 256 invoices,
1,695 products and 806 invoice rows. Local integration checks compare all values
and four relations, all three native models and 17 selector cases per provider.
They also compare every customer/state projection against an independent LEFT JOIN.

The Application/Invoice launcher and complete application model are excluded
from this candidate by the owner's 2026-10-29 scope correction. They remain on
`codex/invoice-local-preserved-20261029` for later work. The existing source database
is only used to prepare or verify the dedicated Base copies; its complete model
is not required by this release.

Unit/adapter tests, real database checks and browser
checks are distinct evidence; none alone constitutes full legacy parity.

<a id="gp-035-030"></a>
## 030 · State-name projections

Block ID: **GP-035-030**.

Base uses one Python page. The runner supplies provider-specific selector_parameters:
Asqueel requests @state.name; SQLAlchemy uses an outer-join state_name projection;
Django uses a native F('state__name') annotation. Null related values are retained.
There is no per-row lookup. No additional physical column is copied.

<a id="gp-035-035"></a>
## 035 · Auxiliary fields and templates

Block ID: **GP-035-035**.

With Asqueel, auxColumns='@state.name' resolves directly through the model on each
request. It needs neither an aliasColumn nor registration of each auxiliary field.
The compiled result name is _state_name, so selected__state_name='.state_name'
writes it into the page Data. Invalid model paths remain errors. SQL expressions
from the client are refused. Other providers accept their explicitly exposed
native projections; Gramlot does not translate a common relation language.

Responses retain rows, identifier and caption. auxColumns adds ordered columns
and headers. Template placeholders such as {display_name} and {_state_name} are
literal record text inside sanitized HTML; placeholders in attributes are refused.
Template presentation takes precedence over the auxiliary-column layout. Selected
fields and template fields are requested automatically. dbComboBox keeps free text
until explicit suggestion navigation/selection; dbSelect stores a record identity.
