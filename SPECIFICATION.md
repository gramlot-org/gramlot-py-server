# gramlot-genro-asgi: initial scope

## Recorded owner request — 2026-09-15

Create this repository under `gramlot-org` using `genro-asgi` as the boilerplate
reference. Keep the checkout under `/Users/gporcari/Sviluppo/gramlot`.

## Intended integration

Genro ASGI hosting without a database, followed by an optional Genropy database profile.

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
5. Verify its rendered Python-authored Gramlot page.

The seven presentation scenarios in the framework context remain the wider
roadmap. Creating these three repositories does not implement every scenario.
