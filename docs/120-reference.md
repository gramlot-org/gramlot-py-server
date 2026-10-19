# 120 · Uvicorn reference

Document ID: **GP-120**.

Derived from a guide of the archived gramlot-uvicorn repository.

[Paired view](../docs_llm/120-reference.md).

<a id="gp-120-005"></a>

## 005 · Python API

Block ID: **GP-120-005**.

`from gramlot_py_server.uvicorn import Application, create_application`

Module functions, outside `__all__`:

- `serve(pages, *, host="127.0.0.1", port=8000, **options)`: runs Uvicorn with
  `create_application(pages, **options)` until it stops. Uvicorn must be installed.
- `commands(verbs)`: adds the verbs `new` and `gallery` of `gramlot uvicorn`, an
  entry point of `gramlot_py_server.commands` ([The gramlot command](020-command.md)).

- `create_application(pages, **options) -> Application`: builds the
  application. `options` are those of `Application`.
- `Application(pages, *, mount_path="", page_ttl=1800, max_pages=1000,
  content_security_policy=None, assets=None, collections=())`: the ASGI callable,
  a subclass of `gramlot_py_server.base.Adapter` (section 020). It handles the
  `http` and `lifespan` scopes. Any other scope type raises `ValueError`
  ("Application supports HTTP only"). On `lifespan.shutdown` it calls
  `shutdown()` and forgets every open page.
  - `gramlot_server`: the core `GramlotFileServer` built on `pages` with the URLs
    `/assets/gramlot.js`, `/gramlot/rpc`, `/gramlot/close`.
  - `mount_path`: the normalized prefix (`""` or `/py`).
  - `content_security_policy`: the configured policy or `None`.
  - `assets`: the map of URLs to files, `{}` when not given.
  - `shutdown()`: forgets every open page.

The adapter does not expose the option `css_theme` of `GramlotServer`: the base
theme is `gramlot-base` for every page, and a page changes it with
`Page.css_theme`.

The core exceptions `PageNotFound`, `ServerCapacity` and `InvalidRequest` are
mapped to HTTP answers below. `GramlotServer.call` answers every other failure
of a call as an outcome inside the response envelope: `page_expired`,
`not_found`, `not_authenticated`, `not_authorized`, `application_error`. Any
other exception raised while a page is opened, including an exception of the
page's own code and `InvalidResourceName`, propagates to the ASGI server, which
answers 500.

<a id="gp-120-010"></a>

## 010 · HTTP endpoints

Block ID: **GP-120-010**.

All paths are shown without the mount prefix. With a prefix, the request path
carries it; a path outside it answers 404 `Not found`, and the prefix without
the final slash answers 301 with `Location: /py/` and the query string. Every
response carries `Content-Length` and `Cache-Control: no-store`, except the
runtime, which carries `Cache-Control: no-cache`. Error bodies are plain text.

| Method and path | Answer |
| --- | --- |
| `GET /<page path>` | 200 `text/html`, the bootstrap document, with `Set-Cookie: gramlot_owner=…` and, when configured, `Content-Security-Policy`; 404 `Page not found`; 503 `Page capacity reached` |
| `GET /<page path>/index.html`, `GET /index.html` | as `GET /<page path>` for the page `<page path>`, as `GET /` for the page `index` |
| any other method on a page path, `HEAD` included | 405, `Allow: GET` |
| `GET`, `HEAD /assets/gramlot.js` | 200 `text/javascript`, the runtime packaged with the core |
| `GET`, `HEAD /themes/<file>` | 200, the file of the core themes with the media type of its extension; a file the core does not have goes on to the rows below |
| `GET`, `HEAD` of a URL of `assets` | 200, the file with the media type of the map |
| `GET`, `HEAD /<file>.css`, `/<file>.js` | 200 `text/css` or `text/javascript` when the real path is below the pages folder; 404 `Not found` otherwise |
| `GET`, `HEAD /app.webmanifest` | 200 `application/manifest+json` for an installable root page; 404 `Not found` otherwise |
| other methods on the runtime, themes, assets, companions and `/app.webmanifest` | 405, `Allow: GET, HEAD` |
| `POST /gramlot/rpc` | body: the request envelope `{"id", "pageId", "contentType", "name", "params"}` as TYTX JSON text, passed to `GramlotServer.call`; 200 `application/json`, the response envelope `{"id", "contentType", "value"}` or `{"id", "contentType", "error": {"code", "name", "message"}}`; 400 `Invalid envelope` when `call` raises `InvalidRequest` |
| `POST /gramlot/close` | body `{"pageId": "…"}`; 200 `{"ok": true}`; 400 `Invalid JSON request` otherwise |
| other methods on `/gramlot/*` | 405, `Allow: POST` |

Declare Source fragments with `@source` and mount them with `remote`;
use `dataRpc` for endpoint values and `dataRemote` for lazy Data. See
[Calling the server](https://github.com/gramlot-org/gramlot/blob/main/docs/public/098-server-calls.md#gc-095-100)
and [Remote content and lazy Data](https://github.com/gramlot-org/gramlot/blob/main/docs/public/099-remote-content.md#gc-095-105).

Common answers of the two protocol endpoints: 415
`Expected application/json`; 400 `Request body is not UTF-8` (a leading byte
order mark is removed). No body size is fixed. A page ID that is expired, unknown or owned by another cookie is the
outcome `page_expired` of `/gramlot/rpc`; `close` answers `{"ok": true}` to it
and forgets nothing. The `contentType` `source` with the name `main` is the
whole page, another name a fragment; `data` names an `@endpoint` method. No
`auth` capability is announced: an endpoint with an `auth` rule answers
`not_authenticated`. The Kajenn adapter announces it ([Kajenn](505-kajenn.md)).

<a id="gp-120-015"></a>

## 015 · Bootstrap document

Block ID: **GP-120-015**.

The HTML answered for a page, by every adapter: `<!doctype html>`,
`<meta charset="utf-8">`, the `Page.title`, `<div id="gramlot-root">`, a
`<script type="importmap" nonce="…">` that maps `@gramlot/gramlot/page` to the
runtime URL, and one `<script type="module" nonce="…">`. The script imports `PageBootstrap` from
the runtime URL and runs it with
`{"config": {"pageId", "rpcUrl", "closeUrl", "rootId", "capabilities", "nameSyntax"},
"resources": {"css": [url…], "js": [{"url", "group"}…]}}`. `config` also has
`devices`, `locale` and `timeZone` when the page declares them; `resources` also
has `collections` when the adapter has them. The URLs carry the
mount prefix; `capabilities` is `[]` in every adapter of this package except
Kajenn, where it is `["auth"]`. `nameSyntax` is the syntax of a method name that
the core server declares. `css` starts with the theme of the page (the base
theme `/themes/gramlot-base/theme.css`), then the `Page.css` URLs and the
companion stylesheet. The logic module, `<page>.js` or `<page>_aux.js`, when
the page has one, has `"group": null`.

<a id="gp-120-020"></a>

## 020 · The shared base

Block ID: **GP-120-020**.

`from gramlot_py_server import base`

The five adapters inherit from `base.Adapter`, which writes the HTTP rules of the
[server protocol](https://gramlot.readthedocs.io/en/latest/docs/public/101-server-protocol.html),
Part B, once. Its names are common to every adapter:

- `Adapter(pages, *, mount_path="", page_ttl=1800, max_pages=1000,
  content_security_policy=None, assets=None, collections=())`: builds
  `gramlot_server` from `server_class(pages, page_ttl=…, max_pages=…,
  collections=…)`. `server_class` is `GramlotFileServer`; the Kajenn adapter
  replaces it with a subclass that has the capability `auth`. Other keyword
  arguments reach the next class in the order of the adapter class: Kajenn's
  `RoutedApplication`; in the other adapters they raise `TypeError`.
- `gramlot_server`, `mount_path`, `content_security_policy`, `assets`.
- `handle(request) -> Reply` (a coroutine): answers one request below the mount
  prefix. The order is: the web manifest, the runtime, the core themes, `assets`,
  the companions, the rpc and close URLs, the pages.
- `shutdown()`: forgets every open page (`close_all`); `close_at_exit()`: the
  same when the interpreter exits or the adapter is collected, for a framework
  with no shutdown hook; it returns the `weakref.finalize`.
- `reply(status, body, content_type, headers, cache_control)`, `refuse(*allowed)`
  (the 405 with `Allow`), `redirect(query)` (the 301 of the bare prefix),
  `owner_cookie(owner)` (the `Set-Cookie` value: `Path`, `HttpOnly`,
  `SameSite=Lax`, no lifetime) and `owner_of(cookie_header)`.
- `METHODS`, `OWNER_COOKIE` (`gramlot_owner`), `COMPANION_MEDIA_TYPES`,
  `THEME_MEDIA_TYPES`.
- `base.Request(method, path, body, query="", content_type="", owner=None,
  identity=None)`: the request in the terms of the adapters. `path` is below the
  mount prefix and decoded once; `body` is a coroutine function that reads the
  body when `handle` asks for it; `owner` is the value of the owner cookie;
  `identity` is passed to `GramlotServer.call`. `base.stored(data)` makes a
  `body` from bytes that the framework has already read.
- `base.Reply(status, body, content_type, headers)`: the response; `headers` are
  `(name, value)` pairs, `Cache-Control` included.

An adapter adds its routes, the translation of its framework request into a
`Request`, the translation of a `Reply` into its response, and its shutdown.

