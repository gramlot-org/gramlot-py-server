# 120 · Uvicorn reference

Document ID: **GP-120**.

Derived from GS-130 (gramlot-uvicorn).

[Paired view](../docs_llm/120-reference.md).

<a id="gp-120-005"></a>

## 005 · Python API

Block ID: **GP-120-005**.

`from gramlot_py_server.uvicorn import Application, create_application`

- `create_application(pages, **options) -> Application`: builds the
  application. `options` are those of `Application`.
- `Application(pages, *, mount_path="", page_ttl=1800, max_pages=1000,
  content_security_policy=None, assets=None)`: the ASGI callable. It handles the `http` and
  `lifespan` scopes. Any other scope type raises `ValueError`
  ("Application supports HTTP only"). On `lifespan.shutdown` it forgets every
  open page.
  - `host`: the core `FileHost` built on `pages` with the URLs
    `/assets/gramlot.js`, `/gramlot/main`, `/gramlot/source`, `/gramlot/close`.
  - `mount_path`: the normalized prefix (`""` or `/py`).
  - `content_security_policy`: the configured policy or `None`.
  - `assets`: the map of URLs to files, `{}` when not given.

The core exceptions `PageNotFound`, `HostCapacity`, `PageExpired` and
`SourceNotFound` are mapped to HTTP answers below. Any other exception raised
while a page is opened or a Source method runs, including an exception of the
page's own code and `InvalidResourceName`, propagates to the ASGI server, which
answers 500.

<a id="gp-120-010"></a>

## 010 · HTTP endpoints

Block ID: **GP-120-010**.

All paths are shown without the mount prefix. With a prefix, the request path
carries it; a path outside it answers 404 `Not found`, and the prefix without
the final slash answers 301 with `Location: /py/` and the query string. Every
response carries `Cache-Control: no-store` and `Content-Length`. Error bodies
are plain text.

| Method and path | Answer |
| --- | --- |
| `GET /<page path>` | 200 `text/html`, the bootstrap document, with `Set-Cookie: gramlot_owner=…` and, when configured, `Content-Security-Policy`; 404 `Page not found`; 503 `Page capacity reached` |
| any other method on a page path, `HEAD` included | 405, `Allow: GET` |
| `GET`, `HEAD /assets/gramlot.js` | 200 `text/javascript`, the runtime packaged with the core |
| `GET`, `HEAD` of a URL of `assets` | 200, the file with the media type of the map |
| `GET`, `HEAD /<file>.css`, `/<file>.js` | 200 `text/css` or `text/javascript` when the real path is below the pages folder; 404 `Not found` otherwise |
| other methods on those paths | 405, `Allow: GET, HEAD` |
| `POST /gramlot/main` | body `{"pageId": "…"}`; 200 `application/json`, the Source of `main` as TYTX |
| `POST /gramlot/source` | body `{"pageId": "…", "method": "…", "params": {…}}`; 200, the Source branch as TYTX; 404 `Unknown Source method` |
| `POST /gramlot/close` | body `{"pageId": "…"}`; 200 `{"ok": true}` |
| other methods on `/gramlot/*` | 405, `Allow: POST` |

Common answers of the three protocol endpoints: 415
`Expected application/json`; 413 `Request too large` above 4096 bytes; 400
`Invalid JSON request` or `Source params must be a dictionary`; 404
`Unknown page` for a page ID that is expired, unknown or owned by another
cookie.

<a id="gp-120-015"></a>

## 015 · Bootstrap document

Block ID: **GP-120-015**.

The HTML answered for a page, by every adapter: `<!doctype html>`,
`<meta charset="utf-8">`, the `Page.title`, `<div id="gramlot-root">`, a
`<script type="importmap" nonce="…">` that maps `@gramlot/gramlot/page` to the
runtime URL, and one `<script type="module" nonce="…">`. The script imports `PageBootstrap` from
the runtime URL and runs it with
`{"config": {"pageId", "mainUrl", "sourceUrl", "closeUrl", "rootId"},
"resources": {"css": [url…], "js": [{"url", "group"}…]}}`. The URLs carry the
mount prefix. The logic module, `<page>.js` or `<page>_aux.js`, has
`"group": null`.
