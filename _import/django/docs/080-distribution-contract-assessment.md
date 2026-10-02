# 080 · Phase 1 assessment: core and Django adapter distribution contract

Document ID: **GD-080**.

Date: 2026-09-15

**Historical pre-implementation assessment.** The public hosting/transport
interface and adapter migration have since been implemented locally. The
[release procedure](065-release.md) tracks the remaining publication gates.
The observations and proposals below describe the original audit snapshot.
Scope: release baseline and the supported interface between `gramlot` and
`gramlot-django`. This assessment records the current working trees; it does not
authorize publication and does not treat earlier migration results as release
acceptance.

<a id="gd-080-005"></a>

## 005 · Status

Block ID: **GD-080-005**.

Phase 1 is **not ready to close**. The extracted Django adapter works against the
local core, but its production code imports two private core modules and calls a
private registry method. The concurrently extracted FastAPI adapter uses the same
private boundary. A supported core interface must therefore land before either
adapter candidate is selected.

No releasable commit set can be named from the current HEADs:

| Repository | Branch and HEAD inspected | Working-tree fact |
| --- | --- | --- |
| `gramlot` | `develop` at `e2127a1582cdcd62c21b2612741576527aabbfc3` | Dirty; includes the Django removal, FastAPI compatibility work, runtime changes and substantial unrelated work. |
| `gramlot-django` | `develop` at `e4dbcb6304bd5d05b73f5d2d2fe3dd80f433ed55` | Dirty; the extracted adapter implementation and its main behavior test are untracked. |
| `gramlot-fastapi` | `develop` at `543a67887210fa2a6916ac53c6da0866d3da814c` | Dirty; the extracted adapter implementation and tests are untracked. |

These hashes identify the inspected baselines, not candidate release commits.
Unrelated working changes must remain out of the phase commits.

<a id="gd-080-010"></a>

## 010 · Verified ownership boundary

Block ID: **GD-080-010**.

Gramlot owns stateless page authoring and method roles, page discovery and
invocation, TYTX transport, the shared store, startup-document generation,
browser-manifest interpretation and the packaged browser payload.

`gramlot-django` owns Django URL composition, request and response handling,
middleware, CSRF, authentication and permissions, ORM projection and
transactions, Django templates, and Django file responses. Generic `WebPage`,
service invocation or browser assets must not be copied into this repository.

The current code follows that responsibility split in substance. The defect is
that the shared host facilities are exposed only under
`gramlot.contrib._shared`, whose package docstring explicitly calls them
internal.

<a id="gd-080-015"></a>

## 015 · Exact core surface consumed by `gramlot_django`

Block ID: **GD-080-015**.

### Private imports that require a supported replacement

| Current symbol | Production use in the adapter | Required supported contract |
| --- | --- | --- |
| `gramlot.contrib._shared.pages.DEFAULT_PREFIX` | Default collection prefix. | Stable default value (`/page`) owned by the public hosting API. |
| `TYTX_FORMAT` | Decode and encode transport selection. | Public transport constant; current value is `json`. |
| `TYTX_MEDIA_TYPE` | Request validation and response content type. | Public transport media type; current value is `application/vnd.tytx+json`. |
| `PageRegistry` | Base class for discovery, method registration, store ownership and invocation. | Public host-extension class with documented hooks and lookup methods. |
| `ServiceParameterError` | Maps signature/binding failures to HTTP 422. | Public exception that remains distinct from application exceptions. |
| `gramlot.contrib._shared.runtime.RuntimeAssets` | Base for manifest discovery, import maps, entry URL and document template. | Public runtime descriptor that does not require adapters to inspect its internals. |
| `PACKAGE_ASSET_DIRECTORIES` | Builds Django URL patterns for source-mode assets. | Replace with a public asset-mount iterator; the directory layout remains core-owned. |
| `render_document` | Produces the default HTML shell. | Public host helper with HTML/JSON escaping retained. |
| `script_json` | Safely embeds import-map and startup JSON in custom Django templates. | Public host helper with the current `<` escaping guarantee. |

### Private or structural members used after import

The adapter also relies on members that are not an explicit contract today:

| Member | Current use | Required change |
| --- | --- | --- |
| `PageRegistry._invoke(...)` | Recipe and Data/Source dispatch. | Rename/expose as async `invoke(...)`; adapters must stop calling `_invoke`. |
| `page_classes` | Index navigation and access checks. | Expose a read-only `pages` mapping and retain `require_page(name)` for lookup. |
| `page_methods` | HTTP role and method preflight. | Expose `registered_method(page_name, method_name) -> PageMethod | None`. |
| `run_sync` | Django supplies `sync_to_async(..., thread_sensitive=True)`. | Document as a required async extension hook. |
| `prepare_page` | Attaches the current Django request before invocation. | Document as the request-context extension hook. |
| `require_page` | Django translates missing pages to `Http404`. | Keep as an overridable public lookup hook. |
| `RuntimeAssets.browser_manifest` | Chooses cache policy and asset roots. | Replace adapter inspection with mount descriptors carrying `immutable`. |
| `browser_directory`, `package_directory`, `frontend_directory` | Constructs served directories. | Replace with mount descriptors carrying resolved directories. |
| `prefix`, `base_url`, `entry_url`, `import_map()`, `document_template()` | URL generation and HTML startup. | Explicitly document these as supported runtime properties/methods. |

`tests/test_django_adapter.py` additionally calls
`PageRegistry._registered_methods` to mutate a loaded page class. This is test
coupling, not a production requirement. Rewrite that case so the failing endpoint
is declared in its fixture page before registry construction; do not publish a
registry mutation API for the test.

### Existing non-private core imports to retain

The adapter also consumes the following current public module paths:

- `gramlot.builder.GramlotBuilder`
- `gramlot.transport.to_tytx`
- `gramlot.page.WebPage`, `endpoint`, and `source`
- `gramlot.resolvers.RpcResolver`
- `gramlot.grid.GridStruct`
- `gramlot.ide.IdePageMixin`

These symbols are host-independent and remain core-owned. Phase 1 should list
them in the compatibility contract even though their imports need no path change.
The temporary pages in the adapter tests also use
`gramlot.page.InvocationContext`.

<a id="gd-080-020"></a>

## 020 · Proposed public interface

Block ID: **GD-080-020**.

This section is a proposal, not verified current behavior.

Add one public facade, `gramlot.hosting`, while keeping implementation details in
the existing internal files for the first change. This minimizes moves and merge
conflicts during the FastAPI extraction. The facade should export only:

```python
from gramlot.hosting import (
    DEFAULT_PREFIX,
    PageRegistry,
    RuntimeAssetMount,
    RuntimeAssets,
    ServiceParameterError,
    render_document,
    script_json,
)
from gramlot.transport import (
    TYTX_FORMAT,
    TYTX_MEDIA_TYPE,
    from_tytx,
    to_tytx,
)
```

`PageRegistry` should expose this adapter-facing protocol:

```python
class PageRegistry:
    pages: Mapping[str, type[WebPage]]

    def require_page(self, name: str) -> type[WebPage]: ...
    def registered_method(self, page_name: str, method_name: str) -> PageMethod | None: ...
    async def invoke(
        self,
        page_name: str,
        role: PageMethodRole,
        method_name: str,
        params: Mapping[str, object],
        request: object | None = None,
    ) -> object: ...

    async def run_sync(self, function, *args): ...
    def create_page(self, page_class): ...
    def prepare_page(self, page, context: InvocationContext) -> None: ...
    def invoke_sync(self, page, method, args, kwargs): ...
    def materialize_result(self, page, result): ...
```

The invocation behavior to support is the behavior already implemented in core:
flat trusted `pages/*.py` discovery, effective Python MRO role discovery, a fresh
page and Source builder for every call, framework-controlled
`InvocationContext`, named-parameter validation, role checking, and
materialization before the host worker boundary is released. HTTP status codes,
authentication and exception disclosure remain adapter policy.

`RuntimeAssets.asset_mounts()` should return immutable descriptors instead of
exposing the core wheel layout:

```python
@dataclass(frozen=True, slots=True)
class RuntimeAssetMount:
    name: str
    url_prefix: str
    directory: Path
    immutable: bool
```

For a compiled payload it returns one mount rooted at the manifest-selected
browser directory with `immutable=True`. For explicit source development it
returns the current grouped roots with `immutable=False`. Both adapters can then
mount or serve the same descriptors without importing
`PACKAGE_ASSET_DIRECTORIES` or reading `browser_manifest`. Validation of the
complete release payload and disabling accidental source fallback in installed
releases remain phase 2 work.

Add `from_tytx` beside `to_tytx` in `gramlot.transport`, so host adapters use the
core-owned transport entry point in both directions. The wrapper should preserve
the selected TYTX transport and registered Gramlot types.

The public facade needs an explicit `__all__`, reference documentation, and a
compatibility statement. The old `_shared` paths may remain private implementation
paths during this pre-alpha transition; neither external adapter may import them
after the coordinated update.

<a id="gd-080-025"></a>

## 025 · Minimal file-level implementation plan

Block ID: **GD-080-025**.

### Gramlot core

1. Add `src/gramlot/hosting.py` as the supported facade.
2. In `src/gramlot/contrib/_shared/pages.py`, expose `invoke`, `pages` and
   `registered_method`; keep validation helpers private and document the five
   adapter hooks above.
3. In `src/gramlot/contrib/_shared/runtime.py`, add `RuntimeAssetMount` and
   `asset_mounts()`; keep package-directory tables private.
4. In `src/gramlot/transport.py`, expose `TYTX_FORMAT`, `TYTX_MEDIA_TYPE` and
   `from_tytx` with `to_tytx`.
5. Add focused public-contract tests and a short maintained hosting reference.

### Django adapter

1. Change `application.py` and `runtime.py` to import only from
   `gramlot.hosting` and `gramlot.transport`.
2. Replace `_invoke`, `page_classes`, `page_methods`, manifest and package-path
   access with `invoke`, `pages`, `registered_method` and `asset_mounts()`.
3. Rewrite the one test that calls `_registered_methods`; add a source audit that
   rejects imports from `gramlot.contrib._shared` and calls to `_invoke`.
4. Preserve all existing Django behavior tests; this boundary change must not
   alter middleware, CSRF, permissions, ORM or transaction semantics.

### Concurrent FastAPI extraction

`gramlot-fastapi` currently imports the same five page symbols, both document
helpers, `RuntimeAssets`, `PACKAGE_ASSET_DIRECTORIES`, and it calls `_invoke` and
reads the same registry/runtime structures. Update it to the same public facade
in the same compatibility window. Move host-independent page-service assertions
from the FastAPI suite into core contract tests; keep HTTP routing, thread-pool
dispatch, static mounting and compression tests in `gramlot-fastapi`.

The compatibility modules still present under `gramlot.contrib.fastapi*` should
remain thin transition shims. They must not become a second implementation of
the hosting contract.

<a id="gd-080-030"></a>

## 030 · Contract test gate

Block ID: **GD-080-030**.

The following tests are meaningful phase 1 gates:

### Core-only tests

- Import `gramlot.hosting`, `gramlot.page` and `gramlot.transport` while imports
  of Django, FastAPI, Starlette and Genropy are blocked.
- With a temporary `pages/` directory and a minimal `PageRegistry` test subclass,
  verify page discovery, implicit `main`, explicit Data/Source roles, MRO
  shadowing, parameter errors, `InvocationContext` injection, sync and async
  invocation, fresh page/Source objects and materialization timing.
- Verify that `pages` cannot be mutated through the public view and that
  `registered_method` returns `PageMethod` or `None` without exposing the backing
  dictionary.
- In compiled and explicit development modes, verify every
  `RuntimeAssetMount`, entry URL, import-map URL and cache-policy flag. Reject a
  missing or invalid required manifest entry.
- Verify `script_json` and `render_document` escape embedded markup and preserve
  the startup/import-map schema.

### Adapter tests

- Import `gramlot_django`, `DjangoIdePage` and `DjangoTablesPage` while FastAPI,
  Starlette and the removed `gramlot.contrib.django` namespace are blocked.
- Statically reject imports from `gramlot.contrib._shared` and private registry
  calls in installed adapter source.
- Run the existing real Django behavior suite against the candidate core; its
  Source/Data, CSRF, permission, ORM, transaction, ASGI and asset assertions are
  regression coverage, not substitutes for the new core-only tests.
- Build both wheels, install them into an isolated environment without FastAPI,
  run `pip check`, and import the adapter from the installed locations.

Apply the equivalent private-import guard and public invocation tests to
`gramlot-fastapi` before calling the shared interface stable.

<a id="gd-080-035"></a>

## 035 · Dependency and release blockers

Block ID: **GD-080-035**.

### Verified facts

- `gramlot-django` is `0.0.0.dev0`, requires exact `gramlot==0.1.5`, allows
  `Django>=5.2,<6.1`, and uses an editable sibling `tool.uv.sources` override.
- Its CI checks out the moving core `develop` branch, prepares the core browser
  assets with npm and installs the checkout. This does not test the declared
  package dependency or a reproducible core artifact.
- Core source is `0.1.5`. Its base dependencies remain server-independent. Its
  current `fastapi` extra points to the unpublished extraction as
  `gramlot-fastapi>=0.0.0.dev0`; core CI currently installs `.[test]`, so that
  extra is not exercised there.
- `gramlot-fastapi` is `0.0.0.dev0`, requires `gramlot>=0.1.5,<0.2`, and also
  uses a sibling source override. Its extracted source and tests are not in its
  current HEAD.
- Core retains compatibility modules which import `gramlot_fastapi` only when
  those legacy FastAPI namespaces are requested. The checked core-only import
  path does not load Django or FastAPI.
- The current core publishing workflow produces GitHub prereleases and uses the
  hard-coded `docs/release-notes-0.1.3.md`; it does not publish the inspected
  core candidate to PyPI.
- `gramlot-django` directly imports `genro_tytx.from_tytx`, `genro_bag.Bag` and
  `asgiref.sync`, while its own dependency list names only Gramlot and Django.
  Those imports currently resolve transitively.
- This audit did not recheck package registries. Current public availability and
  available version numbers remain release checks; older repository notes are
  not used as present registry evidence.

### Proposed release decisions

- Put the supported hosting interface in the core `0.1.5` candidate before
  releasing either adapter. Retain the Django exact pin for the first candidate;
  widen it only after cross-version contract tests exist.
- Use a final adapter version that the unqualified
  `pip install gramlot-django` command may select. `0.0.0.dev0` cannot be the
  final acceptance version. A stable `0.1.0` version with an honest pre-alpha
  classifier is the smallest coherent choice; prerelease candidates can still
  be tested explicitly before it.
- Decide whether Django declares its directly imported `genro-bag` and `asgiref`
  dependencies or removes those direct imports through supported core/Django
  APIs. Do not leave undeclared transitive imports in the release candidate.
  Exposing core `from_tytx` removes the direct `genro-tytx` import.
- Coordinate the FastAPI release cycle: either publish the compatible core first
  and the adapter immediately afterward before advertising `gramlot[fastapi]`, or
  remove/defer that extra from the core candidate. Do not let Django CI depend on
  the FastAPI package.
- Replace moving-branch CI inputs with exact candidate artifacts once the three
  working trees are separated into reviewable commits.

<a id="gd-080-040"></a>

## 040 · Phase 1 done gate

Block ID: **GD-080-040**.

Phase 1 can close only when:

1. the public hosting and bidirectional transport interface is documented and
   covered by core-only tests;
2. Django and FastAPI adapters contain no `_shared` imports or private registry
   calls;
3. core imports with all optional host frameworks absent, and Django imports with
   FastAPI absent;
4. direct dependency ownership and the FastAPI extra sequence are resolved;
5. exact clean commits and candidate versions are recorded; and
6. core contract tests plus both adapters' relevant behavior tests pass against
   those exact commits or artifacts.

<a id="gd-080-045"></a>

## 045 · Verification performed for this assessment

Block ID: **GD-080-045**.

Source and Git state were inspected in all three repositories. Two isolated
subprocess probes passed: the current Django adapter imports with FastAPI,
Starlette and the removed Django contrib namespace blocked; the current core page
and private shared modules import with Django, FastAPI, Starlette and Genropy
blocked. No migrations, full test suites, builds, commits, pushes or publications
were run.
