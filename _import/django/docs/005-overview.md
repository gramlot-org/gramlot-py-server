# 005 · gramlot-django: POC overview

Document ID: **GD-005**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-django/blob/develop/docs_llm/005-overview.md).

**Current native lane:** [GD-090](090-native-html.md) documents the local
Gramlot 0.1.0 Django Host adapter. The PoC installation, demo and ORM discussion
below is historical and does not describe the installable native package.

<a id="gd-005-005"></a>

## 005 · Status and repository roles

Block ID: **GD-005-005**.

This repository is a proof of concept. The intention is to move to a reviewed
prerelease soon, after review and consolidation of both Gramlot and its Django
integration. These previews evaluate APIs and design choices. Described behavior
is intended behavior and may have bugs or incomplete cases. There is no committed
release date or stable API guarantee.
The GitHub downloadable prerelease remains experimental; a distribution label
is not architectural acceptance. Neither package was published on PyPI by this work.

Use [gramlot-poc](https://github.com/gramlot-org/gramlot-poc) for the executable
experimental core. [gramlot](https://github.com/gramlot-org/gramlot) is the clean
product repository that will contain the first actual consolidated version.
It currently defines principles and the port process, not an installable runtime.

<a id="gd-005-010"></a>

## 010 · Responsibilities

Block ID: **GD-005-010**.

Applications are authored primarily in Python. Gramlot owns Source declarations,
Data Bags, bindings, services and reusable JavaScript browser behavior. Django
integration owns its host adaptation and its ORM-specific data adaptation.
These are separate roles even when supplied by the same integration package.
See [architecture](030-architecture.md) for the boundaries and current implementation.

<a id="gd-005-015"></a>

## 015 · Trying the POC

Block ID: **GD-005-015**.

Use the pinned [GitHub installation](010-github-preview.md); development uses the
sibling `gramlot-poc` checkout. Polls is bundled and starts with
`gramlot-django demo --open`. Bakery is a separate project with additional
Wagtail dependencies. Examples are exploratory applications, not final API designs.

<a id="gd-005-020"></a>

## 020 · Acceptance and documentation

Block ID: **GD-005-020**.

The [product constitution](https://github.com/gramlot-org/gramlot/blob/main/docs/00-constitution.md)
and [port protocol](https://github.com/gramlot-org/gramlot/blob/main/ports/README.md)
distinguish prototype evidence from accepted product contracts. Passing POC tests
does not automatically accept a port or establish every host/backend combination.

Expanded `docs/` documents have concise `docs_llm/` counterparts where identified
in the [documentation policy](055-documentation.md). Both versions preserve status,
constraints and open points. Final shared database contracts and the migration
of this adapter to accepted core ports remain work to be consolidated.
