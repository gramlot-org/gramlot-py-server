# gramlot-fastapi: scope and extraction inventory

## Native 0.1.0 release boundary — 2026-09-23

The supported native path is `NativeHtmlApplication` or `mount_native_html`
against clean Gramlot 0.1.0 and its neutral Host. See [GF-050](docs/050-native-html.md).
The extraction, SQLite and preview-wheel sections below document the older
PoC profile, not the current 0.1.0 installer or API. Its legacy imports require
modules absent from the clean core. Neither adapter nor core is claimed
published to a registry.

## Provisional SQLite profile — 2026-09-16

`GramlotApplication`, `mount_gramlot` and `PageCollection` accept an optional
core `DbHandler` as `db_handler`. They attach it to fresh `DbPageMixin` pages.
The caller owns handler shutdown; the core reader owns per-operation connections.
The optional `sqlalchemy` extra and SQLite example provide read-only dbSelect
through the core wheel's existing reader. No write or general ORM API is claimed.
See [the current SQLAlchemy guide](docs/035-sqlalchemy.md).

## Distribution clarification — 2026-09-16

This integration remains a POC under review. The experimental runtime lives in
`gramlot-poc`; `gramlot` will contain the first consolidated product. Preview
0.1.0a1 pins the compatible core 0.1.5 candidate, following Django's checksummed
wheel distribution model. See [release preparation](docs/020-release.md) and the
paired [architecture](docs/010-architecture.md). No publication is implied.
The adapter now declares the checksummed experimental core wheel as a direct
dependency, so users do not need a matching Gramlot source tag. Version 0.1.5
identifies that packaged POC snapshot. Preview descriptions express intended
behavior for API and design evaluation; bugs and incomplete cases may exist.
Server and database adaptation are separate responsibilities. SQLite belongs in
Gramlot/gramlot-poc; temporary legacy placement is tolerated for this preview.
The older extraction scope below is historical where later architecture refines it.

## Owner clarification — 2026-09-15

The section below records the extraction scope. The later
[server and database integration direction](docs/040-server-and-database-integration.md)
refines its ownership boundary: Gramlot will define a standard database
interface, with server-independent optional adapters in its contrib area.
Server integration remains in the host repositories. A fake adapter will use
three small standard tables. This architecture is agreed in direction; the
database API and implementation are still to be defined.

This repository will own the FastAPI integration currently maintained in Gramlot.
Users combining Gramlot and FastAPI must find the adapter and necessary
host-specific classes here, together with their tests and usage documentation.

Provide a plain FastAPI host and two optional database integrations:

- SQLAlchemy.
- Genropy through an initialized `GnrApp` and its database.

The two database integrations belong to this project and must remain independent:
plain hosting must not require either, and using one must not require the other.
Extract the existing `gramlot.contrib.fastapi` and
`gramlot.contrib.fastapi_genropy` implementations rather than creating a competing
FastAPI adapter. SQLAlchemy support is new work; no corresponding integration was
found in the inspected Gramlot Python package.

This direction supersedes the initial description of this repository as only a
consumer boilerplate with a future Genropy profile.

## Initial extraction inventory — 2026-09-15

Inspected source: the sibling `gramlot` checkout, on `develop` at `e2127a1`,
including local uncommitted changes. This is a working-tree inventory, not a
claim that its current contents match a published release.

Paths below are relative to the Gramlot repository.

| Source | Responsibility and migration scope |
| --- | --- |
| `src/gramlot/contrib/fastapi/application.py` | `GramlotApplication`, `mount_gramlot`, `PageCollection`; HTTP page, recipe and RPC handling and worker dispatch. |
| `src/gramlot/contrib/fastapi/runtime.py` | FastAPI static asset mounting, cache headers and compression for Gramlot's browser runtime. |
| `src/gramlot/contrib/fastapi/__init__.py` and `examples.py` | Public exports and the example-helper compatibility import. |
| `src/gramlot/contrib/fastapi_genropy/` | `GenropyPage`, `GenropyPageCollection`, factory and mounting functions, invocation-scoped DB access, selection results, relation metadata and legacy Bag conversion. |
| `src/gramlot/__main__.py` | FastAPI-specific `serve` command and dependency guidance; the manual command is unrelated to this extraction. |
| `pyproject.toml` | FastAPI extra and the dependencies needed by the extracted host. |
| `tests/test_fastapi_adapter.py`, `test_fastapi_browser_distribution.py`, `test_fastapi_genropy.py` | Adapter behavior, CLI, packaged browser delivery and Genropy lifecycle coverage. |
| Other RPC, page-service, resolver and example-host tests | Separate reusable framework assertions from FastAPI integration assertions and preserve coverage. |
| `docs/source/guide/fastapi.rst`, `docs/source/reference/fastapi.rst`, `docs/fastapi.md` | Host installation, usage and API documentation to migrate and update. |
| `docs/examples/serve.py`, `navigation.py` and database examples | FastAPI example hosting and Genropy-backed pages; review imports and ownership without duplicating generic framework examples. |

### Shared framework boundary

The adapter depends on `gramlot.contrib._shared.pages` and
`gramlot.contrib._shared.runtime`, also used by the Django integration. These
host-independent facilities require a stable dependency boundary; they must not
be moved wholesale into a FastAPI-only package. Gramlot continues to own generic
page authoring, builders, Bags, transport, resolvers and the browser runtime.
This package owns their FastAPI delivery and database-specific integration.

### Migration decisions

- Public imports are `gramlot_fastapi` and `gramlot_fastapi.genropy`; the command
  is `gramlot-fastapi serve`. Gramlot retains re-export-only compatibility modules
  and its legacy command delegates to this package during the transition.
- The package pins Gramlot 0.1.5 and remains pre-alpha. The inspected
  local framework is 0.1.5 with uncommitted work; consumers must install a matching
  framework checkout until a compatible release is available from their index.
- SQLAlchemy session and transaction ownership, synchronous/asynchronous scope,
  and conversion of query results to the existing Gramlot data contracts.
- Example ownership and coordinated updates to consumers and framework tests.

## Established constraints

- Gramlot is an independent Python-authoring and JavaScript-runtime framework.
- Application UI, state and interactions use Gramlot declarations and services.
- Author application pages in Python; reusable browser behavior belongs in the framework.
- Keep host-specific dependencies in the consumer integration.
- Reuse existing adapters before introducing another implementation.
- Distinguish installed/released capabilities from local, unpublished work.

## Implemented extraction

The package now contains the FastAPI application and mounting APIs, browser
runtime delivery, role-checked TYTX endpoints, a standalone development command,
the Genropy `GnrApp` profile, behavior tests and Genropy-backed example pages.
Host-independent registry, page, builder, transport and runtime discovery remain
in Gramlot. The provisional SQLAlchemy profile now wires the core read-only
SQLite adapter to database pages;
see [current SQLAlchemy scope](docs/035-sqlalchemy.md). Earlier statements about the
absence of SQLAlchemy code describe the initial extraction inventory.

## Remaining work

1. Update external consumers to the public `gramlot_fastapi` imports and direct
   dependency when they next change; compatibility shims cover the transition.
2. Publish or otherwise make the compatible Gramlot version available before a
   standalone index installation can resolve this package.
3. Extend the provisional read-only SQLAlchemy profile only after agreeing further
   database operations and transaction semantics.
4. Verify rendered Python-authored Gramlot pages and installed-package use for
   plain hosting and each database profile independently.

The seven presentation scenarios in the framework context remain the wider
roadmap. Creating these three repositories does not implement every scenario.
