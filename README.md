<p align="center">
  <img src="docs/_static/gramlot-logo.png" alt="Gramlot logo" width="160">
</p>

# gramlot-flask

Gramlot applications hosted by Flask.

**Status: experimental preview.** This adapter uses the checksummed Gramlot 0.1.5
PoC wheel. It does not claim compatibility with an executable consolidated core.

## Run the Microblog demo

From this checkout, with Python 3.11+ and uv:

```sh
uv sync --extra demo
uv run gramlot-flask
```

Open http://127.0.0.1:8073/ and sign in as **demo**, password **gramlot-demo**.
The **Gramlot** navigation link opens the community explorer. Search for a member
to see their profile, follower counts and latest posts, or open the original
Microblog profile. Both interfaces use the same database and login session.

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

## Host your own pages

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
