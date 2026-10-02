# 055 · Getting started with native HTML

Document ID: **GF-055**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-fastapi/blob/main/docs_llm/getting-started.md).

<a id="gf-055-005"></a>
## 005 · Install and launch

Block ID: **GF-055-005**.

Native 0.1.0 uses clean Gramlot Page modules and `NativeHtmlApplication`.
In Python 3.11+, build the core wheel and the FastAPI, Flask, Genro ASGI and
Hello World wheels locally. Install all wheels in one environment:

```sh
python -m pip install /path/to/gramlot-0.1.0-py3-none-any.whl \
  /path/to/gramlot_fastapi-*.whl /path/to/gramlot_flask-*.whl \
  /path/to/gramlot_genro_asgi-*.whl /path/to/gramlot_example_app-*.whl
python -m gramlot_example_app.server.fastapi
```

Open <http://127.0.0.1:8000/>. The example's page is a Python `Page` from
`gramlot.page`. Its launcher uses the adapter's `NativeHtmlApplication`, not
the legacy CLI. See [GF-050](050-native-html.md) for routes and lifecycle.

<a id="gf-055-010"></a>
## 010 · Mount in an existing app

Block ID: **GF-055-010**.

For an existing FastAPI app, mount a trusted directory of Page modules:

```python
from fastapi import FastAPI
from gramlot_fastapi import mount_native_html

app = FastAPI()
pages = mount_native_html(app, "/path/to/pages")
```

<a id="gf-055-015"></a>
## 015 · Scope

Block ID: **GF-055-015**.

The core and adapter artifacts are local candidates. The older
`gramlot-fastapi serve` command and `GramlotApplication` require PoC modules
absent from clean 0.1.0. The [historical first-page guide](first-page.rst)
records that separate profile; it is not a native launch procedure.
