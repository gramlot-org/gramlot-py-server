# gramlot-genro-asgi

Experimental Python-authored Gramlot applications hosted by Genro ASGI, with
optional GenroPy legacy database access through a caller-owned `GnrApp`.

## Status and scope

The first implementation provides page discovery, Source and Data RPC dispatch,
packaged browser assets, fresh page instances and same-worker legacy database
cleanup. It uses the experimental `gramlot-poc` checkout, not the clean product core.
This is an experimental integration, not an accepted core port or a public release.
The current priority is Genro ASGI + GenroPy legacy. SQLAlchemy is outside this slice.
Plain hosting does not import GenroPy. No FastAPI or Django runtime is required.

## Development setup

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

## Documentation and boundaries

Read the [integration contract](docs/005-genro-asgi-legacy.md), its
[concise counterpart](docs_llm/005-genro-asgi-legacy.md), and
[SPECIFICATION.md](SPECIFICATION.md). Documentation uses the classic Read the Docs
theme. New work stays on `develop`; verified, accepted work is consolidated on `main`.

Queries, permissions and explicit transaction decisions belong to application
services. The host adapter supplies execution and cleanup, not a generic database
contract. Endpoints are public unless the owning host adds access control; legacy
permissions are not inherited automatically. The CLI binds only to localhost.
No registry publication, deployment or public preview is claimed.
