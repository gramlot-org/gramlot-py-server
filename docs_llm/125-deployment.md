# 125 · Deployment

Document ID: **GS-125**.

[Paired view](../docs/125-deployment.md).

<a id="gs-125-005"></a>

## 005 · Behind a reverse proxy with a mount prefix

Block ID: **GS-125-005**.

Route `/py/` to the adapter and strip the prefix before dispatch; give the
adapter the same prefix as `mount_path`:

```python
application = create_asgi_application("pages", mount_path="/py",
                                      content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'")
```

The browser then requests `/py/hello`, `/py/assets/gramlot.js`,
`/py/hello_aux.js` and `/py/gramlot/main`; the adapter sees them without `/py`.
The owner cookie is scoped to `Path=/py`. A front that does not strip the prefix
is not supported: the adapter would look for a page `py/hello`.

Uvicorn behind a proxy: `uvicorn app:application --host 127.0.0.1 --port 8000
--proxy-headers`. The adapter reads no client address and no forwarded header;
TLS ends at the proxy.

<a id="gs-125-010"></a>

## 010 · Static assets

Block ID: **GS-125-010**.

The adapter serves the runtime at `/assets/gramlot.js` and the companions of
the pages folder. Everything else, themes, images, fonts, is an asset of the
application: serve it from the proxy or from another ASGI route and reference
it from `Page.css` with a root-relative URL (it receives the mount prefix) or
an absolute URL. The adapter sends `Cache-Control: no-store` on every response,
including the runtime; a cache in front of it has to decide on its own.

<a id="gs-125-015"></a>

## 015 · Security notes

Block ID: **GS-125-015**.

- The pages folder is trusted application source. A page module is executed
  again at every opening; never point `pages` at a folder that receives uploads.
- Of the pages folder only `.css` and `_aux.js` files below it are served, with
  `GET` and `HEAD`. Page modules, READMEs and other files are never served, and
  a path that resolves outside the folder answers 404.
- The companion runs in the browser and is public. Server-only logic, queries,
  keys and data access belong in modules the companion does not import.
- Send the strict Content Security Policy profile unless a page needs inline
  code; the permissive profile allows `'unsafe-eval'`.
- The owner cookie identifies a browser, not a user. Put authentication in
  front of the adapter.
- A page expires after `page_ttl` seconds and the process keeps at most
  `max_pages` open pages; a browser that keeps a page past its expiry gets 404
  on the next request and must reload.

<a id="gs-125-020"></a>

## 020 · Production checklist

Block ID: **GS-125-020**.

- `gramlot>=0.2.0` installed from PyPI; `pip show gramlot` reports one version.
- `mount_path` equal to the prefix the proxy strips.
- `content_security_policy` set, strict where possible.
- `page_ttl` and `max_pages` sized for the expected number of open pages.
- One worker process, or a proxy that keeps a browser on the same worker: the
  page registry is process-local, so a request routed to another worker answers
  404 "Unknown page".
- Authentication and TLS at the proxy.
- The pages folder read-only for the server process.
