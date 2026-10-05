# 010 · Writing pages for these hosts

Document ID: **GP-010**.

Derived from a guide of the archived gramlot-uvicorn repository.

[Paired view](../docs/010-writing-pages.md).

The binding itself, pointers, formulas, controllers, buttons and events, is the
core guide
[Writing pages](https://gramlot.readthedocs.io/en/latest/docs/public/095-writing-pages.html).
This guide covers what depends on the host. It is valid for every adapter of
this package: all five serve the pages folder through the core `FileHost`.

<a id="gp-010-005"></a>

## 005 · Files and folders

Block ID: **GP-010-005**.

For the URL path `orders` the `FileHost` takes the file page `orders.py` first,
then the folder page `orders/orders.py`. When both exist the file wins. For
`shop/orders` it takes `shop/orders.py`, then `shop/orders/orders.py`. The URL
of the mount root, `/` or `/py/`, opens the page `index`.

- Path segments contain letters, digits, `_` and `-`. Any other character, and
  a path whose real location leaves the folder, answers 404.
- The module must define a class `Page` that extends `gramlot.Page`. The module
  is executed again at every opening of the page.
- The `_aux` suffix is reserved: `orders_aux.js` is never a page, and no page is
  called `*_aux`.
- The pages folder is trusted application source, not uploaded content.

<a id="gp-010-010"></a>

## 010 · Companions

Block ID: **GP-010-010**.

Beside the page file, with the page's name:

| File | Role | Served at |
| --- | --- | --- |
| `orders.css` | the page stylesheet | `/orders.css` |
| `orders.js` | the page module, exporting `class Logic` | `/orders.js` |
| `orders_aux.js` | the page's JavaScript module, exporting `class Logic` | `/orders_aux.js` |
| `orders.md` | the README of the page | not served |

The URLs carry the mount prefix, for example `/py/orders.css`. Every companion
is optional. The logic of `orders.py` is the `Logic` export of `orders.js`,
else of `orders_aux.js`; with both files the opening of the page raises
`ValueError`. `orders.js` may also export a `Page`, the JavaScript version of
the same page, which the Python host leaves unused. The module imports the
runtime as `@gramlot/gramlot/page`: the import map of the bootstrap resolves
it. The bootstrap loads the `Page.css` URLs first, then `orders.css`, then
imports the logic module. A folder page keeps its companions in its folder,
beside `orders/orders.py`.

The companion rule: `GET` and `HEAD` answer a `.css` or `.js` file whose real
path is below the pages folder, so a page module and its relative imports reach
the browser. Any other file answers 404. Another method is refused; the status
depends on the adapter and is in its guide. The `.js` files of the folder run
in the browser, so they are public. Server-only logic belongs in Python modules
that the page imports, never in a `.js` file of the pages folder.

<a id="gp-010-015"></a>

## 015 · Page.css

Block ID: **GP-010-015**.

`Page.css` is a tuple of stylesheet URLs, written as in `<link href>`:

```python
class Page(BasePage):
    css = ("/themes/gramlot-base/theme.css", "orders-print.css")
```

A root-relative URL (`/themes/gramlot-base/theme.css`) receives the mount prefix
once: the adapter serves it from the themes of the core. A relative URL
(`orders-print.css`) and an absolute URL stay as written. A `Page.css`
URL that points inside the pages folder is served by the companion rule when it
ends in `.css`. A URL outside the folder is an asset of the application, which
serves it itself or through its web server.

`css_requires` and `js_requires` name resources of a Host with a resource
system. `FileHost` and the adapters of this package have none: a name in either
field raises `InvalidResourceName` ("requires need a Host with a resource
system") when the page is opened. The resource system comes with genro-kajenn,
part of Genro, the framework that succeeds GenroPy.

<a id="gp-010-020"></a>

## 020 · Named logic

Block ID: **GP-010-020**.

The methods of `class Logic` in the companion are the named logic of the page.
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

A method decorated with `@source` builds a Source branch on request:

```python
from gramlot import Page as BasePage, source


class Page(BasePage):
    def main(self, root):
        root.div(id="details")

    @source
    def details(self, root, name="Ada"):
        root.p(name)
```

The browser asks for it with
`page.remoteSource(targetNode, "details", {name: "Grace"})` from named logic,
for example from a button controller. The adapter answers
`POST /gramlot/source` with
`{"pageId", "method": "details", "params": {"name": "Grace"}}`. The parameters
arrive as keyword arguments. `main` and Source methods may be synchronous or
asynchronous. They build into `root` and return `None`. A method that is not
decorated answers 404 "Unknown Source method". Gramlot has no declarative
remote Source request.

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
| `POST /gramlot/main`, `/gramlot/source`, `/gramlot/close` | the page protocol |

Nothing else of the pages folder leaves the server: no `.py`, no `.md`, no
other asset. Other static assets of the application live outside the pages
folder; the `assets` option serves a list of them below the prefix, or the
application and its web server serve them. The answers to other
methods and paths differ between frameworks; each guide lists them.
