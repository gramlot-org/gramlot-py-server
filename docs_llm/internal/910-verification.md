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
