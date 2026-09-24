# gramlot-genro-asgi

Native HTML Gramlot Pages hosted by raw ASGI/Uvicorn or Kajenn/Genro ASGI.
The clean core's neutral Host supplies Page execution. This is a local 0.1.0
candidate, without a registry release or deployment claim.

## Run the native Hello World

In a Python 3.11+ environment, install the locally built Gramlot 0.1.0 wheel
and all three adapter wheels, then the example application's `python-hosts`
extra. Build each adapter wheel from its checkout first:

```sh
python -m pip install /path/to/gramlot-0.1.0-py3-none-any.whl \
  /path/to/gramlot_fastapi-*.whl /path/to/gramlot_flask-*.whl \
  /path/to/gramlot_genro_asgi-*.whl
python -m pip install -e '/path/to/gramlot-examples/apps/hello-world[python-hosts]'
python -m gramlot_example_app.server.uvicorn
```

Open <http://127.0.0.1:8000/>. For the actual Kajenn integration, launch
`python -m gramlot_example_app.server.kajenn` and open
<http://127.0.0.1:8000/page/>. The launchers use `create_asgi_application` and
`KajennNativeHtmlApplication`, respectively. The [native guide](docs/010-native-html.md)
describes their distinct contracts. This profile has no database integration.

## Historical PoC profile

The legacy GenroPy `GnrApp` example, `GramlotApplication` and
`python -m gramlot_genro_asgi` command below use PoC Page/recipe/RPC APIs.
They are preserved as experimental evidence and are outside native 0.1.0
compatibility; their imports require modules absent from the clean core.

### Historical status and scope

The historical implementation provides page discovery, Source and Data RPC dispatch,
packaged browser assets, fresh page instances and same-worker legacy database
cleanup. It uses the experimental `gramlot-poc` checkout, not the clean product core.
This is an experimental integration, not an accepted core port or a public release.
The current priority is Genro ASGI + GenroPy legacy. SQLAlchemy is outside this slice.
Plain hosting does not import GenroPy. No FastAPI or Django runtime is required.

### Historical development setup

Python 3.11+ and an authorized sibling `gramlot-poc` checkout are required:

```sh
uv sync --extra dev --extra docs
uv run python scripts/check.py
uv run python -m gramlot_genro_asgi examples/plain --port 8065
```

Open `http://127.0.0.1:8065/page/hello/`. For legacy database access, install your
GenroPy checkout into this environment and select an instance explicitly:

```sh
uv pip install -e /path/to/genropy/gnrpy
.venv/bin/python -m gramlot_genro_asgi examples/genropy --instance YOUR_INSTANCE
```

Open `http://127.0.0.1:8065/page/database/`. This example executes only `SELECT 1`.
Using `.venv/bin/python` preserves the manually installed legacy dependency;
`uv sync` may remove packages outside the lockfile.

The resolved baseline is Genro ASGI 0.45.0 + Gramlot PoC 0.1.5 + Bag 0.21.1.
Current Genro ASGI releases requiring Bag 0.22 conflict with the PoC's `<0.22`
constraint. Do not override the resolver to force that combination.

### Historical documentation and boundaries

Read the [integration contract](docs/005-genro-asgi-legacy.md), its
[concise counterpart](docs_llm/005-genro-asgi-legacy.md), and
[SPECIFICATION.md](SPECIFICATION.md). Documentation uses the classic Read the Docs
theme. New work stays on `develop`; verified, accepted work is consolidated on `main`.

Queries, permissions and explicit transaction decisions belong to application
services. The host adapter supplies execution and cleanup, not a generic database
contract. Endpoints are public unless the owning host adds access control; legacy
permissions are not inherited automatically. The CLI binds only to localhost.
No registry publication, deployment or public preview is claimed.
