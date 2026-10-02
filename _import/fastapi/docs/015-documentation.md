# Documentation policy

Document ID: **GF-015**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-fastapi/blob/main/docs_llm/015-documentation.md).

<a id="1-paired-views"></a>
<a id="gf-015-005"></a>

## 005 · Paired views

Block ID: **GF-015-005**.

Follow Gramlot constitution section 9. Expanded English `docs/<path>` and concise
`docs_llm/<path>` describe the same facts with matching numbered sections and
reciprocal links. Preserve decisions, constraints, status and unresolved questions.

<a id="2-coverage"></a>
<a id="gf-015-010"></a>

## 010 · Coverage

Block ID: **GF-015-010**.

The paired set is overview, architecture, documentation, release, inspector, SQLAlchemy and Read the Docs setup. Older API
and integration guides remain detailed references; mirror them when substantially
revised. The concise index routes readers to both sets. Historical documents must
retain the dates and limits of their evidence.

<a id="3-maintenance"></a>
<a id="gf-015-015"></a>

## 015 · Maintenance

Block ID: **GF-015-015**.

Update both sides together. Read the constitution and relevant POC evidence before
changing architecture claims. Distinguish observed behavior, proposed APIs and
accepted contracts. POC tests and downloadable builds do not imply product acceptance.


<a id="stable-identity-and-migration-inventory"></a>
<a id="gf-015-020"></a>

## 020 · Stable identity and migration inventory

Block ID: **GF-015-020**.

Use repository-wide GF document IDs and GF document/block IDs. Assign three-digit
filename and block numbers initially spaced by five; insert in gaps. Both views
share lowercase explicit anchors. Preserve identities and anchors across moves;
never reuse retired IDs. Cite IDs with links and update inbound references.

Migrated Markdown pairs: overview ([GF-005](005-overview.md)), architecture ([GF-010](010-architecture.md)), documentation
([GF-015](015-documentation.md)), release ([GF-020](020-release.md)), inspector ([GF-025](025-inspector.md)), Read the Docs ([GF-030](030-readthedocs.md)),
SQLAlchemy ([GF-035](035-sqlalchemy.md)), integration direction ([GF-040](040-server-and-database-integration.md)).
Native hosting ([GF-050](050-native-html.md)) and native getting started
([GF-055](getting-started.md)) also have paired guides with stable IDs. The
integration direction and getting-started guides now have concise mirrors.

Remaining legacy guides: first-page.rst, guide.rst and reference.rst lack
concise mirrors and stable IDs. Migrate and add mirrors on
substantial revision. Entry points, configuration, requirements and assets are
exempt. Keep Sphinx with sphinx_rtd_theme. Public documentation follows main; new work stays on
develop until verified and accepted.
