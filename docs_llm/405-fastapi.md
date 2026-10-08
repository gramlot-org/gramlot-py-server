# 405 · FastAPI

Document ID: **GP-405**.

Derived from GF-050 (gramlot-fastapi).

[Paired view](../docs/405-fastapi.md).

`gramlot_py_server.fastapi` serves a pages folder from a FastAPI application,
as a router added to an existing application or as a ready-made application.
The rules common to every adapter are in the
[Introduction](005-introduction.md) and in
[Writing pages for these hosts](010-writing-pages.md).

<a id="gp-405-005"></a>

## 005 · Install

Block ID: **GP-405-005**.

```sh
python -m pip install "gramlot-py-server[fastapi,uvicorn]"
```

The extra `fastapi` installs `fastapi>=0.115`. FastAPI needs an ASGI server to
run; the extra `uvicorn` installs Uvicorn. The command `fastapi dev` is not
part of either extra: it needs `pip install "fastapi[standard]"`.

<a id="gp-405-010"></a>

## 010 · Create a project

Block ID: **GP-405-010**.

`gramlot fastapi new` writes the quick start project of the README
([The gramlot command](020-command.md)):

```sh
gramlot fastapi new my-site
cd my-site
python -m pip install -r requirements.txt
uvicorn app:app
```

Beside `pages/index.py`, `pages/index.js` and `requirements.txt` the project has
`app.py`:

`app.py`:

```python
"""Serve the pages inside a FastAPI app: ``uvicorn app:app``."""
from pathlib import Path

from fastapi import FastAPI

from gramlot_py_server.fastapi import mount_pages

PAGES = Path(__file__).resolve().parent / "pages"

app = FastAPI()
mount_pages(
    app,
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)
```

Open <http://127.0.0.1:8000/>. The page shows a field with `Ada` and the text
`Hello, Ada`. It has no inline code, so the project sends the strict profile.
`requirements.txt` installs FastAPI with Uvicorn. With `fastapi[standard]`
installed, `fastapi dev app.py` also works. The test
`tests/fastapi/test_fastapi_project.py` creates the project and serves it with
FastAPI's `TestClient`.

`gramlot fastapi gallery` serves the example gallery with this adapter.

<a id="gp-405-015"></a>

## 015 · Mounting and options

Block ID: **GP-405-015**.

Two ways to serve the pages:

```python
from fastapi import FastAPI
from gramlot_py_server.fastapi import Application, mount_pages

# on an existing application
app = FastAPI()
pages = mount_pages(app, PAGES, mount_path="/py")

# as a ready-made application
app = Application(PAGES, mount_path="/py", title="Pages")
```

- `mount_pages` creates a `Pages`, calls its `mount(app)` and returns it.
  `mount` includes an `APIRouter` with `prefix` equal to `mount_path` and
  registers a `shutdown` event handler that forgets every open page.
- `Application` is a `FastAPI` subclass. It passes every option it does not
  know, `title` in the example, to `FastAPI`. It calls `mount_pages` on
  itself and keeps the result in `gramlot_pages`.
- The router removes the prefix before the routes of `Pages` see the path. The
  same `mount_path` goes to `open_page` and to the `Path` of the owner cookie.
- With a prefix the router has one more route, `/py` without the final slash,
  that answers 301 to `/py/` with the query string: pages link each other with
  relative URLs.
- `page_ttl`, `max_pages`, `content_security_policy` and `assets` have the
  meaning of the [Uvicorn options](110-configuration.md).

<a id="gp-405-020"></a>

## 020 · What is served and FastAPI specifics

Block ID: **GP-405-020**.

- **Routes.** `/assets/gramlot.js` accepts `GET` and `HEAD`.
  `/gramlot/main`, `/gramlot/source` and `/gramlot/close` accept `POST`. `/`
  and `/{page_path:path}` accept `GET` and `HEAD` and serve the pages, the
  files of `assets` and the companions.
- **`HEAD` on a page.** The adapter answers 405 with `Allow: GET`. `HEAD` on a
  companion or a file of `assets` answers 200 without a body.
- **Other methods.** FastAPI answers them with 405, the JSON body
  `{"detail": "Method Not Allowed"}` and `Allow: GET, HEAD`. A `GET` on
  `/gramlot/main`, `/gramlot/source` or `/gramlot/close` matches the page
  route, which answers 405 with `Allow: POST`.
- **Responses.** Pages, companions and protocol answers carry
  `Cache-Control: no-store`. The runtime carries
  `Content-Type: text/javascript; charset=utf-8` and `Cache-Control: no-cache`.
  Error messages are plain text bodies without a `Content-Type` header.
- **Request body.** A `Content-Length` above 4096 answers 413 before the body
  is read. The body is read in chunks and answers 413 as soon as it passes
  4096 bytes. The media type of `Content-Type` is compared with
  `application/json`; parameters such as `charset` are ignored.
- **Errors.** An exception of the page's own code reaches FastAPI, which
  answers 500.
- **Workers.** The page registry lives in the process. Run one worker, or keep
  a browser on the same worker.

<a id="gp-405-025"></a>

## 025 · API reference

Block ID: **GP-405-025**.

`from gramlot_py_server.fastapi import Application, Pages, mount_pages`

Module functions, outside `__all__`:

- `serve(pages, *, host="127.0.0.1", port=8000, **options)`: runs
  `Application(pages, **options)` with Uvicorn, which must be installed.
- `commands(verbs)`: adds the verbs `new` and `gallery` of `gramlot fastapi`, an
  entry point of `gramlot_py_server.commands` ([The gramlot command](020-command.md)).

- `mount_pages(app, pages, **options) -> Pages`: creates the `Pages` and calls
  `mount(app)`.
- `Application(pages, *, mount_path="", page_ttl=1800, max_pages=1000,
  content_security_policy=None, assets=None, **fastapi_options)`: a `FastAPI` application.
  `gramlot_pages` holds its `Pages`.
- `Pages(pages, *, mount_path="", page_ttl=1800, max_pages=1000,
  content_security_policy=None, assets=None)`:
  - `mount(app)`: includes the router and registers the shutdown handler.
  - `shutdown()`: forgets every open page.
  - `server`: the core `GramlotFileServer` built on `pages` with the URLs
    `/assets/gramlot.js`, `/gramlot/main`, `/gramlot/source`, `/gramlot/close`.
  - `mount_path`: the normalized prefix (`""` or `/py`).
  - `content_security_policy`: the configured policy or `None`.
  - `assets`: the map of URLs to files, `{}` when not given.
  - `asset`, `page`, `static`, `companion`, `main`, `source`, `close`,
    `redirect`: the endpoints.

| Method and path | Answer |
| --- | --- |
| `GET /<page path>` | 200 `text/html; charset=utf-8`, the bootstrap document, with `Set-Cookie: gramlot_owner=…` and, when configured, `Content-Security-Policy`; 404 `Page not found`; 503 `Page capacity reached` |
| `GET /<page path>/index.html`, `GET /index.html` | as `GET /<page path>` for the page `<page path>`, as `GET /` for the page `index` |
| `HEAD /<page path>` | 405, `Allow: GET` |
| `GET`, `HEAD /assets/gramlot.js` | 200 `text/javascript; charset=utf-8`, the runtime |
| `GET`, `HEAD /py` (the bare prefix) | 301, `Location: /py/` with the query string |
| `GET`, `HEAD /themes/<file>` | 200, the file of the core themes with the media type of its extension; a file the core does not have goes on to the rows below |
| `GET`, `HEAD` of a URL of `assets` | 200, the file with the media type of the map |
| `GET`, `HEAD /<file>.css`, `/<file>.js` | 200 `text/css; charset=utf-8` or `text/javascript; charset=utf-8` when the real path is below the pages folder; 404 `Not found` otherwise |
| `POST /gramlot/main`, `/gramlot/source`, `/gramlot/close` | as the [Uvicorn endpoints](120-reference.md) |
| other methods | 405 from FastAPI, with `Allow`; a `GET` on `/gramlot/*` answers 405 with `Allow: POST` |

Source methods (`@source`, `remoteSource`) are not yet part of the page-writing API: they arrive together with the `remote` grammar attribute and `@endpoint`.
