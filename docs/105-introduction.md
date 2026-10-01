# 105 · Introduction

Document ID: **GS-105**.

[Paired view](../docs_llm/105-introduction.md).

<a id="gs-105-005"></a>

## 005 · What this adapter does

Block ID: **GS-105-005**.

Gramlot describes a web interface in Python or JavaScript and keeps it bound to
the application state in the browser. The core guide
[The Gramlot family](https://gramlot.readthedocs.io/en/latest/docs/public/055-family.html)
explains Page, Source, Data, logic and Host, and lists the repositories.

`gramlot-uvicorn` is the Host adapter for Python pages served from a Python web
server. It is an ASGI application. It takes a folder of Python `Page` modules,
opens a page when a browser asks for it, serves the Gramlot browser runtime and
the page companions, answers the Source requests of the running page and closes
the page when the browser leaves. Uvicorn runs it; any ASGI server does.

The adapter does not render HTML from the Source and does not run page logic:
the browser runtime does both. It does not serve JavaScript pages
(`gramlot-js-server` does) and it does not export a page that opens without a
server (`gramlot-serverless` does).

<a id="gs-105-010"></a>

## 010 · A request on this host

Block ID: **GS-105-010**.

For a page `hello.py` in the pages folder, served at the root:

1. **Page URL.** The browser requests `GET /hello`. The adapter asks the core
   `FileHost` for the page: `hello.py`, or `hello/hello.py`. It registers a new
   page ID for this browser and answers the bootstrap document: a small HTML
   page with the title, an empty root `div` and one module script that carries a
   nonce. The response sets the cookie `gramlot_owner`, which identifies this
   browser as the owner of the page.
2. **Bootstrap.** The module script imports the runtime from `/assets/gramlot.js`
   and runs `PageBootstrap` with the page ID, the URLs of the main, source and
   close endpoints, and the resources of the page: the `Page.css` URLs, the
   companion stylesheet `hello.css` and the companion module `hello_aux.js` when
   they exist beside the page file.
3. **Main.** The runtime posts `{"pageId": …}` to `/gramlot/main`. The adapter
   runs `Page.main(root)` on the server and answers the Source tree as TYTX. The
   runtime renders the DOM from it and installs the data binding.
4. **Source.** A page method marked with `@source` answers `POST /gramlot/source`
   with `{"pageId", "method", "params"}`; the runtime mounts the returned branch
   where the page asked for it.
5. **Close.** When the browser disposes the page, or leaves it without keeping it
   in the back/forward cache, the runtime posts `{"pageId": …}` to
   `/gramlot/close` and the adapter forgets the page. A page that is never closed
   expires after `page_ttl` seconds (default 1800).

Companion files are served with `GET` and `HEAD` only, and only `.css` and
`_aux.js` files whose real path is below the pages folder. Every other file of
the folder, including the `.py` pages, answers 404.
