# 005 · Overview

Document ID: **GFL-005**.

[Paired view](../docs/005-overview.md).

<a id="gfl-005-005"></a>

## 005 · Status and purpose

Block ID: **GFL-005-005**.

This is the future Flask host adapter. The scaffold contains a namespace, tooling and documentation only; no page API, CLI, demo or runtime compatibility is verified.

<a id="gfl-005-010"></a>

## 010 · Boundaries

Block ID: **GFL-005-010**.

Keep Flask hosting here and shared UI/state/behavior contracts in Gramlot. SQLAlchemy is independently optional; plain hosting must need no database.

<a id="gfl-005-015"></a>

## 015 · Reference and branches

Block ID: **GFL-005-015**.

Follow the Genro ASGI layout and FastAPI ownership boundary. Develop on `develop`; move verified, owner-accepted work to `main`. Publication and deployment need separate authorization.
