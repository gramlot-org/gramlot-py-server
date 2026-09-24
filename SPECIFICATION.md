# gramlot-flask: scope and implementation

## Native 0.1.0 release boundary — 2026-09-23

`mount_native_html` adapts Flask to the clean Gramlot 0.1.0 Host; see
[GFL-025](docs/025-native-html.md). The Microblog demo, `mount_gramlot` and CLI
contract below are historical PoC material, outside native compatibility. Their
imports require modules absent from the clean core. The old wheel provenance
below is historical evidence, not an active 0.1.0 dependency instruction.

## Purpose

Provide Flask hosting for Gramlot, with database choice independent of the host.
The default CLI starts Microblog with an added Gramlot community explorer.

## Implemented experimental contract

- `mount_gramlot(app, directory, prefix="/gramlot", title="Gramlot",
  db_handler=None, access_check=None)` registers HTML, recipe, typed Source/Data
  services and the shared browser assets. Pages are discovered once; each service
  invocation gets a fresh page through Gramlot's shared PageRegistry.
- Synchronous WSGI views bridge to the shared async invocation on the request
  thread. Flask context and ORM sessions remain request-scoped. This is not a
  general ASGI/WebSocket/streaming integration.
- Explicit role/method registration, TYTX content-type and parameter checks apply
  to services. Unexpected failures return a generic error and log server details.
  Public runtime assets are cached immutably; page/service responses use no-store.
- Caller-owned `access_check` runs before all page/recipe/service routes. The demo
  requires the original Microblog login for every data-bearing Gramlot route.
  Typed POSTs do not accept browser form content types; no cross-origin access is
  enabled. This is not a general-purpose authentication or CSRF middleware API.
- `gramlot-flask` defaults to `demo`; `demo --data-dir ... --port ...` selects a
  separate persistent SQLite database. The CLI binds to 127.0.0.1, disables debug
  and reload, and releases database resources at shutdown.
- `serve DIRECTORY` hosts ordinary Gramlot pages without the demo/database extras.

## Demo ownership

Microblog app/config source at revision a975ef64864354867c88e0ed3a17ba7d17dca752
is bundled unchanged under its MIT license. A wrapper supplies configuration,
fixtures and a navigation overlay. No upstream private data or database is copied.
The default six accounts use password `gramlot-demo`; they are demonstration data.

The Gramlot page uses Source, Data bindings, dbSelect and remote Source. Its
read-only selector reuses Gramlot's SQLAlchemy SqliteDbHandler. Profile and post
services query Microblog's existing ORM models within Flask's request context;
they do not implement another database adapter. Microblog owns ORM session cleanup;
the CLI owns SqliteDbHandler shutdown. The page exposes public profile/post fields,
not email addresses, credentials or private messages.

## Runtime provenance and review

The adapter depends on the checksummed experimental Gramlot 0.1.5 wheel distributed
with the Django preview. That wheel provides shared page dispatch, authoring,
transport, SQLAlchemy selection and packaged browser assets. It is not an accepted
consolidated core release. The clean core's architectural constitution and port
protocol remain authoritative. See ports/PORT-0001-flask-microblog-demo/README.md.

## Limits and open work

No production deployment, package publication or external documentation setup is
included. External Elasticsearch search, translation, password-reset email and
background exports are unavailable in the demo. Original templates use CDN assets.
Full Microblog feature coverage and cross-database portability are not claimed.
The explorer shows at most 20 latest posts per user; it does not edit records.
Microblog's conventional `app` and `config` imports require a dedicated demo
process. The reusable Flask adapter has no such import restriction.
No general Live Object Tree semantics, capability protocol or dataRecord contract
is introduced. Adoption by the consolidated core needs separate destination review.
