# 010 · Writing pages for these hosts

Document ID: **GP-010**.

Derived from a guide of the archived gramlot-uvicorn repository.

[Paired view](../docs/010-writing-pages.md).

The binding itself, pointers, formulas, controllers, buttons and events, is the
core guide
[Data binding and controllers](https://gramlot.readthedocs.io/en/latest/docs/public/097-data-binding.html);
the structure of a page is [Writing pages](https://gramlot.readthedocs.io/en/latest/docs/public/095-writing-pages.html).
This guide covers what depends on the server. It is valid for every adapter of
this package: all five serve the pages folder through the core `GramlotFileServer`
and answer the HTTP rules of the
[server protocol](https://gramlot.readthedocs.io/en/latest/docs/public/101-server-protocol.html).

<a id="gp-010-005"></a>

## 005 · Files and folders

Block ID: **GP-010-005**.

For the URL path `orders` the `GramlotFileServer` takes the file page `orders.py` first,
then the folder page `orders/orders.py`. When both exist the file wins. For
`shop/orders` it takes `shop/orders.py`, then `shop/orders/orders.py`. The URL
of the mount root, `/` or `/py/`, opens the page `index`.

- Path segments contain letters, digits, `_` and `-`. Any other character, and
  a path whose real location leaves the folder, answers 404.
- The module must define a class `Page` that extends `gramlot.Page`; the base
  `gramlot.Page` itself is refused. The module runs once per process, or again
  at every opening with `GRAMLOT_DEV` set ([Configuration](110-configuration.md)).
- The `_aux` suffix is reserved: `orders_aux.js` is never a page, and no page is
  called `*_aux`.
- The pages folder is trusted application source, not uploaded content.
- `main` may be synchronous or asynchronous. It builds into `root` and
  returns `None`.

<a id="gp-010-010"></a>

## 010 · Companions

Block ID: **GP-010-010**.

Beside the page file, with the page's name:

| File | Role | Served at |
| --- | --- | --- |
| `orders.css` | the page stylesheet | `/orders.css` |
| `orders.js` | the page module, exporting `class Logic` when the page has named logic | `/orders.js` |
| `orders_aux.js` | the page's JavaScript module, exporting `class Logic` | `/orders_aux.js` |
| `orders.md` | the README of the page | not served |

The URLs carry the mount prefix, for example `/py/orders.css`. Every companion
is optional. The logic of `orders.py` is the `Logic` export of `orders.js`,
else of `orders_aux.js`; with both files the opening of the page raises
`ValueError`. A page without `Logic` has no logic methods: write the class only
when the page names a method with `func=`. `orders.js` may also export a `Page`,
the JavaScript version of the same page, which the Python server leaves unused.
The module imports the runtime as `@gramlot/gramlot/page`: the import map of the
bootstrap resolves it. The bootstrap loads the theme of the page first, then the
`Page.css` URLs, then `orders.css`, then imports the logic module. A folder page
keeps its companions in its folder, beside `orders/orders.py`.

The companion rule: `GET` and `HEAD` answer a `.css` or `.js` file whose real
path is below the pages folder, so a page module and its relative imports reach
the browser. Any other file answers 404. Another method answers 405 with
`Allow: GET, HEAD`. The `.js` files of the folder run in the browser, so they
are public. Server-only logic belongs in Python modules that the page imports,
never in a `.js` file of the pages folder.

<a id="gp-010-015"></a>

## 015 · Page.css

Block ID: **GP-010-015**.

`Page.css` is a tuple of stylesheet URLs, written as in `<link href>`. The
server loads the theme of the page before them: the base theme `gramlot-base`,
which every page has without a line in `Page.css`. `Page.css` lists what follows
the theme, such as an overlay of the core and the stylesheets of the application:

```python
class Page(BasePage):
    css = ("/themes/gramlot-compact/theme.css", "orders-print.css")
```

A page replaces the base theme with `css_theme = "<name>"` and loads none with
`css_theme = False`. The adapters of this package do not expose the option
`css_theme` of `GramlotServer`, the base theme of the server: it stays
`gramlot-base` for every page, and `Page.css_theme` is the only way to change it.

A root-relative URL (`/themes/gramlot-compact/theme.css`) receives the mount
prefix once: the adapter serves it from the themes of the core. A relative URL
(`orders-print.css`) and an absolute URL stay as written. A `Page.css`
URL that points inside the pages folder is served by the companion rule when it
ends in `.css`. A URL outside the folder is an asset of the application, which
serves it itself or through its web server. See
[Themes and CSS](https://gramlot.readthedocs.io/en/latest/docs/public/096-themes-and-css.html).

`css_requires` and `js_requires` name resources of a `GramlotServer` with a
resource system. `GramlotFileServer` and the adapters of this package have
none: a name in either field raises `InvalidResourceName` ("requires need a
GramlotServer with a resource system") when the page is opened. The resource system comes with genro-kajenn,
part of Genro, the framework that succeeds GenroPy.

<a id="gp-010-020"></a>

## 020 · Named logic

Block ID: **GP-010-020**.

The methods of `class Logic` in the companion are the named logic of the page.
`Logic` is optional: a page without named logic needs no class. A misspelt
export (`logic`) is not an error when the module loads; the error appears when
a `func=` looks for its method.
`func="greet"` on a `dataFormula` calls `greet(kwargs)` and uses the returned
value. `func="countChange"` on a `dataController` calls
`countChange(node, kwargs)`. `kwargs` holds the resolved parameters of the
declaration plus `_node`, `_triggerpars` and `_reason`.

Named logic runs under both Content Security Policy profiles. Inline code (a
`formula` string, `script`, `==` expressions, button `action`,
`connect_on<event>`, `_if`/`_else`) runs only under the permissive profile; see
[Configuration](110-configuration.md).

<a id="gp-010-025"></a>

## 025 · Remote Source

Block ID: **GP-010-025**.

Declare Source fragments with `@source` and mount them with `remote`;
use `dataRpc` for endpoint values and `dataRemote` for lazy Data. See
[Calling the server](https://github.com/gramlot-org/gramlot/blob/main/docs/public/098-server-calls.md#gc-095-100)
and [Remote content and lazy Data](https://github.com/gramlot-org/gramlot/blob/main/docs/public/099-remote-content.md#gc-095-105).

Endpoints (`@endpoint`, called from the Source by `dataRpc`) are described in
[Calling the server](https://gramlot.readthedocs.io/en/latest/docs/public/098-server-calls.html)
of the core, and fragments and lazy Data in
[Remote content and lazy Data](https://gramlot.readthedocs.io/en/latest/docs/public/099-remote-content.html).
The adapters answer every call, a fragment
(`contentType` `source`) or an endpoint (`contentType` `data`), at
`POST /gramlot/rpc`; see section 030, What is served. Only the Kajenn adapter announces
the `auth` capability and evaluates an `auth` rule against the tags of the Kajenn
avatar ([Kajenn](505-kajenn.md)). In the other adapters an endpoint with an `auth`
rule answers `not_authenticated`.

<a id="gp-010-030"></a>

## 030 · What is served

Block ID: **GP-010-030**.

Paths are shown without the mount prefix.

| Request | Answer |
| --- | --- |
| `GET /<page path>` | the bootstrap document of the page |
| `GET /<page path>/index.html`, `GET /index.html` | the bootstrap document of the page `<page path>`, of the page `index` |
| `GET`, `HEAD /assets/gramlot.js` | the Gramlot browser runtime packaged with the core |
| `GET`, `HEAD /themes/<file>` | a file of the themes packaged with the core, such as `/themes/gramlot-base/theme.css` |
| `GET`, `HEAD` of a URL of the `assets` option | the file, with its media type |
| `GET`, `HEAD` of a `.css` or `.js` file below the pages folder | the file |
| `GET`, `HEAD /app.webmanifest` | the web manifest of an installable root page ([Configuration](110-configuration.md)); 404 otherwise |
| `POST /gramlot/rpc`, `/gramlot/close` | the page protocol: the envelopes of `GramlotServer.call`, the close of a page |

Nothing else of the pages folder leaves the server: no `.py`, no `.md`, no
other asset. Other static assets of the application live outside the pages
folder; the `assets` option serves a list of them below the prefix, or the
application and its web server serve them. The five adapters answer the same
status codes and headers (the 405 with `Allow` of any other method included);
each guide lists the answers, and the
[server protocol](https://gramlot.readthedocs.io/en/latest/docs/public/101-server-protocol.html)
of the core states the rules.


<a id="gp-010-035"></a>

## 035 · Initial Data companion

Block ID: **GP-010-035**.

The optional `foo_data.tytx` beside the page supplies a typed initial Data Bag before browser defaults and rendering. No loader declaration is needed in main. Existing dataSetter, default and remote data mechanisms remain available. Invalid files fail loading; missing files leave behavior unchanged. Client edits do not write back to the file. The gallery copies the Data companion beside its staged Python wrapper.
