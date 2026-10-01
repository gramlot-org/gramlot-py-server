# 140 · Troubleshooting

Document ID: **GS-140**.

[Paired view](../docs_llm/140-troubleshooting.md).

<a id="gs-140-005"></a>

## 005 · The page does not start

Block ID: **GS-140-005**.

**The browser shows an empty page and the console reports an `EvalError`
"inline code blocked by the Content Security Policy of the page".** The page
uses inline code (a `formula` string, `script`, `==`, button `action`,
`connect_on<event>`, `_if`/`_else`) and the adapter sends the strict profile.
The message names the node and the attribute, for example `dataFormula
'dataFormula_0' 'formula'`. Move the code to a method of `class Logic` in the
page companion `_aux.js` and name it with `func=`, or send the permissive
profile (`'unsafe-eval'` in `script-src`).

**404 on `/<page>_aux.js` or `/<page>.css`.** The file is not beside the page
file with the page's name, or its real path leaves the pages folder (a symbolic
link to another folder). For a folder page `orders/orders.py` the companions
live in `orders/`. Check the names: `orders_aux.js`, not `orders.aux.js` or
`orders-aux.js`.

**500 on `GET /<page>`.** The page module raised while it was imported, has no
class `Page` extending `gramlot.Page`, or declares `css_requires` or
`js_requires` (this host has no resource system and raises
`InvalidResourceName`). The server log holds the traceback.

**404 `Page not found`.** No `<path>.py` and no `<path>/<name>.py` below the
pages folder, a segment with a character outside letters, digits, `_` and `-`,
a path ending in `_aux`, or a prefix that the front did not strip (the adapter
looks for `py/hello` when it receives `/py/hello`).

**404 on `/favicon.ico` in the server log.** The browser asks for an icon; the
adapter serves none. Serve it from the proxy or ignore it.

<a id="gs-140-010"></a>

## 010 · The page stops working

Block ID: **GS-140-010**.

**404 `Unknown page` on `/gramlot/main` or `/gramlot/source`.** The page ID is
expired (`page_ttl`, default 30 minutes), the server restarted, the request
reached another worker process, or the cookie `gramlot_owner` is missing or
differs from the one of the opening (another browser, a cleared cookie, a cookie
`Path` that does not cover the request because `mount_path` differs from the
prefix the front strips). Reload the page; for the worker case keep one worker
or make the proxy keep a browser on the same one.

**404 `Unknown Source method`.** The method is not decorated with `@source`,
is named `main`, or an override without the decorator hides it.

**500 on `/gramlot/source`.** The Source method raised; the server log holds
the traceback.

**503 `Page capacity reached`.** `max_pages` pages are open and not expired.
Raise `max_pages`, lower `page_ttl`, or make sure pages are closed.

<a id="gs-140-015"></a>

## 015 · Requests refused

Block ID: **GS-140-015**.

- 415 `Expected application/json`: a protocol request without
  `Content-Type: application/json`.
- 413 `Request too large`: a body above 4096 bytes.
- 400 `Invalid JSON request`: the body is not a JSON object with a string
  `pageId`; 400 `Source params must be a dictionary`: `params` is not an object.
- 405: `HEAD` or `POST` on a page URL (only `GET`), `POST` on a companion (only
  `GET` and `HEAD`), `GET` on `/gramlot/*` (only `POST`).

<a id="gs-140-020"></a>

## 020 · Installation

Block ID: **GS-140-020**.

The adapter declares `gramlot>=0.2.0`. `pip show gramlot` reports the version
and the location of the core that Python imports. When a copy from PyPI and a
copy installed in editable mode from a checkout are both present, the report
names the one that wins; uninstall the other, or keep one virtual environment
per core.
