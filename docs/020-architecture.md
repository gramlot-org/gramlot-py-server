# 020 · Architecture and first integration

Document ID: **GFL-020**.

[Paired view](../docs_llm/020-architecture.md).

<a id="gfl-020-005"></a>

## 005 · Host ownership

Block ID: **GFL-020-005**.

The planned adapter translates Flask requests and responses into Gramlot server contracts. The core remains independent of Flask. Review resource delivery, request-local state, error mapping and cleanup against the selected runtime. API names and runtime dependency versions remain undecided.

<a id="gfl-020-010"></a>

## 010 · Application and database ownership

Block ID: **GFL-020-010**.

Author applications in Python through Gramlot Source, Data Bags, bindings, controllers, resolvers and shared components. Expose missing capabilities in the reusable framework. Do not introduce application-local DOM, manual events, input scraping, ad hoc requests or parallel state. Reuse SQLAlchemy through the shared database contracts, independently of Flask hosting.

<a id="gfl-020-015"></a>

## 015 · Evidence and open work

Block ID: **GFL-020-015**.

The clean Gramlot core currently provides architectural and port records, not an executable runtime. Existing FastAPI experimental integrations are evidence, not automatically accepted contracts. Select a bounded integration and record its provenance, compatibility, lifecycle ownership and test evidence. No formal Live Object Tree semantics, authentication API or async transport support is inferred.
