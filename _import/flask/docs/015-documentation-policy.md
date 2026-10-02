# 015 · Documentation policy

Document ID: **GFL-015**.

[Paired view](../docs_llm/015-documentation-policy.md).

<a id="gfl-015-005"></a>

## 005 · Identity and pairing

Block ID: **GFL-015-005**.

Follow the Gramlot constitution section 9 and core guide GC-005. This repository uses namespace **GFL**. Guide filenames use three digits initially spaced by five. Expanded and concise views share paths, document IDs, block IDs and explicit lowercase anchors. Preserve identities across moves and update links; never reuse retired IDs.

<a id="gfl-015-010"></a>

## 010 · Presentation and publication

Block ID: **GFL-015-010**.

Use Sphinx with `sphinx_rtd_theme`, its default blue/dark/light appearance and the Gramlot logo. Preserve the experimental preview notice. Public consolidated documentation follows `main`; `develop` may have a separate preview. Read the Docs configuration does not mean that external hosting is connected.

<a id="gfl-015-015"></a>

## 015 · Coverage

Block ID: **GFL-015-015**.

All numbered guides have paired paths and stable block identities from inception; there are no legacy guide migration gaps. Entry points, build configuration, requirements and assets are exempt from guide numbering. Update both views together, preserving status, constraints, limitations and open decisions. The check script validates pairing and IDs and builds both views with warnings as errors.
