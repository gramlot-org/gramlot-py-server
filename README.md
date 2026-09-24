<p align="center">
  <img src="docs/_static/gramlot-logo.png" alt="Gramlot logo" width="160">
</p>

# gramlot-flask

Gramlot native HTML Pages hosted by Flask. The 0.1.0 profile uses
`mount_native_html` and the clean core's neutral Host. It is a local release
candidate; no registry publication is claimed.

## Run the native Hello World

In a Python 3.11+ environment, install the locally built core wheel and all
three adapter wheels, then the example application with its `python-hosts`
extra. Build each adapter wheel from its checkout first:

```sh
python -m pip install /path/to/gramlot-0.1.0-py3-none-any.whl \
  /path/to/gramlot_fastapi-*.whl /path/to/gramlot_flask-*.whl \
  /path/to/gramlot_genro_asgi-*.whl
python -m pip install -e '/path/to/gramlot-examples/apps/hello-world[python-hosts]'
python -m gramlot_example_app.server.flask
```

Open <http://127.0.0.1:8000/>. The launcher mounts the installed Python Page
through `mount_native_html`. To use an existing Flask application:

```python
from flask import Flask
from gramlot_flask import mount_native_html

app = Flask(__name__)
pages = mount_native_html(app, "/path/to/pages")
```

See the [native host contract](docs/025-native-html.md) for route and lifecycle
details. This profile has no database or Microblog integration.

## Historical PoC profile

The following Microblog and `gramlot-flask serve` instructions use the older
`gramlot-poc` Page/recipe/RPC API. They are retained as experimental history,
outside native 0.1.0 compatibility; their imports require modules absent from
the clean core. Do not use them as native 0.1.0 launch commands.

### Run the historical Microblog demo

From this checkout, with Python 3.11+ and uv:

```sh
uv sync --extra demo
uv run gramlot-flask
```

Open http://127.0.0.1:8073/ and sign in as **demo**, password **gramlot-demo**.
The **Gramlot** navigation link opens the community explorer. Search for a member
to see their profile, follower counts and latest posts, or open the original
Microblog profile. A posts grid drives the selected-post preview. The SPA header
includes a Python source button and an inspector icon. Both interfaces use the
same database and login session.

The first run seeds six users, 24 posts, follow relationships and six messages.
The separate SQLite demo database persists in the platform's `gramlot-flask`
application configuration directory. Subsequent launches preserve edits. To use
another directory or port:

```sh
uv run gramlot-flask demo --data-dir /path/to/demo-data --port 8074
```

The command binds to loopback, without debug mode or a reloader. Stop it with
Ctrl+C. This is a local development demonstration, not a production deployment.
Search backed by Elasticsearch, translation, password-reset email and background
exports are not configured. Original Microblog styling uses external CDNs.

Microblog's application source is included under its MIT license, with the exact
revision recorded in [its provenance](src/gramlot_flask/_vendor/microblog/PROVENANCE.md).
The added Gramlot page is Python-authored and uses shared components, bindings,
database services and remote Source. No installation-time checkout or runtime
download of Microblog is needed. There is no claimed PyPI release.

### Historical PoC hosting

Plain hosting does not require Microblog or SQLAlchemy:

```sh
python -m pip install .
gramlot-flask serve /path/to/application
```

The directory must contain `pages/*.py`, with a `Page(WebPage)` class in each file.
To integrate with an existing Flask app:

```python
from flask import Flask
from gramlot_flask import mount_gramlot

app = Flask(__name__)
collection = mount_gramlot(app, "/path/to/application")
```

Pages are mounted at `/gramlot/<name>/`. The caller owns an optional `db_handler`
and its shutdown. `access_check` can protect all page, recipe and service routes;
plain hosting is public unless the caller provides that callback.

## Development

For native 0.1.0, run the focused native tests and strict documentation build
against the clean core. The full check script and demo-oriented CI below still
cover the historical PoC profile and are not a native release gate.

```sh
uv sync --extra dev --extra docs
uv run python scripts/check.py
uv run python -m build
uv run python -m twine check dist/*
git config core.hooksPath hooks
```

Checks include Ruff, real Flask/Microblog behavior tests, paired-guide validation
and both Sphinx builds. Mypy is advisory. CI verifies installed-wheel hosting and
the demo outside the checkout. See [development](docs/010-development.md) and
[SPECIFICATION.md](SPECIFICATION.md).

`develop` carries new work; `main` is the consolidated reference after verification
and owner acceptance. Read the Docs configuration is provided, but external hosting
is not connected. No automatic package publication or deployment is configured.

## License

Adapter: Apache License 2.0, copyright 2026 Softwell S.r.l. See LICENSE and NOTICE.
Bundled Microblog: MIT, copyright Miguel Grinberg; its notice is retained.
