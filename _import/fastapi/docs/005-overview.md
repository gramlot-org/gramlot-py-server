# FastAPI adapter overview

Document ID: **GF-005**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-fastapi/blob/main/docs_llm/005-overview.md).

<a id="1-status-and-repositories"></a>
<a id="gf-005-005"></a>

## 005 · Status and repositories

Block ID: **GF-005-005**.

The native HTML FastAPI adapter is implemented against the clean Gramlot 0.1.0
core. `NativeHtmlApplication` and `mount_native_html` are the 0.1.0 entry points;
the [native guide](050-native-html.md) defines their bounded contract. Core and
adapter are local release candidates; no registry publication or deployment is
implied. The older Page/recipe/RPC adapter remains PoC evidence and is outside
native 0.1.0 compatibility.

<a id="2-responsibilities"></a>
<a id="gf-005-010"></a>

## 010 · Responsibilities

Block ID: **GF-005-010**.

FastAPI supplies server adaptation: requests, routing, invocation and asset delivery.
Database adapters supply backend access and metadata independently of the server.
Gramlot owns Python declarations, shared services, transport and reusable browser behavior.

<a id="3-trying-and-maintaining-the-poc"></a>
<a id="gf-005-015"></a>

## 015 · Trying and maintaining the POC

Block ID: **GF-005-015**.

See [release procedure](020-release.md) for local 0.1.0 artifacts and installation.
The separate historical PoC profile uses sibling `gramlot-poc`. Its Genropy and
database contracts remain outside the native release.
The paired documentation follows [documentation policy](015-documentation.md).

This repository currently hosts the FastAPI server adapter and explains the
SQLAlchemy integration boundary. The core POC has an experimental read-only SQLite
reader, now connected to FastAPI through the optional `db_handler` parameter.
See [SQLAlchemy status](035-sqlalchemy.md).
