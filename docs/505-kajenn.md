# 505 · Kajenn

Document ID: **GP-505**.

Derived from GA-010 (gramlot-kajenn).

[Paired view](../docs_llm/505-kajenn.md).

`gramlot_py_server.kajenn.Application` serves a pages folder as an application
of a Kajenn site. It is a Kajenn `RoutedApplication`. The rules common to every
adapter are in the [Introduction](005-introduction.md) and in
[Writing pages for these hosts](010-writing-pages.md).

<a id="gp-505-005"></a>

## 005 · Install

Block ID: **GP-505-005**.

```sh
python -m pip install "gramlot-py-server[kajenn]"
```

The extra `kajenn` installs `kajenn>=0.1.0`, which provides the command
`kajenn`.

<a id="gp-505-010"></a>

## 010 · Create a project

Block ID: **GP-505-010**.

`gramlot kajenn new` writes the quick start project of the README
([The gramlot command](020-command.md)):

```sh
gramlot kajenn new my-site
cd my-site
python -m pip install -r requirements.txt
kajenn serve config.py --port 8000
```

Beside `pages/index.py`, `pages/index.js` and `requirements.txt` the project has
`config.py`:

`config.py`:

```python
"""Kajenn site: ``kajenn serve config.py --port 8000``, pages under ``/pages/``."""
from pathlib import Path

from kajenn.config.templates import DefaultConfiguration

from gramlot_py_server.kajenn import Application

PAGES = Path(__file__).resolve().parent / "pages"


class Site(DefaultConfiguration):
    def applications_section(self, cfg):
        cfg.applications().application(
            code="pages",
            mount="pages",
            app_class=Application,
            pages=PAGES,
            content_security_policy=(
                "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"
            ),
        ).request(body="raw")
```

Open <http://127.0.0.1:8000/pages/>. The page shows a field with `Ada` and the
text `Hello, Ada`. It has no inline code, so the project sends the strict
profile. Without `--port`, Kajenn binds this configuration to a free port
and the server log prints it. The test `tests/kajenn/test_kajenn_project.py`
creates the project and serves it through a Kajenn `AsgiServer`.

`gramlot kajenn gallery` serves the example gallery with this adapter.

<a id="gp-505-015"></a>

## 015 · Mounting and options

Block ID: **GP-505-015**.

The application is declared in the site recipe, as in the example:

- `app_class=Application` and `pages=` the pages folder.
- `mount=` the mount of the application: a single lowercase URL segment (a
  letter, then letters, digits, `_` or `-`), or `""` for the site root, without
  prefix. Any other value raises `ValueError` ("mount must be a single lowercase
  URL segment or empty") when the application is created.
- `.request(body="raw")`. The request envelope reaches `GramlotServer.call` as
  the TYTX text the browser sent, not through Kajenn's TYTX hydration. Without it every protocol request raises
  `RuntimeError` ("Application requires request(body='raw')") and answers 500.
- `page_ttl`, `max_pages`, `content_security_policy` and `assets`, with the
  meaning of the [Uvicorn options](110-configuration.md). There is no
  `mount_path` option.

The Kajenn server removes the mount from the request path. The application
passes `/<mount>` to `open_page` as the prefix of the browser URLs and uses it
as the `Path` of the owner cookie: `/pages` in the example. Kajenn routes
`/pages` and `/pages/` alike; the application tells them apart by the ASGI
`raw_path` and answers `/pages` with 301 to `/pages/`, with the query string:
pages link each other with relative URLs. A server that sends no `raw_path`
serves `/pages` as `/pages/`. With `mount=""` the application answers every
path that no other application claims, the prefix is empty and the cookie
`Path` is `/`.

<a id="gp-505-020"></a>

## 020 · What is served and Kajenn specifics

Block ID: **GP-505-020**.

- **Routes.** The branch `assets` serves `gramlot.js` with `GET` and `HEAD`;
  its `index` route passes every other path below `assets/` to the `index`
  route of the application. The branch `gramlot` holds `rpc` and `close`, which
  accept `POST`. The `index` route serves the files of `assets`,
  the pages and the companions from the remaining path segments.
- **Methods.** A page accepts `GET` only; `HEAD` answers 405. A method that a
  route does not accept answers 405 `Method not allowed`, without an `Allow`
  header.
- **Responses.** Pages, companions and protocol answers carry
  `Cache-Control: no-store`. The runtime carries
  `Content-Type: text/javascript; charset=utf-8` and `Cache-Control: no-cache`.
  Errors are Kajenn HTTP exceptions: the answer is `application/json` with the
  body `{"error": "…"}`, for example `{"error": "Invalid envelope"}`. The
  outcomes of a call are not errors: they arrive in the 200 response envelope.
- **Request body.** The application reads the raw body and passes it to
  `GramlotServer.call` as text. The adapter fixes no size, and Kajenn 0.1
  reads the whole body before the route runs; a size limit declared on the
  application is kajenn-org/kajenn#32. The media type of `Content-Type` is compared with
  `application/json`; parameters such as `charset` are ignored.
- **Cookies.** The page response carries `gramlot_owner`. In the example the
  Kajenn site also sets its own `session_id` cookie; the adapter does not read
  it.
- **Errors.** An exception of the page's own code while a page opens reaches
  Kajenn, which answers 500. In a call through `/gramlot/rpc` it is the outcome
  `application_error` of a 200 response.
- **Workers.** The page registry lives in the process. Run one worker, or keep
  a browser on the same worker.

<a id="gp-505-025"></a>

## 025 · API reference

Block ID: **GP-505-025**.

`from gramlot_py_server.kajenn import Application`

Module functions, outside `__all__`:

- `serve(pages, *, host="127.0.0.1", port=8000, mount_path="", **options)`:
  declares an `Application` with the Kajenn mount `mount_path` in a Kajenn site
  and serves it; an empty `mount_path` puts it at the site root.
- `commands(verbs)`: adds the verbs `new` and `gallery` of `gramlot kajenn`, an
  entry point of `gramlot_py_server.commands` ([The gramlot command](020-command.md)).

`Application(pages, *, page_ttl=1800, max_pages=1000,
content_security_policy=None, assets=None, **kwargs)`: the other keyword arguments go to
Kajenn's `RoutedApplication`. The site recipe passes them.

- `gramlot_server`: a subclass of the core `GramlotFileServer` built on `pages`
  with the URLs `/assets/gramlot.js`, `/gramlot/rpc`, `/gramlot/close`. Its
  `capabilities` is `["auth"]`; `record_avatar(owner, avatar)` records the avatar
  tags of an owner in `owner_tags`, at most `max_pages` owners, emptied by
  `close_all`; `evaluate_auth(rule, owner=…)` evaluates a rule against them.
- `content_security_policy`: the configured policy or `None`.
- `assets`: the map of URLs to files, `{}` when not given.
- `index`: the route of assets, pages and companions.
- `on_shutdown()`: the Kajenn lifecycle hook; it forgets every open page.
- `redirect(request)`, `static(request, asset)`, `companion(request,
  page_path, suffix)`, `operation(request, body_raw, operation)`,
  `require_method(request, *methods)`: the helpers of the routes.

Paths below are without the mount.

| Method and path | Answer |
| --- | --- |
| `GET /<page path>` | 200 `text/html; charset=utf-8`, the bootstrap document, with `Set-Cookie: gramlot_owner=…` and, when configured, `Content-Security-Policy`; 404 `Page not found`; 503 `Page capacity reached` |
| `GET /<page path>/index.html`, `GET /index.html` | as `GET /<page path>` for the page `<page path>`, as `GET /` for the page `index` |
| `GET`, `HEAD /assets/gramlot.js` | 200 `text/javascript; charset=utf-8`, the runtime |
| `GET /pages` (the mount without the final slash) | 301, `Location: /pages/` with the query string |
| `GET`, `HEAD /themes/<file>` | 200, the file of the core themes with the media type of its extension; a file the core does not have goes on to the rows below |
| `GET`, `HEAD` of a URL of `assets` | 200, the file with the media type of the map |
| `GET`, `HEAD /<file>.css`, `/<file>.js` | 200 `text/css; charset=utf-8` or `text/javascript; charset=utf-8` when the real path is below the pages folder; 404 `Not found` otherwise |
| `POST /gramlot/rpc`, `/gramlot/close` | as the [Uvicorn endpoints](120-reference.md), with JSON error bodies |
| other methods | 405 `Method not allowed` |

Source methods (`@source`, `remoteSource`) are not yet part of the page-writing API: they arrive together with the `remote` grammar attribute.

The Kajenn adapter passes the envelope to `GramlotServer.call` as the other
adapters do and announces the capability `auth`: the bootstrap `config` carries
`"capabilities": ["auth"]`. Before each call through `/gramlot/rpc` the
application records the tags of the request's Kajenn avatar (`request.avatar()`)
for the owner cookie, or no identity when the request is anonymous. The
`evaluate_auth` of `gramlot_server` evaluates an `auth` rule with
`genro_toolbox.tags_match` against those tags, the evaluation the genro-routes
`AuthPlugin` applies to route entries: no avatar answers `not_authenticated`, tags
that do not satisfy the rule answer `not_authorized`. The avatar comes from the
Kajenn site: for example a `basic_user` with `tags` under
`authentication().credentials()` of the site recipe, sent as HTTP Basic
credentials. A rule with a syntax error is the outcome `application_error`.
Registering the endpoints as genro-routes `RouterNode`s, with the OpenAPI, env
and logging plugins, belongs to genro-kajenn, not to this adapter.
