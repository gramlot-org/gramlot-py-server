# 005 · Introduction

Document ID: **GP-005**.

Derived from a guide of the archived gramlot-uvicorn repository.

[Paired view](../docs/005-introduction.md).

<a id="gp-005-005"></a>

## 005 · What this package does

Block ID: **GP-005-005**.

Gramlot describes a web interface in Python or JavaScript and keeps it bound to
the application state in the browser. The core guide
[The Gramlot family](https://gramlot.readthedocs.io/en/latest/docs/public/055-family.html)
explains Page, Source, Data, logic and `GramlotServer`, and lists the repositories.

`gramlot-py-server` serves Gramlot pages written in Python from a Python web
server. It holds one adapter module per framework. Each adapter takes a folder
of Python `Page` modules and serves it through the core `GramlotFileServer`:

- it opens a page when a browser asks for it and answers the bootstrap document;
- it serves the Gramlot browser runtime and the themes packaged with the core;
- it serves the page companions, the `.css` and `.js` files below the pages
  folder: stylesheets and the page modules that hold the page `Logic`;
- it serves the files of an optional assets map;
- it answers the main and Source requests of the running page;
- it forgets the page when the browser closes it.

The adapters do not render HTML from the Source and do not run page logic. The
browser runtime does both. The package does not serve JavaScript pages
([gramlot-js-server](https://github.com/gramlot-org/gramlot-js-server) does) and
does not talk to a database.

<a id="gp-005-010"></a>

## 010 · Extras and modules

Block ID: **GP-005-010**.

Python 3.11 or later. The package declares `gramlot>=0.2.12`. Each adapter comes
with the extra of the same name, which installs its framework:

| Extra | Module | Names | Guide |
| --- | --- | --- | --- |
| `uvicorn` | `gramlot_py_server.uvicorn` | `Application`, `create_application(pages, **options)` | [Uvicorn tutorial](105-tutorial.md) |
| `django` | `gramlot_py_server.django` | `Pages`; its `urlpatterns` go into a URLconf | [Django](205-django.md) |
| `flask` | `gramlot_py_server.flask` | `Pages`, `mount_pages(app, pages, **options)` | [Flask](305-flask.md) |
| `fastapi` | `gramlot_py_server.fastapi` | `Pages`, `mount_pages(app, pages, **options)`, `Application` | [FastAPI](405-fastapi.md) |
| `kajenn` | `gramlot_py_server.kajenn` | `Application`, a Kajenn `RoutedApplication` | [Kajenn](505-kajenn.md) |
| `gallery` | `gramlot_py_server.gallery` | `gramlot <environment> gallery`; installs `gramlot-examples` | [The gramlot command](020-command.md) |

```sh
python -m pip install "gramlot-py-server[flask]"
```

Each module imports only its own framework. Importing the Django, Flask,
FastAPI or Kajenn module without its extra raises `ImportError`.
`gramlot_py_server.uvicorn` imports no framework: it is a plain ASGI
application, and the extra `uvicorn` installs the server that runs it. The
extras `test` and `docs` install the test suite and the documentation build.

The package installs the command `gramlot <environment> <verb>`:
`gramlot django new my-site` writes the quick start project of a framework,
`gramlot django gallery` serves the example gallery with its adapter. See
[The gramlot command](020-command.md).

<a id="gp-005-015"></a>

## 015 · A request on these hosts

Block ID: **GP-005-015**.

For a page `hello.py` in the pages folder, served without a mount prefix. All
five adapters answer the same paths:

1. **Page URL.** The browser requests `GET /hello`. The adapter asks the core
   `GramlotFileServer` for the page: `hello.py`, or `hello/hello.py`. The core registers
   a new page ID for this browser. The adapter answers the bootstrap document: a
   small HTML page with the title, an empty root `div` and one module script
   that carries a nonce. The response sets the cookie `gramlot_owner`.
2. **Bootstrap.** The module script imports the runtime from
   `/assets/gramlot.js`. It runs `PageBootstrap` with the page ID, the URLs of
   the main, source and close endpoints, and the resources of the page: the
   `Page.css` URLs, the companion stylesheet `hello.css` and the module that
   holds the page logic: `hello.js` beside the page file, else `hello_aux.js`.
   An import map before the script maps `@gramlot/gramlot/page` to the runtime
   URL, so the page module imports the runtime already loaded.
3. **Main.** The runtime posts `{"pageId": …}` to `/gramlot/main`. The adapter
   runs `Page.main(root)` on the server and answers the Source tree as TYTX. The
   runtime renders the DOM from it and installs the data binding.
4. **Source.** The adapter answers `POST /gramlot/source` with
   `{"pageId", "method", "params"}`. The runtime mounts the returned branch.
   Source methods (`@source`, `remoteSource`) are not yet part of the page-writing API:
   they arrive together with the `remote` grammar attribute and `@endpoint`.
5. **Close.** When the browser disposes the page, or leaves it without keeping
   it in the back/forward cache, the runtime posts `{"pageId": …}` to
   `/gramlot/close`. The adapter forgets the page. A page that is never closed
   expires after `page_ttl` seconds.

<a id="gp-005-020"></a>

## 020 · Mount prefix

Block ID: **GP-005-020**.

The mount prefix is the path before the URLs of the adapter, for example
`/py`. Every adapter passes it to `open_page` as `prefix`. The core adds it once
to the root-relative URLs of the bootstrap document: runtime, main, source,
close, companions and root-relative `Page.css` URLs. The owner cookie is set
with `Path=/py`, or `Path=/` without a prefix.

How the prefix is given depends on the framework:

| Adapter | Option | Who removes the prefix from the request path |
| --- | --- | --- |
| Uvicorn | `mount_path` | the application |
| Django | `mount_path` | `Pages.urlpatterns` in the URLconf |
| Flask | `mount_path` | the blueprint `url_prefix` |
| FastAPI | `mount_path` | the router `prefix` |
| Kajenn | the Kajenn `mount` of the application; `""` for the site root | the Kajenn server |

The request paths carry the prefix: `/py/hello`, `/py/assets/gramlot.js`. The
adapter removes it and answers 404 to every path outside it. A proxy in front
of the adapter passes the path unchanged. The prefix without the final slash,
`/py`, answers 301 to `/py/`, with the query string: pages link each other with
relative URLs, which resolve against `/py/`.

`mount_path` is normalized: `"py"`, `"/py"` and `"/py/"` give `/py`; `""` and
`"/"` give no prefix.

<a id="gp-005-025"></a>

## 025 · Rules common to every adapter

Block ID: **GP-005-025**.

- **Companions.** `GET` and `HEAD` answer a `.css` or `.js` file whose real
  path is below the pages folder. Every other file of the folder, including the
  `.py` pages, is not served.
- **`index.html`.** As on a static host, `GET /<path>/index.html` opens the
  page `<path>` and `GET /index.html` opens the page `index`. `/<path>/` opens
  the page `<path>` too. Another file name, such as `index.htm` or
  `<path>.html`, is not a page and answers 404.
- **Core themes.** `GET` and `HEAD` of `/themes/…` answer every file whose
  real path is below the themes folder of the core package
  (`gramlot/resources/themes`), with the media type of its extension, as the
  runtime: `Page.css = ["/themes/gramlot-base/theme.css"]` works without other
  settings. A path the core does not have goes on to the assets, the
  companions and the pages.
- **Assets.** The option `assets` maps URLs below the prefix to files:
  `{"/gallery/dist/gallery.js": {"file": path, "type": "application/javascript"}}`,
  the form that `build_gallery` of `gramlot-examples` returns. `GET` and `HEAD`
  answer the file with its media type; the map comes before the companions and
  the pages.
- **Owner cookie.** The first `GET` of a page sets `gramlot_owner` (`HttpOnly`,
  `SameSite=Lax`) with a random token when the browser sends none. `main`,
  `source` and `close` succeed only with the cookie of the owner of the page.
  The cookie identifies a browser. It is not authentication.
- **Request limit.** Protocol requests must be `POST` with
  `Content-Type: application/json`. A body above 4096 bytes answers 413.
- **Lifetime and capacity.** `page_ttl` (seconds, default `1800`) and
  `max_pages` (default `1000`) are passed to `GramlotFileServer`. A page that is not
  closed expires after `page_ttl`. The opening after `max_pages` open pages
  answers 503. A value that is not finite and positive raises `ValueError` when
  the adapter is created.
- **Content Security Policy.** `content_security_policy` is sent as the
  `Content-Security-Policy` header of each HTML page. `{nonce}` in it is
  replaced by the nonce of the bootstrap script of that opening. With `None`
  (the default) no header is sent. See
  [Uvicorn configuration](110-configuration.md) for the two profiles.
- **Process-local registry.** Open pages live in the memory of one process.
  Pages opened by one worker are unknown to another.

<a id="gp-005-030"></a>

## 030 · Earlier repositories

Block ID: **GP-005-030**.

The adapters of this package replace five repositories that were never
published on PyPI: `gramlot-uvicorn`, `gramlot-django`, `gramlot-flask`,
`gramlot-fastapi` and `gramlot-kajenn`. They are archived. Their class and
function names are not aliases in this package: use the names of the table in
section 010.
