# 905 · Architecture

Document ID: **GP-905**.

Derived from a guide of the archived gramlot-uvicorn repository.

[Paired view](../../docs/internal/905-architecture.md).

<a id="gp-905-005"></a>

## 005 · One module per framework

Block ID: **GP-905-005**.

`src/gramlot_py_server/` holds one module per framework: `uvicorn.py`,
`django.py`, `flask.py`, `fastapi.py` and `kajenn.py`. Each module imports the
core `gramlot.server`, the standard library and its own framework, which
arrives with the extra of the same name. `kajenn.py` also imports
`genro_routes`, a dependency of Kajenn. `uvicorn.py` imports no framework: it
is a plain ASGI callable, and the extra `uvicorn` installs only the server that
runs it. An adapter module imports no other adapter module; it imports
`scaffold` and `gallery` of the package for its verbs (section 020).

There is no shared module for the HTTP contract. Each adapter module defines its
own copy of the small constants and helpers: `OWNER_COOKIE = "gramlot_owner"`,
`COMPANION_MEDIA_TYPES` for `.css` and `.js`, `THEMES`, `THEME_MEDIA_TYPES` and
`theme_file`. Each module has one `_operation` (Kajenn: `operation`) for
`/gramlot/rpc` and `/gramlot/close`: it checks the media type (415), decodes
the body as UTF-8 (400), passes the text of `rpc` to `GramlotServer.call`
(400 on `InvalidRequest`, 200 with the response envelope otherwise) and reads
`{pageId}` of `close`. The size limit `MAX_REQUEST_BYTES = 4096` and its 413
left with core 0.2.14, which fixes no size. A change to the common contract is
made in all five modules, with their tests.

| Module | Public names | Framework object |
| --- | --- | --- |
| `uvicorn.py` | `Application`, `create_application` | an ASGI callable with `http` and `lifespan` scopes |
| `django.py` | `Pages` | the URL patterns `Pages.urlpatterns`, which include `Pages.urls` |
| `flask.py` | `Pages`, `mount_pages` | a `Blueprint` from `Pages.blueprint()` |
| `fastapi.py` | `Pages`, `mount_pages`, `Application` | an `APIRouter` included by `Pages.mount(app)`; `Application` is a `FastAPI` subclass |
| `kajenn.py` | `Application` | a Kajenn `RoutedApplication` with the branches `assets` and `gramlot` |

<a id="gp-905-010"></a>

## 010 · GramlotFileServer and the mount prefix

Block ID: **GP-905-010**.

Every adapter builds the core `GramlotFileServer` on the pages folder with the
root-relative URLs `/assets/gramlot.js`, `/gramlot/rpc` and `/gramlot/close`,
and passes `page_ttl` and `max_pages` to it. The URLs carry no
prefix. The adapter passes the mount prefix to `open_page` as `prefix`; the core
adds it once to every root-relative URL of the bootstrap document. The request
path carries the prefix and the adapter, or its framework, removes it before
the routes of the adapter see the path: the application itself for Uvicorn,
`include()` in `Pages.urlpatterns` for Django, `url_prefix` for Flask, the
router `prefix` for FastAPI, the Kajenn server for Kajenn. A path outside the
prefix answers 404. The prefix without the final slash answers 301 to the
prefix with it: the explicit rule `/py` in Uvicorn, Django, Flask and FastAPI,
the ASGI `raw_path` in Kajenn, where the server routes `/py` and `/py/` alike.
Until 0.2.1 the Uvicorn application expected the prefix removed by a front
server; on 2026-10-04 the owner aligned it with the other four.

Uvicorn, Django, Flask and FastAPI take the prefix as `mount_path` and
normalize it to `""` or `/name`. Kajenn uses the application `mount`, which
must be one lowercase segment, and passes `/<mount>`.

<a id="gp-905-015"></a>

## 015 · Companions and Page.css files

Block ID: **GP-905-015**.

GET and HEAD serve a file of the pages folder whose name ends in `.css` or
`.js`: the `GramlotFileServer` companions `foo.css`, `foo.js` and `foo_aux.js`, the
relative imports of a page module, and `Page.css` files placed in the folder
(GC-090 §030 of the core: `.css` and `.js` from core 0.2.5, `.css` and `_aux.js`
until 0.2.4). This package serves `.js` files from 0.2.2; 0.2.1 served `.css`
and `_aux.js`. The real path of the file must stay below the pages folder, as
in `GramlotFileServer.url`. Every other file, including `.py` and `.md`,
answers 404. A `Page.css` URL outside the pages folder is an asset of the
application, which serves it itself. Each adapter checks the companion suffix
before it treats the path as a page path. Before it opens a page, each adapter
removes `index.html` from a path that ends in `/index.html`, so
`/<path>/index.html` opens the page `<path>` and `/index.html` the page
`index`, as on a static host and as in gramlot-js-server (owner decision of
2026-10-04).

GET and HEAD of `/themes/…` serve every file below `gramlot/resources/themes`
of the installed core, as the runtime: `theme_file(path)` in each module
returns an `assets` entry, with the media type of the extension. The table is
`THEME_MEDIA_TYPES` first, then `MimeTypes()`, the built-in table, which ignores
the system files. `THEME_MEDIA_TYPES` holds the types the built-in table lacks
in some Python version: `.woff`, `.woff2`, `.ttf`, `.otf` and `.webp` in every
one, `.md` before 3.12 (the CI on 3.11 found it). `text/*` types carry
`charset=utf-8`. A path the core does not have goes on, so a `themes/` folder
of the application below the pages folder is still served as companions.

The option `assets` maps URLs below the prefix to `{"file", "type"}`, the form
of `build_gallery` of `gramlot-examples`. Each adapter looks the path up in the
map after the runtime and the core themes, and before the companions. In Kajenn the branch `assets`
captures the paths below `assets/`; its `index` route passes them back to the
`index` route of the application, so a map URL such as
`/assets/branding/logo.svg` reaches the map.

<a id="gp-905-020"></a>

## 020 · The gramlot command

Block ID: **GP-905-020**.

`cli.py` holds `main`, the console script `gramlot`. It reads the names of the
entry points of the group `gramlot_py_server.commands`, parses the first
argument against them and loads only that entry point: the function
`commands(verbs)` of the adapter module. A `ModuleNotFoundError` while it loads
becomes the message that names the extra. Each verb sets `run` on its parser.

- `scaffold.py`: `add_new` and `new_project`. The project is the copy of
  `templates/<environment>/` and `templates/pages/`, the README quick start;
  `tests/test_readme.py` compares them.
- `gallery/__init__.py`: `add_gallery`, `stage` and `run_gallery`. `stage`
  writes the pages of GE-010 section 025 of `gramlot-examples` into a temporary
  folder and returns the `assets` of `build_gallery` with each logic module as
  JavaScript. `gallery/<environment>/` holds the catalogue of each environment;
  its page and module are copies of the templates, checked by
  `tests/test_gallery.py`.
- `serve(pages, *, host, port, **options)` in each adapter module runs the
  server of the framework: `uvicorn.run`, `Flask.run`, Django `runserver` with a
  `ROOT_URLCONF` object (`_URLconf`: Django caches the resolver by it, so it
  must be hashable), Kajenn `AsgiServer.serve` with a site declared in code.
  The gallery and `scripts/serve_adapter.py` use it.

`uvicorn.py` and `fastapi.py` import Uvicorn inside `serve`, so
`gramlot_py_server.uvicorn` still imports no framework and FastAPI without
Uvicorn imports. Kajenn accepts an empty
`mount`, the site root, for the gallery without prefix.
