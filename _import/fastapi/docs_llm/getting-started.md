# 055 · Getting started with native HTML

Document ID: **GF-055**.

[Expanded](../docs/getting-started.md).

<a id="gf-055-005"></a>
## 005 · Install and launch

Block ID: **GF-055-005**.

Build and install the local Gramlot 0.1.0, FastAPI, Flask, Genro ASGI and Hello
World wheels in one Python 3.11+ environment. Run
`python -m gramlot_example_app.server.fastapi` and open
<http://127.0.0.1:8000/>. The launcher uses `NativeHtmlApplication`.

<a id="gf-055-010"></a>
## 010 · Mount in an existing app

Block ID: **GF-055-010**.

Existing FastAPI apps use `mount_native_html(app, pages)` with a trusted Page
directory. See [GF-050](050-native-html.md).

<a id="gf-055-015"></a>
## 015 · Scope

Block ID: **GF-055-015**.

The old `gramlot-fastapi serve`/`GramlotApplication` path requires PoC modules
absent from clean 0.1.0 and is outside this release.
