# 045 · Common Gramlot showcase

Document ID: **GF-045**.

<a id="gf-045-005"></a>
## 005 · Run locally

Run `.venv/bin/python examples/showcase/serve.py` and open
`http://127.0.0.1:8075/page/index/`.

This entry point serves `gramlot.showcase.get_showcase_directory()` through the
normal FastAPI adapter. English lessons, grouped navigation, CSS, source viewing
and Inspector setup live in the shared Gramlot runtime package. FastAPI does not
maintain copies of the lesson code or visual assets. The current development
preview requires the sibling `gramlot-poc` checkout containing that package;
the previously pinned release does not provide this new showcase.

<a id="gf-045-010"></a>
## 010 · Behavior and ownership

Each lesson opens in its own iframe in a closable tab. Switching preserves that
page; closing and reopening starts fresh. The common class supplies the live
container to `main(self, root)` and shows that actual method in CodeMirror.
The Inspector edits only `data_root` and `source_root`. Auxiliary source-viewer
state and tools remain outside those scopes. The right sidebar contains Source and an embedded Inspector in separate tabs,
with a top-edge toggle; the first three lessons are root-level tree leaves. CodeMirror has equal side gutters and uses the shared CDN provider.

The overview introduces the English teaching progression. Nested tree groups
cover bindings, labels, inputs, presentation, layout and validation. Each lesson
introduces a small concept using actual runtime APIs.

<a id="gf-045-015"></a>
## 015 · Verification and other hosts

FastAPI integration tests request every shared page and recipe and verify scoped
Inspector configuration. Shared lesson and shell contracts belong to Gramlot's
tests. This is a local development preview, not a published package or accepted
core port. Python adapters can reuse the same directory; Node.js authoring and
the two standalone variants require their own delivery verification before
cross-host equivalence is claimed. Host-specific apps remain separate examples.

The workshop contains eleven pages: overview, Hello world, live greeting,
reactive labels, input widgets, formatting, formlets, validation, dataFormula, dataController, and dataRpc. Related
widgets share practical forms. A toolbar below the header controls the left
navigation and right Source/Inspector pane, which starts open. At most six
lesson tabs remain open; opening another evicts the oldest opened tab.
The active iframe receives tool visibility through the shared same-origin
`frameChannel` component, including when its recipe initializes after load.
