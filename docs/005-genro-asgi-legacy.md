# 005 · Genro ASGI and GenroPy legacy

Historical PoC integration. Its 2026-09-16 privacy and clean-core status
statements below were superseded: the PoC is public and clean Gramlot 0.1.0 is
locally buildable. This guide's CLI and database APIs remain outside native
0.1.0. Use [GA-010](010-native-html.md) for the current release path.

Document ID: **GA-005**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-kajenn/blob/develop/docs_llm/005-genro-asgi-legacy.md).

<a id="ga-005-005"></a>

## 005 · Scope and evidence

Block ID: **GA-005-005**.

Owner direction, 2026-09-16: keep `gramlot-poc` private for now and begin
Genro ASGI hosting with GenroPy legacy database integration. SQLAlchemy is not
part of this first implementation. The clean Gramlot repository defines policy,
but contains no installable runtime; this adapter uses the authorized local PoC.

Reviewed evidence includes genro-asgi's `genro_asgi_server_app/gui/runtime.py`
(shared browser runtime), GenroPy lifecycle in `genropy_asgi/proxy/genropy_proxy.py`,
and `gramlot_fastapi/genropy.py`. The legacy adapter package
`genro-legacy-genropy` 0.1.0 contains only a namespace and cannot supply the bridge.
The PoC base revision is `e2127a1` with local changes: its shared PageRegistry and
RuntimeAssets are experimental, not a new supported public Gramlot API.

<a id="ga-005-010"></a>

## 010 · Installation and startup

Block ID: **GA-005-010**.

`uv.lock` resolves Genro ASGI 0.45.0, Gramlot PoC 0.1.5 and Bag 0.21.1.
Genro ASGI 0.46.3 requires Bag >=0.22; the current PoC requires <0.22.
The older compatible host is intentional; no resolver override is used.
`tool.uv.sources` selects the authorized sibling PoC for local development.
A private source checkout is required; no anonymous package installation is promised.

```sh
uv sync --extra dev --extra docs
uv run python -m gramlot_genro_asgi examples/plain
# Optional legacy profile, using a separately installed GenroPy checkout:
uv pip install -e /path/to/genropy/gnrpy
.venv/bin/python -m gramlot_genro_asgi examples/genropy --instance YOUR_INSTANCE
```

The CLI binds localhost:8065. Open `/page/hello/` or `/page/database/` respectively.
The legacy example only executes `SELECT 1`; no business tables or records change.
Use the venv interpreter after installing legacy dependencies; `uv sync` may remove
unlocked packages. A host can also compose the adapter directly:

```python
from genro_asgi import BaseServer
from gramlot_genro_asgi.genropy import GenropyApplication

# legacy_app is an initialized, caller-owned gnr.app.gnrapp.GnrApp.
application = GenropyApplication("examples/genropy", genropy_application=legacy_app)
server = BaseServer(applications=[application])
server.serve(host="127.0.0.1", port=8065)
```

<a id="ga-005-015"></a>

## 015 · Contract and ownership

Block ID: **GA-005-015**.

1. Discover flat `pages/*.py` through shared PageRegistry. Every Source/Data
   invocation creates a fresh page. Only `main` and explicitly decorated services
   are exposed; Source and Data roles are checked separately.
2. GET supplies HTML, Source recipes and runtime assets. POST supplies TYTX RPC
   with a one-MiB body limit. Assets are confined to the runtime directories;
   immutable build assets receive long caching. Application failures return a
   generic error to clients and detailed server logs.
3. GenropyPage.db is lazy and synchronous-only. Initialization, query execution,
   result serialization, connection close and environment clearing run within one
   worker invocation. Failures still close/reset; pages must return materialized
   portable TYTX values, not legacy cursors, lazy results or unresolved Bags.
4. The caller owns GnrApp. No automatic commit, shutdown of that shared object,
   schema migration or guessed instance is performed by the adapter. Applications
   own explicit transactions, queries, authorization and any user environment.
5. Plain hosting imports no GenroPy. Server-neutral database contracts still belong
   to Gramlot; this profile is a host lifecycle bridge, not a generic dbSelect or
   dataRecord implementation. No authentication or legacy permission inheritance
   is supplied. Put access controls around nonlocal/private data access.

<a id="ga-005-020"></a>

## 020 · Verification and remaining work

Block ID: **GA-005-020**.

Run `python scripts/check.py`: lint, tests and strict Sphinx build. Tests exercise
real BaseServer HTTP dispatch, recipes, RPC roles/validation, assets, worker-local
cleanup on success/error, concurrent invocations and rejection of async DB use.
With GenroPy installed, an isolated real GnrApp and temporary SQLite database
exercise the read-only example; this test skips explicitly otherwise.

PostgreSQL, application-table queries, inherited legacy permissions, WebSocket
RPC, subscriptions, multiworker deployment, cross-host database contracts and
SQLAlchemy are outside this slice. The temporary SQLite check does not imply
full legacy model compatibility. No release, public repository conversion or
live deployment is performed by this implementation.

The documentation uses the classic Read the Docs theme. GA is this repository's
namespace; paired paths/IDs/anchors match. Legacy getting-started/architecture
paths are retained with mirrors; numbering migration remains pending.
