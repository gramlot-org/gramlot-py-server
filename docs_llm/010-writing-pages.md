# 010 · Writing pages for these hosts

Document ID: **GP-010**.

Derived from GS-115 (gramlot-uvicorn).

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
| `orders_aux.js` | the page's JavaScript module, exporting `class Logic` | `/orders_aux.js` |
| `orders.md` | the README of the page | not served |

The URLs carry the mount prefix, for example `/py/orders.css`. Both companions
are optional. The bootstrap loads the `Page.css` URLs first, then `orders.css`,
then imports `orders_aux.js`. A folder page keeps its companions in its folder,
beside `orders/orders.py`.

The companion rule: `GET` and `HEAD` answer a `.css` or `_aux.js` file whose
real path is below the pages folder. Any other file answers 404. Another method
is refused; the status depends on the adapter and is in its guide. The
companion runs in the browser, so it is public. Server-only logic belongs in
Python modules that the page imports, never in the companion.

<a id="gp-010-015"></a>

## 015 · Page.css

Block ID: **GP-010-015**.

`Page.css` is a tuple of stylesheet URLs, written as in `<link href>`:

```python
class Page(BasePage):
    css = ("/themes/base.css", "theme.css")
```

A root-relative URL (`/themes/base.css`) receives the mount prefix once. A
relative URL (`theme.css`) and an absolute URL stay as written. A `Page.css`
URL that points inside the pages folder is served by the companion rule when it
ends in `.css`. A URL outside the folder is an asset of the application, which
serves it itself or through its web server.

`css_requires` and `js_requires` name resources of a Host with a resource
system. `FileHost` has none: a name in either field raises
`InvalidResourceName` ("requires need a Host with a resource system") when the
page is opened.

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
decorated answers 404 "Unknown Source method". Gramlot 0.2.1 has no declarative
remote Source request.

<a id="gp-010-030"></a>

## 030 · What is served

Block ID: **GP-010-030**.

Paths are shown without the mount prefix.

| Request | Answer |
| --- | --- |
| `GET /<page path>` | the bootstrap document of the page |
| `GET`, `HEAD /assets/gramlot.js` | the Gramlot browser runtime packaged with the core |
| `GET`, `HEAD` of a `.css` or `_aux.js` file below the pages folder | the file |
| `POST /gramlot/main`, `/gramlot/source`, `/gramlot/close` | the page protocol |

Nothing else of the pages folder leaves the server: no `.py`, no `.md`, no
other asset. Static assets of the application live outside the pages folder
and are served by the application or its web server. The answers to other
methods and paths differ between frameworks; each guide lists them.
