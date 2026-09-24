# gramlot-genro-asgi: initial scope

## Native 0.1.0 release boundary — 2026-09-23

`NativeHtmlASGI`, `create_asgi_application` and
`KajennNativeHtmlApplication` host clean Gramlot 0.1.0 Page modules; see
[GA-010](docs/010-native-html.md). The GenroPy `GnrApp` integration and old
CLI described below are historical PoC work, outside native 0.1.0. Their
imports require modules absent from the clean core. SQLAlchemy and database
contracts are excluded from the native slice.

## Current owner direction — 2026-09-16

Begin implementation with Genro ASGI hosting and optional GenroPy legacy database
access through a caller-owned GnrApp. The owner authorized public PoC visibility on 2026-09-17. SQLAlchemy is
deferred from the initial slice; plain hosting remains database-independent.
This supersedes the earlier requirement to implement both database profiles in
the first increment. The historical scope below remains as provenance.

The first experimental implementation now exists on develop; see
[the bounded contract](docs/005-genro-asgi-legacy.md) for dependencies, ownership,
verification and omissions. It is not a clean-core port or public release.

## Recorded owner request — 2026-09-15

Create this repository under `gramlot-org` using `genro-asgi` as the boilerplate
reference. Keep the checkout under `/Users/gporcari/Sviluppo/gramlot`.

## Owner clarification — 2026-09-15

This repository will be the home for users building Gramlot applications on
Genro ASGI, analogous to the role of `gramlot-fastapi` for FastAPI. It will
provide the host integration, examples, tests and usage documentation.

The intended scope includes three profiles:

- Plain Genro ASGI hosting without a database.
- Optional SQLAlchemy database integration, as planned for `gramlot-fastapi`.
- Optional legacy Genropy integration through `GnrApp` and its database.

The database integrations must remain independent: plain hosting must not
require either, and using one must not require the other. This direction
supersedes the initial scope of plain hosting followed only by a Genropy
database profile. It does not describe implemented or released functionality.

## Intended integration

Keep Genro ASGI hosting in this consumer repository or its host integration. Do not introduce a Genro ASGI dependency into the Gramlot core. Review the existing genro-asgi[gui] integration before designing application hosting.

## Established constraints

- Gramlot is an independent Python-authoring and JavaScript-runtime framework.
- Application UI, state and interactions use Gramlot declarations and services.
- Author application pages in Python; reusable browser behavior belongs in the framework.
- Keep host-specific dependencies in the consumer integration.
- Reuse existing adapters before introducing another implementation.
- Distinguish installed/released capabilities from local, unpublished work.

## Initial delivered scope

Repository metadata, license, package namespace, development dependencies,
quality tooling, Git hooks, Sphinx documentation and CI. No application API,
server command, database, demo content or adapter migration is implemented yet.

## Before application implementation

1. Inventory the existing host integration and examples.
2. Decide package ownership versus example application ownership.
3. Select compatible, available runtime dependency versions.
4. Implement a minimal host profile and real behavior tests.
5. Define database lifecycle ownership for SQLAlchemy sessions and transactions
   and for the legacy `GnrApp` connection and database access.
6. Implement both optional database profiles with real behavior tests, reusing
   existing integration code where appropriate.
7. Verify rendered Python-authored Gramlot pages and installed-package use for
   plain hosting and each database profile independently.

The seven presentation scenarios in the framework context remain the wider
roadmap. Creating these three repositories does not implement every scenario.
