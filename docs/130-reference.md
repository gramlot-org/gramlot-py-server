# 130 · Reference

Document ID: **GS-130**.

[Paired view](../docs_llm/130-reference.md).

<a id="gs-130-005"></a>

## 005 · Python API

Block ID: **GS-130-005**.

`from gramlot_uvicorn import NativeHtmlASGI, create_asgi_application`

- `create_asgi_application(pages, **options) -> NativeHtmlASGI`: builds the
  application; `options` are those of `NativeHtmlASGI`.
- `NativeHtmlASGI(pages, *, mount_path="", page_ttl=1800, max_pages=1000,
  content_security_policy=None)`: the ASGI callable. It handles the `http` and
  `lifespan` scopes; any other scope type raises `ValueError`. On
  `lifespan.shutdown` it forgets every open page.
  - `host`: the core `FileHost` built on `pages` with the URLs
    `/assets/gramlot.js`, `/gramlot/main`, `/gramlot/source`, `/gramlot/close`.
  - `mount_path`: the normalized prefix (`""` or `/py`).
  - `content_security_policy`: the configured policy or `None`.

The core exceptions `PageNotFound`, `HostCapacity`, `PageExpired` and
`SourceNotFound` are mapped to HTTP answers below. Any other exception raised
while a page is opened or a Source method runs, including an exception of the
page's own code and `InvalidResourceName`, propagates to the ASGI server, which
answers 500.

<a id="gs-130-010"></a>

## 010 · HTTP endpoints

Block ID: **GS-130-010**.

All paths are without the mount prefix. Every response carries
`Cache-Control: no-store` and `Content-Length`.

| Method and path | Answer |
| --- | --- |
| `GET /<page path>` | 200 `text/html`, the bootstrap document, with `Set-Cookie: gramlot_owner=…` and, when configured, `Content-Security-Policy`; 404 `Page not found`; 503 `Page capacity reached` |
| any other method on a page path | 405, `Allow: GET` |
| `GET`, `HEAD /assets/gramlot.js` | 200 `text/javascript`, the runtime packaged with the core |
| `GET`, `HEAD /<file>.css`, `/<file>_aux.js` | 200 `text/css` or `text/javascript` when the real path is below the pages folder; 404 `Not found` otherwise |
| other methods on those paths | 405, `Allow: GET, HEAD` |
| `POST /gramlot/main` | body `{"pageId": "…"}`; 200 `application/json`, the Source of `main` as TYTX |
| `POST /gramlot/source` | body `{"pageId": "…", "method": "…", "params": {…}}`; 200, the Source branch as TYTX; 404 `Unknown Source method` |
| `POST /gramlot/close` | body `{"pageId": "…"}`; 200 `{"ok": true}` |
| other methods on `/gramlot/*` | 405, `Allow: POST` |

Common answers of the three protocol endpoints: 415 `Expected
application/json`; 413 `Request too large` above 4096 bytes; 400 `Invalid JSON
request` or `Source params must be a dictionary`; 404 `Unknown page` for a page
ID that is expired, unknown or owned by another cookie.

<a id="gs-130-015"></a>

## 015 · Bootstrap document

Block ID: **GS-130-015**.

The HTML answered for a page: `<!doctype html>`, `<meta charset="utf-8">`, the
`Page.title`, `<div id="gramlot-root">` and one `<script type="module"
nonce="…">` that imports `PageBootstrap` from the runtime URL and runs it with
`{"config": {"pageId", "mainUrl", "sourceUrl", "closeUrl", "rootId"},
"resources": {"css": [url…], "js": [{"url", "group"}…]}}`; the URLs carry the
mount prefix. The companion `_aux.js` has `"group": null`.
