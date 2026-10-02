# FastAPI adapter overview

Document ID: **GF-005**.

[Expanded version](../docs/005-overview.md).

<a id="1-status-and-repositories"></a>
<a id="gf-005-005"></a>

## 005 · Status and repositories

Block ID: **GF-005-005**.

Native HTML FastAPI hosting is implemented against clean Gramlot 0.1.0.
`NativeHtmlApplication` and `mount_native_html` are the release-candidate entry
points; see [GF-050](050-native-html.md). Neither core nor adapter is claimed
published or deployed. Old Page/recipe/RPC APIs are historical PoC evidence,
outside native 0.1.0 compatibility.

<a id="2-responsibilities"></a>
<a id="gf-005-010"></a>

## 010 · Responsibilities

Block ID: **GF-005-010**.

FastAPI: server adaptation. Database adapters: backend/model adaptation.
Gramlot: Python declarations, shared
services, transport and reusable JavaScript.

<a id="3-trying-and-maintaining-the-poc"></a>
<a id="gf-005-015"></a>

## 015 · Trying and maintaining the POC

Block ID: **GF-005-015**.

[Release](020-release.md): local core wheel and adapter source/artifact. The
historical profile uses sibling POC; Genropy and DB contracts are excluded.
Maintain paired docs via [policy](015-documentation.md).

This repository currently hosts the FastAPI server adapter and explains the
SQLAlchemy integration boundary. The core POC has an experimental read-only SQLite
reader, now connected to FastAPI through the optional `db_handler` parameter.
See [SQLAlchemy status](035-sqlalchemy.md).
