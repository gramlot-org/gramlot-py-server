# 115 · Uvicorn deployment

Document ID: **GP-115**.

Derived from a guide of the archived gramlot-uvicorn repository.

[Paired view](../docs_llm/115-deployment.md).

<a id="gp-115-005"></a>

## 005 · Behind a reverse proxy with a mount prefix

Block ID: **GP-115-005**.

Route `/py/` to the application with the path unchanged. Give the application
the same prefix as `mount_path`:

```python
from gramlot_py_server.uvicorn import create_application

application = create_application(
    "pages",
    mount_path="/py",
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)
```

With nginx, `proxy_pass` without a URI passes the path unchanged:

```nginx
location /py/ {
    proxy_pass http://127.0.0.1:8000;
}
```

`proxy_pass http://127.0.0.1:8000/;`, with a URI, removes `/py/` and is not
supported: every request answers 404.

The browser then requests `/py/hello`, `/py/assets/gramlot.js`, `/py/hello.js`
and `/py/gramlot/rpc`. The application receives them with `/py` and removes
it. `/py` without the final slash answers 301 to `/py/`; with the `location
/py/` above, nginx itself answers 301 to `/py/` before the request reaches the
application. The owner cookie is scoped to `Path=/py`.

Uvicorn behind a proxy:
`uvicorn app:application --host 127.0.0.1 --port 8000 --proxy-headers`. The
adapter reads no client address and no forwarded header. TLS ends at the proxy.

<a id="gp-115-010"></a>

## 010 · Static assets

Block ID: **GP-115-010**.

The application serves the runtime at `/assets/gramlot.js`, the themes of the
core at `/themes/…`, the companions of the pages folder and the files of its
`assets` option ([Configuration](110-configuration.md)). Images, fonts and
the application's own stylesheets outside the pages folder are assets of the
application: add them to `assets`, or serve them from the proxy or from another
ASGI route. Reference a stylesheet from `Page.css` with a root-relative URL (it
receives the mount prefix) or an absolute URL. The application sends `Cache-Control: no-store` on every
response, including the runtime. A cache in front of it has to decide on its
own.

<a id="gp-115-015"></a>

## 015 · Security notes

Block ID: **GP-115-015**.

These notes hold for every adapter of the package.

- The pages folder is trusted application source. A page module runs once per process, or
  again at every opening with `GRAMLOT_DEV` set. Never point `pages` at a folder that receives
  uploads.
- Of the pages folder only `.css` and `.js` files below it are served, with
  `GET` and `HEAD`. Python pages, READMEs and other files are never served. A
  path that resolves outside the folder answers 404.
- The `.js` files of the pages folder run in the browser and are public.
  Server-only logic, queries, keys and data access belong in Python modules,
  never in a `.js` file of the pages folder.
- `assets` serves exactly the files of its map: build it from trusted paths.
- Send the strict Content Security Policy profile unless a page needs inline
  code. The permissive profile allows `'unsafe-eval'`.
- The owner cookie identifies a browser, not a user. Put authentication in
  front of the adapter.
- A page expires after `page_ttl` seconds and the process keeps at most
  `max_pages` open pages. A browser that keeps a page past its expiry gets 404
  on the next request and must reload.

<a id="gp-115-020"></a>

## 020 · Production checklist

Block ID: **GP-115-020**.

- `gramlot-py-server[uvicorn]` installed with `gramlot>=0.2.14`;
  `pip show gramlot` reports one version.
- `mount_path` equal to the prefix the proxy routes, and the proxy passes the
  path unchanged (`proxy_pass` without a URI).
- `content_security_policy` set, strict where possible.
- `GRAMLOT_DEV` unset: minified runtime, page files run once per process.
- `page_ttl` and `max_pages` sized for the expected number of open pages.
- One worker process, or a proxy that keeps a browser on the same worker: the
  page registry is process-local, so a call routed to another worker
  answers the outcome `page_expired`.
- Authentication and TLS at the proxy.
- The pages folder read-only for the server process.
