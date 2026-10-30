# 910 · Verification

Document ID: **GP-910**.

Derived from a guide of the archived gramlot-uvicorn repository.

[Paired view](../../docs/internal/910-verification.md).

<a id="gp-910-005"></a>

## 005 · Automated checks

Block ID: **GP-910-005**.

The tests live in `tests/<framework>/`, one folder per adapter. Each folder holds
the adapter tests, with the gallery served under `/py`, and
`test_<framework>_project.py`, which creates the project with
`gramlot <framework> new` and serves it. `tests/uvicorn/test_uvicorn_tutorial.py`
serves `examples/`. `tests/test_readme.py`, `tests/test_cli.py` and
`tests/test_gallery.py` need no framework. Each folder runs with its own extra
only:

```sh
python -m pip install -e ".[flask,test]"
python -m pytest -q tests/flask
```

With every extra installed, `python -m pytest -q` runs the whole suite.

The workflow `.github/workflows/tests.yml` runs each framework with its own extra
on Python 3.11 and 3.12 against the core released on PyPI (required job,
coverage uploaded to Codecov with one flag per framework from the 3.12 run).
An informational job runs every adapter against the `main` branch of
`gramlot-org/gramlot` installed in editable mode. Another job validates the
paired guides and builds both documentation views. Two more required jobs use
Playwright Chromium:

- `browser`: `scripts/verify_browser.mjs` serves a pages folder with each
  adapter under `/py` and the strict profile (the 301 of `/py`, an image of the
  `assets` map, the core theme, a Python page that takes its `Logic` from its
  page module); `scripts/verify_gallery_browser.mjs` starts
  `gramlot <environment> gallery` with and without `--mount /py` and opens the
  gallery, every example it links, the `Logic` of c03 and the absence of environment quick-start routes.
- `install`, one run per environment: `scripts/verify_install.py` installs the
  built wheel in a clean virtual environment, runs `gramlot <environment> new`,
  `pip install -r requirements.txt`, the printed start command and
  `gramlot <environment> gallery --mount /py`, and opens each page with
  `scripts/verify_url_browser.mjs`.

```sh
node scripts/verify_browser.mjs "$(command -v python)" "$PLAYWRIGHT_ENTRY" chromium webkit
node scripts/verify_gallery_browser.mjs "$(command -v python)" "$PLAYWRIGHT_ENTRY" chromium webkit
python -m build --wheel -o dist .
python scripts/verify_install.py django dist/gramlot_py_server-*.whl "$PLAYWRIGHT_ENTRY" chromium
```

`python scripts/check_docs.py` validates the paired guides and their
identities, then builds `docs` and `docs_llm` with Sphinx and `-W`.

<a id="gp-910-010"></a>

## 010 · Verification record

Block ID: **GP-910-010**.

> Historical record — the dated PoC checkpoints below precede current-base
> qualification. The final qualification is recorded at the end of this section.

Local PageStore PoC, 2026-10-27, on the isolated codex/websocket-page-stores
branch: the owner authorizes Uvicorn-first work against the local core branch.
Application(..., websocket=True) enables the separate store channel;
existing RPC remains HTTP. The test module declares Page and PageStore as
separate classes, each with main(root). Core owns the recipe and Bag semantics;
this adapter owns ASGI, same-origin/owner validation and subscription routing.

Run the fixture with python scripts/serve_page_store.py 8765 and open
http://127.0.0.1:8765/py/. The environment must contain the local core and adapter
packages, a built core browser runtime and the corrected local Bag JS package
described in the core's GC-250. This is a development fixture, not a release.

Five new ASGI contracts pass. Chromium and WebKit pass
scripts/verify_page_store.mjs with initial snapshots, two binders, the Python
controller's typed total, insertion/deletion, independent HTTP RPC and disposal.
The three failures observed before this change in test_asgi remain: two CSS
expectations omit the current core default theme, and existing gallery staging
does not create a nested output directory used by current gramlot-examples.
The broader HTTP conformance check also exposes two leading-BOM failures,
reproduced against a temporary extraction of the unmodified develop source.
The affected selection has 14 passing tests and these five baseline failures;
all five new ASGI WebSocket tests pass. These failures are not counted as
successful qualification. Documentation pairing and both Sphinx builds pass.

Shared-window extension, owner-authorized 2026-10-27: open /py/family for the
direct/nested iframe fixture and links to connected windows. Only the primary
creates a WebSocket. Same-origin descendants attach their own page IDs, checked
against the same owner; each page retains its own store and HTTP RPC. A page
cannot join two sockets. Detach closes only that page; socket loss closes all
attached stores. A late HTTP close beacon cannot disconnect the primary.

All eleven ASGI PageStore contracts pass. The browser verification script passes
in Chromium and WebKit: one physical socket across direct/nested iframes and
windows opened by the primary or a descendant, isolated state, child navigation,
Source branch removal and window closure. WebKit's missing final postMessage on
context destruction is covered by the core's window.closed lifecycle check.
The full Uvicorn selection also exposes a sixth baseline failure: the tutorial
test's CSS list omits the core default theme. It is reproduced against unmodified
develop, alongside the five earlier failures; the wider suite is not green.

Limits: same-origin windows with retained parent/opener and identical endpoint,
synchronous server controllers/formulas, no fired events, no reconnect/replay/
persistence, no replacement primary election and no Kajenn integration.
General server dataRpc/resolvers and the final lifecycle contract require
subsequent work. No publication or deployment.

Python server-recipe increment, 2026-10-27: the local core activates declared
PageStore recipes automatically through GramlotBuilder, including without
WebSocket configuration. Controller/formula trigger context now distinguishes
node, child and container. All 11 ASGI PageStore tests still pass, as do the
Chromium and WebKit single/shared-window checks. The adapter protocol is
unchanged; its previously recorded baseline HTTP failures remain unresolved.

Shared-channel RPC increment, 2026-10-27: the Uvicorn PoC accepts existing
Source/Data RPC envelopes on its PageStore WebSocket and reuses
GramlotServer.call. Child-page membership and owner checks precede dispatch.
Responses include pageId; concurrent awaitable endpoints can finish out of
order. Binder deltas and RPC responses share the bounded output queue.
Active (pageId, id) calls are unique and limited to 256 per socket. Cancellation,
detach and disconnect cancel pending tasks cooperatively; no automatic retries
or rollback are promised. Synchronous endpoint code still must not block.

All 20 focused ASGI tests pass, covering Source bootstrap, application/auth
errors, concurrent RPC and binder traffic, page-scoped cancellation, foreign
and unattached identities, malformed envelopes, duplicate IDs, capacity and
cleanup. Chromium and WebKit pass declarative dataRpc, reverse completion,
errors and cancellation alongside the existing shared-window scenario,
including RPC from a popup opened by a nested iframe. Both scenarios observe
zero HTTP RPC requests and one physical WebSocket in the primary.

The default browser transport now follows websocketUrl; pages without it keep
HTTP. HTTP close notification is retained for unattached bootstrap cleanup.
This supersedes earlier statements here that RPC remains HTTP-only in the PoC.
The ordinary HTTP route remains available and retains its existing tests.
The six baseline failures of the wider Uvicorn suite are still outside this
increment. No Kajenn integration, reconnect, replay, persistence or publication.

Unified family qualification, 2026-10-27: the local core now uses one
FrameMessages registry and gramlot:message protocol for publications and the
server channel. The adapter's ASGI wire protocol is unchanged. Chromium and
WebKit verify direct-child registration, publication to a popup and back to
its opener, binder/RPC coexistence, removal of an iframe branch, closure of an
intermediate popup and its child, and native primary closure with descendant
popups under both iframe and popup parents. The browser context is explicit:
closing the primary does not implicitly close every page in the test context.
The core separately verifies the same family lifecycle without WebSocket and
checks that a non-Gramlot window opened by the primary remains open.
The earlier separate window handshake and disconnect-only popup behavior are
superseded by this owner-requested unification.

PageStore topic publication increment, 2026-10-27: op=publish uses the existing
shared socket and neutral GramlotServer.prepare_publish dispatcher. The sender must
belong to the channel. An omitted targetPageId addresses its own PageStore; an
explicit target can belong to another socket, but must have the same owner.
Controllers/formulas declare subscribe_<topic>; publish returns an acknowledgement;
their Bag changes use ordinary binder delivery. No browser-side target topic
delivery or retained topic broker is implied.

All 34 ASGI channel tests pass, including cross-socket same-owner delivery and
rejection of foreign/missing targets, forged senders and malformed payloads
before target mutation. Chromium and WebKit exercise the Python-authored
publication button, nested sender identity and publication between independent
primaries in both directions, with results observed through binders and no
HTTP RPC fallback. The six previously established wider HTTP baseline failures
remain outside this increment.

Owner correction, 2026-10-27: rejected publications affect only their message;
the sender receives "ok" or a structured error through the existing correlated
RPC response envelope. id identifies the publication, pageId routes its result
back to the sender, and optional targetPageId only selects the destination.
Owner's subsequent "non facciamo mai wait", confirmed by "ok", supersedes
completion acknowledgement: ok confirms validation and acceptance. The adapter
awaits ASGI send before invoking the prepared subscribers. Invalid payloads and
refused destinations return errors; later subscriber failures are logged without
a second response or channel closure. No rollback or wait option is added.
Controllers remain synchronous on the event loop. The result is not a controller return
value or a database commit guarantee. Channel identity and transport errors
remain separate. Chromium and WebKit verify acknowledgements and foreign-owner
rejection from nested popups and independent primaries, with subsequent RPC,
binder and publication traffic still working. Logs:
/private/tmp/gramlot-publish-ack-asgi.log and
/private/tmp/gramlot-publish-ack-browser.log.
Acceptance-only verification: a send-barrier test proves subscribers have not
started while acknowledgement transmission is suspended. Chromium and WebKit
also verify ok followed by a subscriber exception, with RPC and binders still
working from primaries and nested popups. Current logs:
/private/tmp/gramlot-publish-accepted-asgi.log and
/private/tmp/gramlot-publish-accepted-browser.log.
No release or publication was performed.


Local verification, 2026-10-02, on Python 3.12 in a clean virtual environment
with every extra installed: the full suite passes, 30 tests, with `gramlot`
0.2.1, `kajenn` 0.1.0, Django 6.1.1, Flask 3.1.3, FastAPI 0.142.2 and Uvicorn
0.54.0. The same day each example, started from its folder with the server
named in its docstring on a chosen port, answered 200 on `/hello`
(`/pages/hello` for Kajenn). The FastAPI example was started with
`uvicorn app:app`. No browser was run for this package.

Local verification, 2026-10-04, for 0.2.2 with `gramlot` 0.2.5,
`gramlot-examples` 0.2.5, `kajenn` 0.1.0, Django 6.1.1, Flask 3.1.3, FastAPI
0.142.2 and Uvicorn 0.54.0:

- the full suite passes, 69 tests, on Python 3.12.9 and 3.11.11;
- Playwright 1.63.0 with Chromium 153.0.8010.12 and WebKit 26.6:
  `verify_browser.mjs` 20/20 and `verify_gallery_browser.mjs` 20/20 (five
  environments, with and without `/py`, 34 examples under `/py`);
- `verify_install.py` for the five environments from the built wheel, with
  `--port 8123` because port 5000 is taken by AirPlay Receiver on macOS; Flask
  also without `--port`, with its printed command on port 8000.

The CI run 37184570774 of the branch `feat/gramlot-command` (2026-10-04) passed
the jobs `browser`, `install` (five environments), `repository`,
`documentation`, `core-main` and `published-core` on 3.12, and failed
`published-core` on 3.11: the theme `README.md` was `application/octet-stream`
there. Commit `155aa63` fixed it with `THEME_MEDIA_TYPES`.

Local verification, 2026-10-05, for 0.2.3 with `gramlot` 0.2.6,
`gramlot-examples` 0.2.5, `kajenn` 0.1.1, Django 6.1.1, Flask 3.1.3, FastAPI
0.142.2 and Uvicorn 0.54.0:

- the full suite passes, 74 tests, on Python 3.12.9 and 3.11.11; `ruff check`
  and `mypy src` pass;
- Playwright 1.63.0 with Chromium and WebKit: `verify_browser.mjs` 20/20 and
  `verify_gallery_browser.mjs` 20/20;
- `verify_install.py` for the five environments from the built wheel, with
  `--port 8123`, in Chromium.


Local database-selector development verification, 2026-10-18: connected core and
Python server sources, SQLAlchemy 2.1.5 with SQLite. Server suite: 117 passed,
including registered projection/filter boundaries and the environment catalog.
The five gallery fixtures now activate the same inputs/layout collections as
run_gallery. Live Python gallery checks cover typed keys, key resolution, dependent
filters, dedicated methods, invalid drafts, free text and sole-candidate selection.
GP-025 documents the unreleased increment; core GC-070 §1425 records combined
qualification. Browser/SQL tests do not claim support for other database engines.


Development verification, 2026-10-20 — Gallery staging now creates parent directories for filesystem routes and stages index_aux.js re-exporting the ordinary gallery Logic. The Python gallery/staging and core index checks pass (34 focused tests), and live Chromium/WebKit checks pass under Uvicorn for nested directories, own index pages and retained tabs.


<a id="gp-910-015"></a>

## 015 · Numbered gallery paths — 2026-10-21

Block ID: **GP-910-015**.

Owner explicitly authorizes connected catalogue and staging changes: “Sì, adegua anche le integrazioni”. Gallery catalogues require the physical family `folder`; each executable route is staged at its nested `url`, with its companions. Catalogue keys remain lesson identities. Hosted carousel links include the mount path; offline links include the route depth. Numbered path segments, including `00-index`, are supported by the static exporter without accepting traversal or empty segments. Markdown directory descriptions are supplied by the examples navigation and rendered by the gallery. No core loader change, route alias, release or deployment is included.

Verification: nine gallery catalogue/staging tests pass, including mounted paths. Both documentation builds pass. Live Uvicorn gallery checks confirm numbered navigation, executable and Markdown indexes, nested lesson URLs and retained Python source display.


Intermediate release qualification — 2026-10-21. Owner authorizes tree, pages, gallery and guide only, including the necessary connected integrations. All 126 tests pass. Chromium passes all 84 common lessons under /py and the root gallery/Logic check on Uvicorn, Django, Flask, FastAPI and Kajenn. Both documentation views build without warnings. Database selectors and Genropy experiments are excluded. Package publication is pending at this checkpoint.


Clean-install verification follow-up — 2026-10-21. The wheel installation check now obtains the e01 route from the installed examples catalogue instead of the retired short URL. A fresh Uvicorn virtual environment, generated project and mounted gallery pass Chromium against the published core and examples packages. The same script is exercised for all five frameworks by CI.


Publication receipt — 2026-10-21. Release v0.2.12 passed all required repository and tag checks and is published on PyPI. The five framework matrices, clean wheel installations, generated projects and gallery browser checks pass. Publication workflow: https://github.com/gramlot-org/gramlot-py-server/actions/runs/39575513271 . Hosted gallery promotion has its own deployment receipt.


Coordinated 0.3.17 qualification — 2026-10-26. Owner explicitly requested aligned
publication of the servers with core and examples. All 154 adapter tests pass
against the prepared 0.3.17 candidate; both documentation views build. Gallery
asset tests use the transparent branding path supplied by the core. Remote Edit
remains disabled by default; the Kajenn HEAD Content-Length debt is unchanged.
Registry publication is pending.

PageStore gallery integration, 2026-10-27: the owner explicitly authorizes
preserving PageStore, enabling the experimental Uvicorn channel and staging
current route URLs. The optional PageStore is exported by each generated page
module; nested files follow route.url and index_aux.js loads gallery Logic.
The Uvicorn-only --websocket gallery switch passes the existing adapter option;
other adapters receive no WebSocket option.

44 focused gallery/ASGI tests pass. Chromium and WebKit exercise the additional
gramlot-examples PageStore catalogue through the real tree, code and explanation
panels. Bidirectional edits, customer success, missing-key preservation and
recovery all work with one socket owned by the gallery. Logs:
/private/tmp/gramlot-gallery-stores-tests.log and
/private/tmp/gramlot-page-store-gallery-browser.log. No remote deployment.


Family gallery expansion, 2026-10-27: verify_page_store_gallery.mjs now exercises
the third gramlot-examples lesson: publication from direct/nested iframes and
connected windows with their own PageStores. Chromium and WebKit verify distinct
page identities, isolated success/error outcomes, one socket across all frames
and windows, continued siblings after intermediate closure and recursive popup
closure when the primary gallery closes. No HTTP RPC fallback or console errors.
The core closure correction is owner-authorized and recorded in GC-070.
Log: /private/tmp/gramlot-page-store-family-browser.log.


Cross-page gallery expansion, 2026-10-27: the fourth lesson publishes from a
connected child window to a sibling iframe's PageStore using explicit pageId.
Chromium and WebKit verify sender acceptance versus recipient business outcome,
recipient-only changes, unknown-target and foreign-owner refusal, recovery,
one shared socket and recursive closure. Foreign-owner coverage uses a separate
browser context. Existing binder/family scenarios remain in the same passing run;
no console errors or HTTP RPC fallback. No adapter runtime changes are needed.
Log: /private/tmp/gramlot-cross-page-browser.log.


Publication sender metadata, 2026-10-27: owner explicitly requests "sì aggiungilo
come metadato della publish e aggiorna l'esempio così il controller può sapere il
pageId della finestra mittente". Implemented _subscription_metadata beside the
existing payload context: pageId comes from the validated envelope sender and
remains distinct from the target. Each subscriber receives a fresh mapping;
local/nested publication without metadata gets an empty mapping. Payload cannot
spoof the reserved context. The customer gallery controller writes sender_page_id
on its customer node and the recipient shows it through the ordinary binder.

Verified: 263 core Python tests and 393 subtests pass, with one expected failure;
44 focused adapter PageStore/gallery tests pass. Chromium and WebKit verify the
actual child page ID on success, business error and recovery, recipient-only
changes, authorization refusals, one primary socket and recursive closure.
The broader adapter HTTP/gallery check has three existing unrelated failures:
old CSS expectations (two) and /py/e01 route expectation (one). Prior baseline
is recorded in /private/tmp/gramlot-family-adapter-tests.log; current details in
/private/tmp/gramlot-metadata-adapter-tests.log. No HTTP behavior was changed.
Logs: /private/tmp/gramlot-metadata-core-python.log,
/private/tmp/gramlot-metadata-focused-adapter.log,
/private/tmp/gramlot-publish-metadata-browser.log.
Implementation and verification are complete; owner acceptance is separate.


Server-to-browser publication, 2026-10-27: owner explicitly approves "sì
implementiamola e aggiorniamo l'esempio così il controller del PageStore fa una
publish verso la finestra mittente e lì un datacontroller subscribed la riceve".
PageStore.publish(..., page_id=...) now routes an event to a same-owner browser
page. Omission remains local to the PageStore. Core checks both live pages and
owns only send callbacks; Uvicorn registers the existing primary/child channels.
Page lifetime removes callbacks. The event uses op=publish with no correlation
id and reaches ordinary browser subscriptions through the same family channel.
Subscriber failure is logged without closing the browser channel. No replay,
wait, extra WebSocket or alternate window protocol is introduced.

The gallery's customer controller publishes customer_loaded to the verified
sender; its browser dataController writes a separate notification branch shown
as Server event. The recipient's bound record remains separate from this event.

Verified: 265 core Python tests with 393 subtests pass (one expected failure),
3,793 JavaScript tests pass and the browser runtime rebuild succeeds. The first
JS run used the wrong Python environment, then the freshness check correctly
required rebuilt bundles; the final configured build and full suite pass.
46 focused Uvicorn PageStore/gallery tests pass, including child return events
across one or two primary sockets, acceptance-before-event and live RPC afterward.
Chromium and WebKit verify the actual subscribed controller receives the typed
record only in the sender, retains the same single family socket and preserves
all previous authorization, binder, metadata and closure scenarios.
Logs: /private/tmp/gramlot-reverse-publish-core.log,
/private/tmp/gramlot-reverse-publish-js.log,
/private/tmp/gramlot-reverse-publish-adapter.log,
/private/tmp/gramlot-reverse-publish-browser.log.
Implementation and verification are separate from owner acceptance. Previously
recorded general HTTP baseline failures are outside this bounded change.


Reverse publication metadata, 2026-10-27: owner requests metadata on the
PageStore-to-client event and its display in the child window. The outbound
metadata.pageId comes from the validated source store; the outer pageId remains
the recipient route. PageStoreConnection passes metadata separately into the
existing subscriptions service. Each callback receives its own mapping as a
second argument, and subscribed browser providers expose _subscription_metadata
as a reserved context, including inline scripts and formulas. Payload cannot
override it; nested/local publication receives empty metadata. No public
Gramlot.publish signature change or new protocol is introduced.

The gallery controller writes notification.sender and displays Server event —
PageStore ID. Chromium and WebKit verify this equals the original recipient
iframe's page ID on both successful loads; it differs from the original sender.
The complete existing binder, owner refusal, recovery, one-socket and recursive
closure scenarios pass too. Core: 265 Python tests plus 393 subtests, one expected
failure; 3,794 JavaScript tests and rebuilt runtime pass. Adapter: 46 focused
PageStore/gallery tests pass, with reverse metadata checked across sockets.
Logs: /private/tmp/gramlot-reverse-metadata-core.log,
/private/tmp/gramlot-reverse-metadata-js.log,
/private/tmp/gramlot-reverse-metadata-adapter.log,
/private/tmp/gramlot-reverse-metadata-browser.log.
Implemented and verified; owner acceptance is separate. Earlier general HTTP
baseline issues remain outside this bounded change.


Current-base release qualification, 2026-10-27: all 191 adapter tests pass with
the integrated core; the old HTTP/CSS/route baseline failures are resolved by
alignment with the current shared adapter. The gallery staging test preserves
the separate PageStore class. The full Chromium/WebKit WebSocket fixture and
PageStore gallery pass from clean installed candidate wheels. All five adapters
and their ordinary galleries pass browser checks. Both documentation views build.
Bag JS 0.11.1 is published on npm/JSR; no local dependency patch is required.
The owner authorizes publication and automatic hosted-gallery updates with
"Sì, pubblica e aggiorna le gallery". Registry CI must run after the required
core release is available. Only Uvicorn has WebSocket support in this release.


Dependency publication receipt, 2026-10-27: Gramlot 0.3.19 is published on PyPI
and npm by successful workflow 40593932800. The required core API is now
available from the public registries; rerun the complete adapter release gates
against those packages before consolidating and publishing the adapter.


Public-registry qualification, 2026-10-27: the complete adapter matrix now
passes against published Gramlot 0.3.19, including Python 3.11/3.12, clean
installation of all five frameworks, the shared WebSocket fixture and the
ordinary gallery browser checks. Three initial installs reached stale PyPI
replicas; rerunning those jobs after propagation passed without source changes.
The paired documentation check in GitHub also passes; refresh the external
Read the Docs build before final consolidation.


Kajenn implementation checkpoint, 2026-10-28: the adapter uses Kajenn's native
serve_websocket/WebSocket and connection registry, with handshake authentication
passed to Gramlot RPC. Uvicorn and Kajenn share one _StoreChannel implementation;
the existing owner/origin policy, family routing, snapshots, binders, RPC
cancellation and bidirectional publication metadata are preserved. Both galleries
accept the opt-in --websocket switch. No browser protocol change was needed.

Owner-confirmed db(name)/async_db(name) are implemented on Page and PageStore,
with a backend-neutral host reference and protected _invoke seam in core.
Kajenn registers one call per WebSocket operation, uses its native worker pool
for sync page/controller code and releases sync database handles on that same
thread. An application operation gate serializes live-Bag mutation and HTTP
closure; asynchronous Page methods release it while awaiting. Repeated sync
cancellation drains the worker before releasing the gate or call resources.
No ORM translation, database-name alias or automatic commit was added.

Verification against registry Kajenn 0.7.0 and kajenn-db 0.1.0: core 317 tests and
397 subtests pass, with one existing expected failure, using supported Node 22;
adapter 243 tests pass. Twelve real SQLite checks cover Asqueel, SQLAlchemy and
Django, HTTP/WS access, named databases, binder-triggered and subscribed
controllers, explicit commits, rollback, async access/refusal, closing during
sync work and repeated cancellation. Django async_db remains explicitly refused
by its handler; synchronous access/release thread identity is verified. Shared
channel tests pass in both adapters. Chromium/WebKit pass the complete Kajenn
family fixture; Chromium passes the extracted Uvicorn channel. Both adapter
manuals build. Logs: /private/tmp/kajenn-complete-adapter-tests.log,
/private/tmp/gramlot-kajenn-core-full.log, /private/tmp/kajenn-database-browser.log,
/private/tmp/uvicorn-shared-channel-browser.log, /private/tmp/kajenn-complete-docs.log.

Remaining upstream issue: /private/tmp/check-kajenn-cancel.py reproduces that
Kajenn 0.7.0 WorkPool.run finishes its cancelled await while the executor work is
still active. Native async database cleanup can consequently race in-flight I/O.
The owner has been asked to authorize a bounded Kajenn pool correction and its
tests without publication. No workaround was added for this upstream async issue.
Async I/O cancellation is not claimed qualified until it is resolved. This
increment depends on the matching core changes and is not yet published or
consolidated into the public reference.


Upstream report, 2026-10-28: owner says "fai un issue non so se su kajenn o
kajen db". Filed [Kajenn #89](https://github.com/kajenn-org/kajenn/issues/89),
"WorkPool cancellation can let call cleanup run before executor work finishes".
The event-controlled reproduction on Kajenn 0.7.0 confirms a cancelled await
completes while its worker has not finished; the same pool implementation is
present on upstream main. The report separates that observation from the
potential database-cleanup race; no corruption or data loss was demonstrated.
The remaining upstream work is tracked by this issue. No Kajenn source change
or publication was authorized or performed as part of filing it.


Kajenn/Asqueel gallery verification, 2026-10-28: implemented the owner-authorized
optional customer catalogue in gramlot-examples and its native Kajenn runner in
gramlot-py-server. A dedicated SQLite file is migrated/seeded only when new;
subsequent startup preserves committed changes and deletions. Separate Page and
PageStore classes use existing dataBinder and subscribed controllers. Key changes
load records; saves explicitly commit or roll back, with loaded ID, status and
error in Data. Independent page drafts read other windows' commits on reload;
the last successful save wins. No cross-draft sync or conflict detection is implied.

Verified real reads/saves, missing keys, empty-name validation, duplicate-email
rollback and recovery in Chromium and WebKit. Direct/nested iframes, connected
windows and their descendants share exactly one physical primary WebSocket;
closing a connected parent closes its descendant window. The persistence test
verifies startup does not reseed or overwrite existing data. All 244 adapter tests
pass; examples pass 62 Python tests and 178 subtests, with one existing skip.
Both adapter manuals build; examples documentation validates 111 lessons,
5 paired guides and local links/anchors. Logs: /private/tmp/kajenn-sqlite-gallery-browser.log,
/private/tmp/kajenn-gallery-adapter-tests.log, /private/tmp/kajenn-gallery-examples-tests.log,
/private/tmp/kajenn-gallery-adapter-docs.log, /private/tmp/kajenn-gallery-examples-docs.log.

Local preview: http://127.0.0.1:8768/py/ with demonstration data at
/private/tmp/gramlot-kajenn-demo/customers.sqlite. The optional catalogue requires
the matching development versions, including the unreleased core database API.
Implemented and locally verified; owner review remains distinct from acceptance.
No release, deployment or upstream Kajenn source edit was performed. Kajenn #89
remains the separate async-cancellation dependency; these synchronous controllers
do not exercise or resolve it.


<a id="gp-910-020"></a>
## 020 · Unified local consolidation base — 2026-10-29

Block ID: **GP-910-020**.

The owner-approved local base combines the upstream Kajenn PageStore/WebSocket
and database integration with the Base Asqueel dependent selectors. Invoice is
excluded. Against the integrated core (forms, selectors, prepared collections and
Grid), the full Python server suite passes: 307 tests, including optional Kajenn
database paths. The source environment must include all three repositories on
PYTHONPATH; an older installed adapter is not this checkpoint.

The local preview at http://127.0.0.1:61505/ composes the existing gallery staging
and Kajenn Application APIs. It exposes the common catalogue including Grid,
Base and Asqueel selectors, PageStore/WebSocket and Kajenn database lessons.
Remote Edit is disabled. The Base PostgreSQL connection remains read-only;
the Kajenn database demonstration uses its separate local SQLite fixture.

This checkpoint does not publish packages or deploy the preview. Public release
still requires final consumer/package checks and the client-condition/server
constraint security review. Runner receipts: /private/tmp/gramlot-release-integration-20261029/;
integration verification: /private/tmp/gramlot-grid-integration-20261029/.
<a id="gp-910-070"></a>
## 070 · Processing updates during synchronous recipes — 2026-10-29

Block ID: **GP-910-070**.

Bounded connected work approved by the owner: Data binder requests must reach
the PageStore recipe, and state written during processing must reach the client
before the recipe returns. No wire operation is added. The shared channel has an
independent outgoing writer with serialized socket sends, preserving publication
acceptance before subscriber entry. Uvicorn runs synchronous store operations
serially off the event loop and drains cancelled workers before cleanup. Kajenn
keeps its existing operation and database execution policy.

Shared channel tests cover both hosts, including gated processing over binder
change and publication, feedback delivery before releasing the worker, ordered
final updates, ownership, RPC, cancellation and cleanup. A Uvicorn-specific test
checks worker draining before the next mutation. Protocol conformance passed
on both hosts. The isolated development environment also checks local core chat
integration; package requirements and installed dependency sources are unchanged.
No release or deployment is implied by these local verification results.

Local common-base confirmation: the full 312-test adapter suite passes against
the integrated core, including the five feedback/cleanup regressions. The chat
catalogue works inside the Kajenn gallery iframe at port 61505. Original
chat-feedback-adapter work is preserved; Invoice and public deployment are out
of this integration scope.


<a id="gp-910-075"></a>
## 075 · Resident database Grid limits — 2026-10-29

Block ID: **GP-910-075**.

Owner requested a real database Grid, server timing and nine selectable limits
from 100 through 100,000. Base Asqueel and local release-gallery staging inject
the existing read-only database service into the environment lesson
`82-grid-database/01-customers`. No transport or core database contract changes.

`scripts/verify_customer_grid.py` checks read-only PostgreSQL transactions and
all nine declared limits against physical `invc.invc_customer` rows, comparing
all fields and deterministic order, actual/requested counts and timing bounds.
It rejects undeclared limits. The current table contains 3,200 rows, so limits
of 5,000 or above return 3,200. This is not a large-table performance benchmark.
Run with the Base environment dependencies and matching gramlot-examples installed.
`tests/test_release_gallery.py` passes and checks page staging/service injection.
Browser verification at 61509 confirms selector-driven RPC reload, server metrics
and virtualized scrolling through all 3,200 rows. No release or deployment.


<a id="gp-910-080"></a>
## 080 · XL Base and invoice-row Grid — 2026-10-29

Block ID: **GP-910-080**.

Following the explicit owner request, all three Base copies now derive from
read-only test_invoice_pg_xl. Backups precede transactional replacement; all
selected values, counts and relations match. All three ORM/selector checks pass
(17 selector cases each); Base/release-gallery tests pass (7 tests).
`scripts/verify_invoice_grid.py` verifies every projected field and row order
against independent SQL for all nine limits through 100,000. Native invoice,
customer and product relations supply the displayed fields. Unit price and total
retain the invoice-row Decimal values, not current product prices.

Live browser loads 100,000 actual rows: observed Query 552.31ms, Server 930.23ms.
End reaches ordinal 100,000, zero bottom gap, 20 mounted rows. Quantity/Unit price
multicolumn sorting and whole-selection search/clear work. Search across 100,000
rows can occupy the browser for several seconds; endpoint timing excludes this
client work, serialization and transfer. No core/dependency changes or claim of
instant large-selection filtering. Aggregate evidence is under xl_refresh in
base/verification.json; earlier sections are historical pre-XL results.

Final XL verification: 54 gallery/catalogue/sample tests pass. Rebuilt examples
documentation validates 127 lessons, five paired guides and all local links;
adapter documentation checks also pass.

<a id="gp-910-085"></a>
## 085 · Cached selection qualification — 2026-10-29

Block ID: **GP-910-085**.

Optional Asqueel-only page and limited cache connection implemented. Ten targeted
tests pass (explicit local DB opt-in): native materialization, first/last window,
search, mixed sort, cache disposal, safe sort protocol, configurable actual-count
threshold and optional gallery staging. Browser verifies resident 1,000 and
410,429 cached with 200 rows in the browser, End, zero-match/reset and multi-sort.
Core full suite 1,464 passes with integration venv; targeted final 48 pass.
Single-run materialization/first-window 829.41/981.20 ms; scroll 42.10 ms;
Parks search server/client 119.10/374.70 ms. Not a controlled benchmark.
No invoice writes, source DB changes, dependency edits, release or deployment.

<a id="gp-910-090"></a>
## 090 · JSONL adoption verification — 2026-10-30

Block ID: **GP-910-090**.

JSONL is shared by the resident invoice floating page and timing lesson. Ten
adapter/cache/staging tests pass. Independent read-only SQL matches all returned
attributes for 100, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000 rows; invalid
limits reject. Real HTTP typed decoding agrees across both pages at 1000/100000;
cancellation and unowned page requests reject; retired comparison routes are 404.
Core targeted loader/coordinator tests: 12 pass. No database writes or migrations
are involved in this adoption; cachedFetch integration remains unchanged.
