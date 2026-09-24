# 005 · Overview

Document ID: **GFL-005**.

[Paired view](../docs/005-overview.md).

<a id="gfl-005-005"></a>

## 005 · Status and purpose

Block ID: **GFL-005-005**.

Native HTML Flask hosting uses clean Gramlot 0.1.0 through
`mount_native_html`; see [GFL-025](025-native-html.md). The older Microblog
demo and CLI use PoC APIs and are outside native compatibility. Artifacts are
local candidates, not claimed registry releases.

<a id="gfl-005-010"></a>

## 010 · Boundaries

Block ID: **GFL-005-010**.

Flask hosting lives here; native Source, Page, Data and runtime remain in core.
Native hosting needs no database. The historical demo uses Microblog ORM/login
and a PoC SQLAlchemy selector.

<a id="gfl-005-015"></a>

## 015 · Development and branches

Block ID: **GFL-005-015**.

Work on `develop`; consolidate verified, owner-accepted changes into `main`. Publication/deployment need separate authorization. The local demo does not configure external search, translation, reset emails or background exports.

The explorer is labeled as a Gramlot SPA example. It presents member statistics,
a read-only posts grid with bound selected-post preview, a toggleable read-only
Python source viewer and an inspector icon. All interactions use shared Gramlot
components and Data bindings. The source viewer displays the registered page
snapshot; it does not read arbitrary files.
