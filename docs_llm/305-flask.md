# 305 · Flask

Document ID: **GP-305**.

Derived from GFL-025 (gramlot-flask).

[Paired view](../docs/305-flask.md).

`gramlot_py_server.flask` serves a pages folder from a Flask application as a
blueprint. The rules common to every adapter are in the
[Introduction](005-introduction.md) and in
[Writing pages for these hosts](010-writing-pages.md).

<a id="gp-305-005"></a>

## 005 · Install

Block ID: **GP-305-005**.

```sh
python -m pip install "gramlot-py-server[flask]"
```

The extra `flask` installs `flask>=3.1,<4`.

<a id="gp-305-010"></a>

## 010 · Run the example

Block ID: **GP-305-010**.

The example lives in the repository, beside the folder `examples/pages`.

`examples/flask/app.py`:

```python
"""Serve the example pages inside a Flask app: ``flask --app app run``."""
from pathlib import Path

from flask import Flask

from gramlot_py_server.flask import mount_pages

PAGES = Path(__file__).resolve().parents[1] / "pages"

app = Flask(__name__)
mount_pages(
    app,
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'",
)
```

From the folder `examples/flask`:

```sh
flask --app app run
```

The Flask development server listens on port 5000. Open
<http://127.0.0.1:5000/hello>. The permissive profile is sent because
`hello.py` uses inline code. The test `tests/flask/test_flask_examples.py`
serves this example with Flask's test client.

<a id="gp-305-015"></a>

## 015 · Mounting and options

Block ID: **GP-305-015**.

`mount_pages(app, pages, **options)` creates a `Pages`, registers its
blueprint on `app` and returns the `Pages`:

```python
pages = mount_pages(app, PAGES, mount_path="/py")
```

- The blueprint is registered with `url_prefix` equal to `mount_path`. Flask
  removes the prefix before the views of `Pages` see the path. The same
  `mount_path` goes to `open_page` and to the `Path` of the owner cookie.
- With a prefix the blueprint has one more rule, `/py` without the final slash,
  that answers 301 to `/py/` with the query string: pages link each other with
  relative URLs.
- The blueprint is named `gramlot_pages_` plus the mount path without its
  outer slashes, inner slashes replaced by `_`, or `root` without a prefix:
  `gramlot_pages_py` for `/py`, `gramlot_pages_root` for `""`. A second mount
  at the same path gives the same name, and Flask raises `ValueError`.
- The `Pages` is recorded in `app.extensions["gramlot_pages"][mount_path]`,
  for example `app.extensions["gramlot_pages"]["/py"]`.
- `page_ttl`, `max_pages`, `content_security_policy` and `assets` have the
  meaning of the [Uvicorn options](110-configuration.md).

`Pages(pages, **options).blueprint()` builds the blueprint without registering
it, for an application that registers blueprints itself.

<a id="gp-305-020"></a>

## 020 · What is served and Flask specifics

Block ID: **GP-305-020**.

- **Routes.** `/assets/gramlot.js` accepts `GET` and `HEAD`. `/gramlot/main`,
  `/gramlot/source` and `/gramlot/close` accept `POST`. `/` and
  `/<path:page_path>` serve the pages, the files of `assets` and the
  companions with Flask's default
  methods: `GET`, `HEAD` and `OPTIONS`.
- **`HEAD` on a page.** A `HEAD` opens a page and sets the cookie; Flask sends
  no body.
- **Other methods.** Flask answers them with its own 405 page and an `Allow`
  header. A `GET` on `/gramlot/main` matches the page route instead and
  answers 404 `Page not found`.
- **Asynchronous core.** The views are synchronous. Each call to the core
  `FileHost` runs in its own event loop through `asyncio.run`.
- **Responses.** Pages, companions and protocol answers carry
  `Cache-Control: no-store`. The runtime carries
  `Content-Type: text/javascript; charset=utf-8` and `Cache-Control: no-cache`.
  Error messages are plain text in a response with Flask's default content
  type `text/html; charset=utf-8`.
- **Request body.** A `Content-Length` above 4096 answers 413 before the body
  is read. A body longer than 4096 bytes answers 413 after it is read.
  `request.mimetype` is compared with `application/json`; parameters such as
  `charset` are not part of it.
- **Errors.** An exception of the page's own code reaches Flask, which answers
  500.
- **Workers.** The page registry lives in the process. Run one worker process,
  or keep a browser on the same one.

<a id="gp-305-025"></a>

## 025 · API reference

Block ID: **GP-305-025**.

`from gramlot_py_server.flask import Pages, mount_pages`

- `mount_pages(app, pages, **options) -> Pages`: creates the `Pages`, registers
  its blueprint and records it in `app.extensions["gramlot_pages"]`.
- `Pages(pages, *, mount_path="", page_ttl=1800, max_pages=1000,
  content_security_policy=None, assets=None)`:
  - `blueprint()`: a new `Blueprint` with the routes below.
  - `host`: the core `FileHost` built on `pages` with the URLs
    `/assets/gramlot.js`, `/gramlot/main`, `/gramlot/source`, `/gramlot/close`.
  - `mount_path`: the normalized prefix (`""` or `/py`).
  - `content_security_policy`: the configured policy or `None`.
  - `assets`: the map of URLs to files, `{}` when not given.
  - `asset`, `page`, `static`, `companion`, `main`, `source`, `close`,
    `redirect`: the views.

| Method and path | Answer |
| --- | --- |
| `GET`, `HEAD /<page path>` | 200 `text/html; charset=utf-8`, the bootstrap document, with `Set-Cookie: gramlot_owner=…` and, when configured, `Content-Security-Policy`; 404 `Page not found`; 503 `Page capacity reached` |
| `GET`, `HEAD /assets/gramlot.js` | 200 `text/javascript; charset=utf-8`, the runtime |
| `GET /py` (the bare prefix) | 301, `Location: /py/` with the query string |
| `GET`, `HEAD` of a URL of `assets` | 200, the file with the media type of the map |
| `GET`, `HEAD /<file>.css`, `/<file>.js` | 200 `text/css; charset=utf-8` or `text/javascript; charset=utf-8` when the real path is below the pages folder; 404 `Not found` otherwise |
| `POST /gramlot/main`, `/gramlot/source`, `/gramlot/close` | as the [Uvicorn endpoints](120-reference.md) |
| other methods | 405 from Flask, with `Allow`; a `GET` on `/gramlot/*` answers 404 `Page not found` |
