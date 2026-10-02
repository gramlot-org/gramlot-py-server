# 055 · Documentation policy

Document ID: **GD-055**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-django/blob/develop/docs_llm/055-documentation.md).

<a id="gd-055-005"></a>

## 005 · Two views of the same information

Block ID: **GD-055-005**.

Follow [Gramlot constitution section 9](https://github.com/gramlot-org/gramlot/blob/main/docs/00-constitution.md):
pair `docs/<path>` with `docs_llm/<path>`. The expanded document explains context
and examples for people; its concise counterpart helps LLMs and readers navigate
with fewer words. Both remain human-readable and preserve decisions, constraints,
status, limitations and open questions. A shorter version must not strengthen a claim.
Use the same numbered sections for stable references, reciprocal links and English.

<a id="gd-055-010"></a>

## 010 · Current coverage

Block ID: **GD-055-010**.

The paired set includes `005-overview.md`, `030-architecture.md`,
`040-admin-spa.md`, `045-inspector.md`, `055-documentation.md`,
`060-readthedocs.md` and native integration guide `090-native-html.md`.
The existing integration, installation, demos and release guides in `docs/` remain
the detailed references; they do not yet all have concise counterparts. Historical
verification reports retain their date and scope. Add mirrors as these guides are
substantially revised; do not pretend existing coverage is complete.
README links to both entry points; [the concise index](https://github.com/gramlot-org/gramlot-django/blob/develop/docs_llm/index.md) routes
to paired documents and the remaining detailed guides. Root SPECIFICATION remains
the adapter ownership reference.

<a id="gd-055-015"></a>

## 015 · Maintenance and review

Block ID: **GD-055-015**.

Update both members of a pair in the same change. New architectural or product
contract documents need both forms. Read the product constitution and relevant
`gramlot-poc` evidence before changing integration claims. Distinguish observed,
proposed, accepted and verified behavior; do not invent APIs from planned contracts.
Examples and passing POC tests do not imply acceptance in the clean product repo.
Use Mermaid when a diagram clarifies a boundary, not instead of defining the contract.
Run repository documentation checks and review links and paired status before publishing.

<a id="gd-055-020"></a>

## 020 · Ordering and stable references

Block ID: **GD-055-020**.

Use three-digit filename prefixes in steps of five: `005-overview.md`,
`010-github-preview.md`, `015-quickstart.md`. Human and concise versions use the
same path, prefix, document ID and block IDs. `index`, Sphinx configuration,
requirements, assets and the historical standalone HTML export are entry points
or support files, not numbered guides.

Initial document IDs use this repository's namespace, for example **GD-040** for
the SPA admin guide. Level-two sections have stable block IDs, initially in steps
of five too: **GD-040-025** identifies validation and saving in both views. Cite
the ID plus a link to the chosen view. For example:

- [Human GD-040-025](https://github.com/gramlot-org/gramlot-django/blob/main/docs/040-admin-spa.md#gd-040-025).
- [Concise GD-040-025](https://github.com/gramlot-org/gramlot-django/blob/main/docs_llm/040-admin-spa.md#gd-040-025).

The explicit HTML anchors work on GitHub and in the Sphinx HTML. IDs identify
logical content; the human and concise presentations intentionally share an ID.
Use different repository namespaces elsewhere to avoid ambiguous citations.

Insert new documents or sections into gaps, such as `011`, without renumbering
existing IDs. Never reuse retired IDs. If display order must change, retain the
original document/block IDs and anchors even if a filename prefix changes. Update
links when moving files; a stable ID does not automatically redirect an old URL.

When folders become useful, mirror their structure in both trees, for example
`030-integration/040-admin-spa.md`. Document IDs remain repository-wide: do not
restart their numbering in each folder. Preserve IDs when reorganizing folders.
Only create a concise counterpart when it is maintained; missing mirrors remain
explicitly recorded in the coverage section.
