# gramlot-flask: initial scope

## Recorded owner request — 2026-09-16

Set up a separate `gramlot-flask` repository using the same system as
`gramlot-fastapi` and `gramlot-genro-asgi`. Keep Flask hosting independent from
SQLAlchemy database access. The repository is a sibling under the canonical
`/Users/gporcari/Sviluppo/gramlot` workspace.

## Delivered scaffold

Package namespace, Apache 2.0 notices, development metadata, Git hooks, mandatory
lint/documentation checks, conditional behavior tests, package verification in CI,
Sphinx with the classic Read the Docs theme and Gramlot logo, paired guides with
GFL stable identities, and Read the Docs configuration. No external hosting setup,
package publication or deployment is part of this scaffold.

References inspected: `gramlot-genro-asgi` commit `db1fd06` (layout and tooling),
`gramlot-fastapi` commit `17c2698` (host/database separation), and the Gramlot
constitution sections 2, 3, 7, 8, 9 and 10. No PoC runtime code is copied.

## Ownership

The adapter will depend on Flask and an explicitly selected Gramlot runtime; the
core must not import Flask. Shared runtime delivery, page services and database
contracts belong to Gramlot. Flask request contexts, registration, responses,
error mapping and lifecycle integration belong here. SQLAlchemy remains a separate
optional database choice; plain hosting must neither install nor import it.

## First bounded implementation

1. Inventory accepted core contracts and separately identify experimental PoC
   evidence. Select and record an available runtime version and provenance; do
   not label a PoC dependency as the consolidated core.
2. Define the Flask integration surface, URL prefix, application isolation,
   request context, resource delivery and error behavior before claiming an API.
3. Implement one Python-authored Gramlot page using shared browser assets and
   services, with no application-local DOM/event/request substitutes.
4. Verify page delivery, safe resource paths, service dispatch and errors, cleanup,
   multiple Flask applications, WSGI hosting and installed-wheel use.
5. Add a bounded SQLAlchemy example reusing the existing data contract, with
   explicit handler/session ownership. Verify plain hosting without SQLAlchemy
   independently from the database profile.
6. Record the implementation, omissions and meaningful test evidence in a bounded
   port/review record, and update both documentation views before acceptance.

## Open decisions and limitations

No public application class, extension factory, CLI, authentication integration,
service protocol, async/streaming/WebSocket support or version compatibility is
established here. No Genropy database profile is promised. Flask's request and
application lifecycle must be reviewed against the actual selected runtime.
The first runtime dependency may require a separate experimental track while
accepted core ports are unavailable. This scaffold does not resolve that choice.
