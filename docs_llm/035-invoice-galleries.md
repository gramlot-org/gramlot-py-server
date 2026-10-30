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

The Base source test_invoice_pg_xl remains database-enforced read-only. Base retains all
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

The three Base copies contain 8 states, 3,200 customers, 60,179 invoices,
1,695 products and 410,429 invoice rows. Local integration checks compare all values
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


<a id="gp-035-060"></a>
## 060 · State-dependent selectors (local trial)

Block ID: **GP-035-060**.

The Asqueel Base runner registers states (code/name) alongside customers and adds
base/asqueel-catalog.json. Its State and customer lesson uses direct legacy
condition and condition_* bindings, with an optional weakCondition preference.
The other runners retain the shared catalog and reject these Asqueel-only options.
Values are bound through native Asqueel sqlparams; server-owned parameters and
selector_ bindings cannot be replaced. Hard-ineligible identity recovery keeps the
registered server predicate and returns the caption with the legacy errors text.
This local trial does not establish authorization for arbitrary client expressions;
public endpoint security review remains separate from normal-flow qualification.

Provider regressions and the read-only PostgreSQL/browser State → Customer trial
passed on 2026-10-29. No public deployment or candidate artifact replacement.


<a id="gp-035-040"></a>
## 040 · XL Base refresh — 2026-10-29

Block ID: **GP-035-040**.

Owner requested switching the Base source to test_invoice_pg_xl and adding a
resident invoice-row Grid. The common specification and all three native models
retain their 21 physical columns and relations. Existing copies were backed up
outside repositories, then refreshed transactionally; counts, ordered value
digests and foreign keys matched the same read-only source snapshot before commit.
The creation command still refuses existing targets. The preserved Application
project and original source databases are unchanged.

The Asqueel gallery adds `82-grid-database/02-invoice_rows`, using native queries
across invoice, customer and product relations. All nine limits through 100,000
are checked by `scripts/verify_invoice_grid.py` against independent physical SQL,
including all projected values, ordering, actual counts and timing bounds.
Query measures joins/execution/fetch; Server includes Query plus Bag construction
and session release. Neither includes serialization, transfer or client rendering.


<a id="gp-035-045"></a>
## 045 · Isolated JSON/JSONL comparison — 2026-10-29

Block ID: **GP-035-045**.

> Historical record: complete-response comparisons retired on 2026-10-30; JSONL is selected for resident invoice loading.

The owner requested separate comparison pages and query, transfer, Bag and search
timings. The local release runner enables them only with `--selection-trials`;
the ordinary gallery retains its existing application and catalogues. Build the
experimental collection in the core with `cd js && node scripts/build-selection-trial.mjs`
and include core `build/selection-trial` in PYTHONPATH alongside the three source
checkouts. No installation or public protocol replacement is required.

`SelectionTrialApplication` adds the local POST route `/gramlot/selection-trial`,
using ordinary page ownership, endpoint and authorization checks. TYTX encodes
one typed record per line; the Kajenn stream batches writes around 64 KiB. Both
comparison pages fully fetch the same read-only Asqueel query before sending.
This tests serialization/transfer, not cursor streaming or server pagination.
The complete-JSON comparison uses ordinary HTTP RPC; the original invoice lesson
retains ordinary WebSocket RPC. No database is changed by these trials.

Verification: 1,000 and 100,000 rows match in every attribute between both HTTP
paths, including Dates and Decimals; abort and unowned requests are rejected.
The runner tests cover enabled and disabled experiment staging. Browser results
are recorded in core GC-375; they are observations, not a release performance SLA.


<a id="gp-035-050"></a>
## 050 · Complete WebSocket comparison — 2026-10-29

Block ID: **GP-035-050**.

> Historical record: complete-response comparisons retired on 2026-10-30; JSONL is selected for resident invoice loading.

Owner discarded the progressive DataBinder variant after per-row collection index
reconciliation dominated the test. Its page, component and protocol tests were
removed; no workaround was adopted. The follow-up optional page 03-websocket-rpc
uses ordinary dataRpc over the existing gallery WebSocket. It calls the same
load_trial_json endpoint as the HTTP comparison, with no adapter protocol change.
The runner only stages the additional page and injects the same read-only service.

scripts/verify_selection_trial_websocket.py checks every row attribute at 1,000
and 100,000 between ordinary HTTP and WebSocket RPC, including Dates and Decimals.
Browser observations include gallery iframe/family routing and codec work; they
are application-path measurements, not isolated wire-protocol benchmarks.

<a id="gp-035-065"></a>
## 065 · Asqueel cached selection — local optional experiment

Block ID: **GP-035-065**.

Enable `serve_release_gallery.py --selection-trials --cached-trial
--cached-threshold 1000` with the existing database/modules/port arguments and the
packaged `gramlot.collections.selection_trial` collection. The threshold applies to the
actual base selection count, capped by the requested limit. Values up to 1,000
load completely; larger ones use native cachedFetch. Filtering below the threshold
does not change the already-created cache mode. Maximum requested limit is 500,000.

The ordinary Base service remains read-only. cached_trial.create_database uses
`gramlot_base_asqueel`, SET ROLE `gramlot_cached_trial`, statement_timeout 120s,
and the native db.options().cachedFetch model option. Schema/catalog setup is
explicit, never performed automatically at server startup.

The owner approved this one-time local preparation (already applied on 2026-10-29):

```sql
CREATE ROLE gramlot_cached_trial NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
CREATE SCHEMA _asql_ AUTHORIZATION gramlot_cached_trial;
GRANT USAGE ON SCHEMA invc TO gramlot_cached_trial;
GRANT SELECT ON invc.invc_state, invc.invc_customer, invc.invc_invoice,
    invc.invc_product, invc.invc_invoice_row TO gramlot_cached_trial;
```

Run only in the explicitly approved local database; do not repeat CREATE statements
against existing objects or extend grants to source databases. PostgreSQL roles
are cluster-level, though these grants apply only to the local copy. Under this
role, `create_database(catalog_only=True)` exposes only the native cache catalog
model. Inspect `session.migration_plan()` before `session.migrate()`; the applied
plan created only `_asql_._asql_cached_fetch` and its owner index. No invoice
migration ran. Effective invoice SELECT is true and INSERT/UPDATE/DELETE false.

Each PageStore generates an unguessable owner; client parameters cannot select a
cache owner or SQL column outside the fixed whitelist. Request start/count and
limit are bounded. Native materialization/sort/search use their own committed
sessions. Closing a PageStore calls cleanup_cached_tables(owner=that_owner).
There is no automatic TTL after process crashes. Source changes are visible only
after Reload; this is a snapshot experiment, not a live database store.

Run local DB verification explicitly with `GRAMLOT_CACHED_TRIAL_DB=1` and
`pytest tests/test_cached_trial.py tests/test_release_gallery.py`. The database
integration case is skipped without this flag; pure protocol/threshold/staging
tests require no prepared cache. Source DB is never modified. The integration
case verifies the XL fixture's 410,429 rows, bounded windows, server search/mixed
sort, switching to resident mode, cleanup and actual-count threshold selection.

<a id="gp-035-070"></a>
## 070 · JSONL resident invoice loading — 2026-10-30

Block ID: **GP-035-070**.

Owner selected JSONL for the timing lesson and floating resident invoice-row Grid.
The local release preview always uses SelectionTrialApplication; --selection-trials
now controls only visibility of the JSONL timing lesson, not route availability.
The Base Asqueel launcher uses the same JSONL-capable application. The core
package includes `gramlot.collections.selection_trial`; no extra PYTHONPATH entry
or standalone collection build is required.
Other Base backends do not mount this invoice lesson and retain their existing host.

The complete JSON HTTP/WebSocket comparison pages and their verification script
are retired. Historical timings remain in GC-375. verify_invoice_grid.py checks
all nine limits against independent SQL; verify_selection_trial_http.mjs decodes
JSONL from both the floating page and timing page at 1000/100000, compares every
attribute and checks cancellation, ownership and old-route 404. Ordinary RPC and
its payload handling are unaffected; no public adapter-wide wire contract changes.
