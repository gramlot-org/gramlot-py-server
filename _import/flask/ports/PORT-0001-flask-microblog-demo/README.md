# PORT-0001 — Flask hosting and Microblog demo

## Scope and status

Implemented experimental host integration, verified locally; consolidated-core
acceptance is not claimed. Owner requested the Flask CLI to start Microblog with
an integration demo. No PoC runtime implementation is copied into the adapter.

## Evidence and dependencies

- Gramlot 0.1.5 experimental wheel, SHA256
  63466802618c8cbd3fed0a83e1072556085a31bd522477dbcfe1122417a26f4a,
  distributed with gramlot-django v0.1.0-preview.1.
- Shared hosting, runtime and SQLAlchemy APIs are consumed from that wheel.
- Microblog a975ef64864354867c88e0ed3a17ba7d17dca752, unchanged app/config source,
  MIT license and provenance bundled. This is third-party host evidence, not a
  new shared Gramlot API.

## Ownership and contract

Flask routes/context/errors/assets belong here. Page discovery, service role
registration, invocation, TYTX, browser runtime and SQLAlchemy selection stay in
Gramlot. Microblog owns its models/session and login; the CLI owns the separate
selector engine and closes it when the server stops. New demo UI uses only Python
Gramlot declarations, bindings, shared dbSelect and remote Source.

## Destination review and verification

The implemented scope follows constitution sections 2, 3, 7, 8, 9 and 10. It
introduces no core dependency on Flask and no duplicate database adapter.
Real client tests cover plain hosting, assets/traversal, typed dispatch failures,
context isolation, session-authenticated access, shared model data and idempotent
fixtures. Installed-package checks exercise both independent installation profiles.
Browser verification found that dbSelect returns string identities; the page now
normalizes decimal identities before querying the integer primary key, with a
regression assertion in the shared-data test.

## Limits and reusable feedback

No core-contract acceptance, production deployment, publishing or general async
transport support. External mail/search/translation/workers are not configured.
The clean core remains non-executable. Keep experimental provenance explicit.
Verify browser-delivered identifier types, not only direct Python calls. Keep
third-party host templates separate from the Python Gramlot interface. Never
promote an integration-specific query helper into a second database adapter.
