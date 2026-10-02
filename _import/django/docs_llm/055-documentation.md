# 055 · Documentation policy

Document ID: **GD-055**.

[Expanded counterpart](../docs/055-documentation.md).

<a id="gd-055-005"></a>

## 005 · Two views

Block ID: **GD-055-005**.

- Follow Gramlot constitution §9: `docs/<path>` ↔ `docs_llm/<path>`.
- Expanded = context/examples; concise = fewer words, still human-readable.
- Preserve decisions, constraints, status, limitations and open questions; never strengthen claims.
- Same numbered sections; reciprocal links; English.

<a id="gd-055-010"></a>

## 010 · Coverage

Block ID: **GD-055-010**.

- Paired now: overview, architecture, documentation, readthedocs, admin-spa,
  inspector and native HTML integration (GD-090).
- Existing integration/install/demo/release guides remain detailed references;
  mirrors are added on substantial revision. Coverage is not complete.
- Dated verification reports keep scope/date. README links both views;
  [index](index.md) routes all readers. Root SPECIFICATION defines adapter ownership.

<a id="gd-055-015"></a>

## 015 · Maintenance

Block ID: **GD-055-015**.

- Change both members together; new architecture/product contracts require a pair.
- Read product constitution and relevant POC evidence before changing claims.
- Separate observed/proposed/accepted/verified; never infer planned APIs as implemented.
- POC examples/tests do not imply product acceptance. Mermaid only when useful.
- Check docs, links and paired status before publishing.

<a id="gd-055-020"></a>

## 020 · Ordering and stable references

Block ID: **GD-055-020**.

- Three-digit filename prefixes, initially 005, 010, 015…; paired paths/prefixes identical.
- Documents: repository-wide GD IDs. Level-two blocks: GD-document-section IDs, initially spaced by five.
- Human and concise views intentionally share logical IDs and explicit HTML anchors.
- Example: **GD-040-025**, validation and saving; [human](../docs/040-admin-spa.md#gd-040-025), [concise](040-admin-spa.md#gd-040-025).
- Insert in gaps (e.g. 011); never reuse retired IDs or renumber stable IDs. Reordering can change filename prefixes, not IDs/anchors. Moving files requires link updates; IDs do not redirect URLs.
- Future folders mirror between trees, e.g. 030-integration/040-admin-spa.md; IDs remain global within the repo, not restarted per folder. Other repos need distinct namespaces.
- index/configuration/requirements/assets/historical HTML export are exempt. Do not invent missing mirrors; track coverage.
