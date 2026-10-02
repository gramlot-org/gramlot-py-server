# 905 · Architecture

Document ID: **GP-905**.

Derived from GS-005 (gramlot-uvicorn).

[Paired view](../../docs_llm/internal/905-architecture.md).

<a id="gp-905-005"></a>

## 005 · One module per framework

Block ID: **GP-905-005**.

`src/gramlot_py_server/` holds one module per framework: `uvicorn.py`,
`django.py`, `flask.py`, `fastapi.py` and `kajenn.py`. Each module imports the
core `gramlot.server`, the standard library and its own framework, which
arrives with the extra of the same name. `kajenn.py` also imports
`genro_routes`, a dependency of Kajenn. `uvicorn.py` imports no framework: it
is a plain ASGI callable, and the extra `uvicorn` installs only the server that
runs it. No module imports another module of the package.

There is no shared module. Each module defines its own copy of the small
constants: `MAX_REQUEST_BYTES = 4096`, `OWNER_COOKIE = "gramlot_owner"` and
`COMPANION_MEDIA_TYPES` for `.css` and `_aux.js`. `uvicorn.py` and
`fastapi.py` also define their own `RequestTooLarge`. A change to the common
contract is made in all five modules, with their tests.

| Module | Public names | Framework object |
| --- | --- | --- |
| `uvicorn.py` | `Application`, `create_application` | an ASGI callable with `http` and `lifespan` scopes |
| `django.py` | `Pages` | a list of URL patterns in `Pages.urls` |
| `flask.py` | `Pages`, `mount_pages` | a `Blueprint` from `Pages.blueprint()` |
| `fastapi.py` | `Pages`, `mount_pages`, `Application` | an `APIRouter` included by `Pages.mount(app)`; `Application` is a `FastAPI` subclass |
| `kajenn.py` | `Application` | a Kajenn `RoutedApplication` with the branches `assets` and `gramlot` |

<a id="gp-905-010"></a>

## 010 · FileHost and the mount prefix

Block ID: **GP-905-010**.

Every adapter builds the core `FileHost` on the pages folder with the
root-relative URLs `/assets/gramlot.js`, `/gramlot/main`, `/gramlot/source` and
`/gramlot/close`, and passes `page_ttl` and `max_pages` to it. The URLs carry no
prefix. The adapter passes the mount prefix to `open_page` as `prefix`; the core
adds it once to every root-relative URL of the bootstrap document. The
framework removes the prefix from the request path before the adapter sees it:
the front server for Uvicorn, `include()` for Django, `url_prefix` for Flask,
the router `prefix` for FastAPI, the Kajenn server for Kajenn.

Uvicorn, Django, Flask and FastAPI take the prefix as `mount_path` and
normalize it to `""` or `/name`. Kajenn uses the application `mount`, which
must be one lowercase segment, and passes `/<mount>`.

<a id="gp-905-015"></a>

## 015 · Companions and Page.css files

Block ID: **GP-905-015**.

GET and HEAD serve a file of the pages folder whose name ends in `.css` or
`_aux.js`: the `FileHost` companions `foo.css` and `foo_aux.js`, and `Page.css`
files placed in the folder. The real path of the file must stay below the pages
folder, as in `FileHost.url`. Every other file, including `.py` and `.md`,
answers 404. A `Page.css` URL outside the pages folder is an asset of the
application, which serves it itself. Each adapter checks the companion suffix
before it treats the path as a page path.
