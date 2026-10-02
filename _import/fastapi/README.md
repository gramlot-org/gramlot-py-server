# gramlot-fastapi

FastAPI hosting for Gramlot's native HTML Page and neutral Host. The native
0.1.0 profile is implemented in `gramlot_fastapi.native_html`; it has no database
integration. Core and adapter packages are local release candidates, not published
registry releases.

## Run the native Hello World

In a Python 3.11+ environment, install the locally built core 0.1.0 wheel and
all three adapter wheels, then the Hello World application with its
`python-hosts` extra. Build each adapter wheel from its checkout first:

```sh
python -m pip install /path/to/gramlot-0.1.0-py3-none-any.whl \
  /path/to/gramlot_fastapi-*.whl /path/to/gramlot_flask-*.whl \
  /path/to/gramlot_genro_asgi-*.whl
python -m pip install -e '/path/to/gramlot-examples/apps/hello-world[python-hosts]'
python -m gramlot_example_app.server.fastapi
```

Open <http://127.0.0.1:8000/>. The launcher imports the installed Python page
and uses `NativeHtmlApplication` directly. For an existing FastAPI application:

```python
from fastapi import FastAPI
from gramlot_fastapi import mount_native_html

app = FastAPI()
pages = mount_native_html(app, "/path/to/pages")
```

`pages` is a directory of trusted Python Page modules. `NativeHtmlApplication`
provides a ready-made app. See the [native host contract](docs/050-native-html.md)
for routes, ownership and request limits.

## Historical PoC profile

`GramlotApplication`, `mount_gramlot`, `PageCollection`, the
`gramlot-fastapi serve` command, Genropy integration, SQLAlchemy reader,
inspector and showcase use the older `gramlot-poc` Page/recipe/RPC API. They are
preserved as experimental evidence and are outside native 0.1.0 compatibility;
their imports require modules absent from the clean core. The older
[specification](SPECIFICATION.md) and [database guide](docs/035-sqlalchemy.md)
retain their historical scope. Do not use these entry points as a native launcher.

## Development

`main` is the consolidated reference; development proceeds on `develop` until
verified and accepted. Run the native protocol tests and strict Sphinx build
from the prepared development environment; the full check script still covers
the historical PoC profile. The [release guide](docs/020-release.md)
distinguishes local artifacts from any later publication. Package publication and
deployment need separate authorization.

Apache License 2.0. Copyright 2026 Softwell S.r.l. See LICENSE and NOTICE.
