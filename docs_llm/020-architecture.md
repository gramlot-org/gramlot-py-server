# 020 · Architecture and first integration

Document ID: **GFL-020**.

[Paired view](../docs/020-architecture.md).

<a id="gfl-020-005"></a>

## 005 · Host ownership

Block ID: **GFL-020-005**.

Translate Flask requests/responses into shared Gramlot contracts; keep the core Flask-independent. Review resources, request-local state, errors and cleanup against the chosen runtime. API and dependency versions remain open.

<a id="gfl-020-010"></a>

## 010 · Application and database ownership

Block ID: **GFL-020-010**.

Use Python and Gramlot Source, Data Bags, bindings, controllers, resolvers and components. Resolve reusable framework gaps; prohibit application-local DOM, events, input scraping, requests or parallel state. SQLAlchemy reuses independent database contracts.

<a id="gfl-020-015"></a>

## 015 · Evidence and open work

Block ID: **GFL-020-015**.

The clean core has architecture/port records, not an executable runtime. FastAPI experimental code is evidence, not accepted contracts. Record bounded integration provenance, compatibility, lifecycle and tests. Do not infer Live Object Tree, authentication APIs or async transports.
