# 005 · Overview

Document ID: **GFL-005**.

[Paired view](../docs_llm/005-overview.md).

<a id="gfl-005-005"></a>

## 005 · Status and purpose

Block ID: **GFL-005-005**.

Native HTML Flask hosting is implemented against clean Gramlot 0.1.0 through
`mount_native_html`; see [GFL-025](025-native-html.md). The older Microblog demo
and `gramlot-flask` CLI use a PoC API and are outside native compatibility.
Core and adapter artifacts are local candidates, without a registry release.

<a id="gfl-005-010"></a>

## 010 · Boundaries

Block ID: **GFL-005-010**.

Flask request integration belongs here; core owns native Source, Page, Data and
browser runtime. Native hosting needs no database. The historical Microblog demo
uses its own ORM and a PoC SQLAlchemy selector.

<a id="gfl-005-015"></a>

## 015 · Development and branches

Block ID: **GFL-005-015**.

Develop on `develop`; consolidate verified, owner-accepted work into `main`. Publication and deployment need separate authorization. External search, translation, password-reset email and background exports are not configured; this is a local demonstration, not a production deployment.

The explorer is labeled as a Gramlot SPA example. It presents member statistics,
a read-only posts grid with bound selected-post preview, a toggleable read-only
Python source viewer and an inspector icon. All interactions use shared Gramlot
components and Data bindings. The source viewer displays the registered page
snapshot; it does not read arbitrary files.
