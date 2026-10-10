# 015 · Troubleshooting

Document ID: **GP-015**.

Derived from a guide of the archived gramlot-uvicorn repository.

[Paired view](../docs_llm/015-troubleshooting.md).

The messages below are the same in every adapter. The body that carries them
differs: plain text for Uvicorn, Django, Flask and FastAPI, a JSON object
`{"error": "…"}` for Kajenn.

<a id="gp-015-005"></a>

## 005 · The page does not start

Block ID: **GP-015-005**.

**The browser shows an empty page and the console reports an `EvalError`
"inline code blocked by the Content Security Policy of the page".** The page
uses inline code (a `formula` string, `script`, `==`, button `action`,
`connect_on<event>`, `_if`/`_else`) and the adapter sends the strict profile.
The message names the node and the attribute, for example
`dataFormula 'dataFormula_0' 'formula'`. Move the code to a method of
`class Logic` in the page module `<page>.js` and name it with `func=`, or send
the permissive profile (`'unsafe-eval'` in `script-src`).

**404 on `/<page>.js`, `/<page>_aux.js` or `/<page>.css`.** The file is not
beside the page file with the page's name, or its real path leaves the pages
folder (a symbolic link to another folder). For a folder page
`orders/orders.py` the companions live in `orders/`. Check the names:
`orders_aux.js`, not `orders.aux.js` or `orders-aux.js`.

**The console reports "the module exports no class Logic".** `orders.js`
beside `orders.py` is the logic module of the page and must export
`class Logic`, even an empty one.

**500 on `GET /<page>`.** The page module raised while it was imported, has no
class `Page` extending `gramlot.Page`, or declares `css_requires` or
`js_requires` (`GramlotFileServer` and these adapters have no resource system and
raise `InvalidResourceName`). The server log holds the traceback.

**404 `Page not found`.** One of these:

- no `<path>.py` and no `<path>/<name>.py` below the pages folder;
- a segment with a character outside letters, digits, `_` and `-`;
- a path ending in `_aux`;
- a request path outside the mount prefix, for example a proxy that removes
  the prefix before it passes the request on. The path must reach the adapter
  with the prefix; with Django the URLconf holds `Pages.urlpatterns`.

**404 on `/favicon.ico`.** The browser asks for an icon. The adapters serve
none. Serve it from the application or the proxy, or ignore it.

<a id="gp-015-010"></a>

## 010 · The page stops working

Block ID: **GP-015-010**.

**The outcome `page_expired` from `/gramlot/rpc`.** The response is 200 with
`"error": {"code": "page_expired", …}`. One of these:

- the page ID is expired (`page_ttl`, default 30 minutes);
- the server restarted;
- the request reached another worker process;
- the cookie `gramlot_owner` is missing or differs from the one of the opening:
  another browser, a cleared cookie, or a cookie `Path` that does not cover the
  request because the mount prefix given to the adapter differs from the one
  the browser uses.

Reload the page. For the worker case keep one worker, or make the proxy keep a
browser on the same one.

**The outcome `not_found`.** The envelope names a fragment or an endpoint that
the page does not declare for its `contentType`: `data` with the name `main`
included. Source methods (`@source`, `remoteSource`) are not yet part of the page-writing API: they arrive together with the `remote` grammar attribute.

**The outcome `application_error`.** The method of the page raised: `name` and
`message` are those of the exception. With `GRAMLOT_DEV=DEBUG` the error also
carries `details`, the traceback.

**The outcome `not_authenticated`.** The endpoint has an `auth` rule. No adapter
of this package knows an identity, so every rule is closed.

**503 `Page capacity reached`.** `max_pages` pages are open and not expired.
Raise `max_pages`, lower `page_ttl`, or make sure pages are closed.

<a id="gp-015-015"></a>

## 015 · Requests refused

Block ID: **GP-015-015**.

- 415 `Expected application/json`: a protocol request without
  `Content-Type: application/json`. Parameters such as `charset` are accepted.
- 400 `Request body is not UTF-8`: the body bytes are not UTF-8 text.
- 400 `Invalid envelope`: `call` refused the body of `/gramlot/rpc`. The body is
  not TYTX JSON text of an object; `id`, `pageId`, `contentType` or `name` is
  not a string; `contentType` is neither `source` nor `data`; or `params` is
  not an object.
- 400 `Invalid JSON request`: the body of `/gramlot/close` is not a JSON
  object with a string `pageId`.
- 413 from a web server in front: the adapters fix no body size, a proxy may.
- A method that a path does not accept is refused. The status differs by
  framework: see the endpoint table of each guide.
- 500 on every protocol request with Kajenn: the application is declared
  without `request(body="raw")`; see [Kajenn](505-kajenn.md).

<a id="gp-015-020"></a>

## 020 · Installation

Block ID: **GP-015-020**.

**`ImportError` when a module is imported.** The extra of the framework is not
installed: `pip install "gramlot-py-server[django]"` for
`gramlot_py_server.django`, and the same for `flask`, `fastapi` and `kajenn`. The
command `gramlot` reports the same case as
`gramlot django: asgiref is not installed. Install the extra: …`, and a gallery
without `gramlot-examples` as `The gallery needs gramlot-examples: …`; the
other messages of the command are in [The gramlot command](020-command.md).

**Two cores.** The package declares `gramlot>=0.2.14`. `pip show gramlot`
reports the version and the location of the core that Python imports. When a
copy from PyPI and a copy installed in editable mode from a checkout are both
present, the report names the one that wins. Uninstall the other, or keep one
virtual environment per core.
