# 005 · Overview

Document ID: **GFL-005**.

[Paired view](../docs_llm/005-overview.md).

<a id="gfl-005-005"></a>

## 005 · Status and purpose

Block ID: **GFL-005-005**.

Flask hosting and the Microblog integration demo are implemented as an experimental preview, using the checksummed Gramlot 0.1.5 PoC wheel. This is not a consolidated core release. The default `gramlot-flask` command serves Microblog on loopback port 8073; use demo / gramlot-demo to sign in.

<a id="gfl-005-010"></a>

## 010 · Boundaries

Block ID: **GFL-005-010**.

Flask request integration belongs here; shared Source, Data, bindings, controllers, resolvers and components remain in Gramlot. Plain hosting needs no database. The optional Microblog demo uses its own ORM and the shared read-only SQLAlchemy selector. It adds a Gramlot user/profile/post explorer to the original host application.

<a id="gfl-005-015"></a>

## 015 · Development and branches

Block ID: **GFL-005-015**.

Develop on `develop`; consolidate verified, owner-accepted work into `main`. Publication and deployment need separate authorization. External search, translation, password-reset email and background exports are not configured; this is a local demonstration, not a production deployment.

The explorer is labeled as a Gramlot SPA example. It presents member statistics,
a read-only posts grid with bound selected-post preview, a toggleable read-only
Python source viewer and an inspector icon. All interactions use shared Gramlot
components and Data bindings. The source viewer displays the registered page
snapshot; it does not read arbitrary files.
