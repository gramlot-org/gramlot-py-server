# FastAPI inspector

Historical PoC guide: this inspector/CLI is outside clean 0.1.0.
See [GF-050](050-native-html.md) for native hosting.

Document ID: **GF-025**.

[Expanded counterpart and screenshots](../docs/025-inspector.md).

<a id="1-run-the-example"></a>
<a id="gf-025-005"></a>

## 005 · Run the example

Block ID: **GF-025-005**.

From a checkout with the preview installed: `gramlot-fastapi serve examples/plain`.
Open http://127.0.0.1:8000/page/inspector/.
Source: `examples/plain/pages/inspector.py`. Both screenshots use this plain
FastAPI page, without a database. APIs are experimental.

<a id="2-explore-and-edit-data"></a>
<a id="gf-025-010"></a>

## 010 · Explore and edit Data

Block ID: **GF-025-010**.

Magnifying glass or Ctrl+Shift+D. Select Data, then message. Edit the Properties
value and leave the row. Screenshot value: Edited through the FastAPI inspector.
The text field and text display share the binding; no database operation occurs.

<a id="3-explore-and-edit-source"></a>
<a id="gf-025-015"></a>

## 015 · Explore and edit Source

Block ID: **GF-025-015**.

Select Source, expand div_0, select h1_0, edit its value and leave the row.
Screenshot heading: FastAPI: live Source edit.
Source is the live UI declaration tree generated from Python.

<a id="4-lifetime-and-boundaries"></a>
<a id="gf-025-020"></a>

## 020 · Lifetime and boundaries

Block ID: **GF-025-020**.

Edits affect the running page; no Python rewrite or automatic persistence.
Reload/controllers may replace edits; bindings can react to them.
`source_inspection = False` disables the inspector in startup configuration;
it is not server authorization. See SQLAlchemy status and architecture.
