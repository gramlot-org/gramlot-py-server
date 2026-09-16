# 005 · Overview

Document ID: **GFL-005**.

[Paired view](../docs_llm/005-overview.md).

<a id="gfl-005-005"></a>

## 005 · Status and purpose

Block ID: **GFL-005-005**.

This repository is the future Flask host adapter for Gramlot. Only the package namespace, tooling and documentation exist. No page API, server command, demo or runtime compatibility has been implemented or verified.

<a id="gfl-005-010"></a>

## 010 · Boundaries

Block ID: **GFL-005-010**.

Flask-specific hosting belongs here. Source, Data Bags, bindings, controllers, resolvers and shared components belong to Gramlot. SQLAlchemy is an independent optional database adapter. Plain hosting must not require a database.

<a id="gfl-005-015"></a>

## 015 · Reference and branches

Block ID: **GFL-005-015**.

The repository follows the layout of gramlot-genro-asgi and the ownership boundaries of gramlot-fastapi. Develop new work on `develop`; consolidate verified and owner-accepted work into `main`. Publication and deployment require separate owner authorization.
