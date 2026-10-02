# 005 · gramlot-django: POC overview

Document ID: **GD-005**.

[Expanded counterpart](../docs/005-overview.md).

**Current native lane:** [GD-090](090-native-html.md) covers the local
Gramlot 0.1.0 Django Host adapter. The PoC install, demo and ORM material below
is historical and not part of the installable native package.

<a id="gd-005-005"></a>

## 005 · Status and repositories

Block ID: **GD-005-005**.

- Preview for evaluating APIs/design choices; intended behavior may have bugs or incomplete cases.
- POC under review; reviewed prerelease intended soon, no fixed date or stable API.
- GitHub prerelease is an experimental download, not product acceptance; no PyPI publication.
- [gramlot-poc](https://github.com/gramlot-org/gramlot-poc): executable experimental core.
- [gramlot](https://github.com/gramlot-org/gramlot): future first consolidated product;
  currently principles and port protocol, not an installable runtime.

<a id="gd-005-010"></a>

## 010 · Responsibilities

Block ID: **GD-005-010**.

- Python-first apps; Gramlot owns Source, Data, bindings, services and browser runtime.
- Django integration owns distinct host and ORM adaptations; see [architecture](030-architecture.md).

<a id="gd-005-015"></a>

## 015 · Usage

Block ID: **GD-005-015**.

- [Pinned GitHub installation](../docs/010-github-preview.md); development uses sibling `gramlot-poc`.
- Bundled Polls: `gramlot-django demo --open`. Bakery needs its separate project/Wagtail dependencies.
- Examples are exploratory, not final API designs.

<a id="gd-005-020"></a>

## 020 · Acceptance and documentation

Block ID: **GD-005-020**.

- Product constitution and port protocol govern acceptance; POC tests are evidence only.
- Paired `docs`/`docs_llm` preserve status, constraints and open questions; update together.
- Shared DB contracts and migration to accepted core ports remain to be consolidated.
- [Documentation coverage and policy](055-documentation.md).
