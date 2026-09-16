# 005 · Overview

Document ID: **GFL-005**.

[Paired view](../docs/005-overview.md).

<a id="gfl-005-005"></a>

## 005 · Status and purpose

Block ID: **GFL-005-005**.

Experimental Flask adapter and Microblog demo using the checksummed Gramlot 0.1.5 PoC wheel, not a consolidated core release. Run `gramlot-flask`: loopback port 8073; login demo / gramlot-demo.

<a id="gfl-005-010"></a>

## 010 · Boundaries

Block ID: **GFL-005-010**.

Flask hosting lives here; shared UI/state/behavior remains in Gramlot. Plain hosting needs no database. The optional demo combines Microblog ORM/login with Gramlot’s read-only SQLAlchemy selector and a user/profile/post explorer.

<a id="gfl-005-015"></a>

## 015 · Development and branches

Block ID: **GFL-005-015**.

Work on `develop`; consolidate verified, owner-accepted changes into `main`. Publication/deployment need separate authorization. The local demo does not configure external search, translation, reset emails or background exports.

The explorer is labeled as a Gramlot SPA example. It presents member statistics,
a read-only posts grid with bound selected-post preview, a toggleable read-only
Python source viewer and an inspector icon. All interactions use shared Gramlot
components and Data bindings. The source viewer displays the registered page
snapshot; it does not read arbitrary files.
