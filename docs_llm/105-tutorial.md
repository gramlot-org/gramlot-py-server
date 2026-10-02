# 105 · Uvicorn tutorial

Document ID: **GP-105**.

Derived from GS-110 (gramlot-uvicorn).

[Paired view](../docs/105-tutorial.md).

This tutorial uses the files of `examples/pages` and `examples/uvicorn/app.py`
of the repository. The test `tests/uvicorn/test_uvicorn_examples.py` serves
them with `gramlot` 0.2.1: it checks the bootstrap documents, the companions,
the Content Security Policy header and the Source of `main`. It does not run a
browser.

<a id="gp-105-005"></a>

## 005 · Install

Block ID: **GP-105-005**.

Python 3.11 or later:

```sh
python -m venv .venv
.venv/bin/pip install "gramlot-py-server[uvicorn]"
```

The extra `uvicorn` installs Uvicorn. The example files are in the repository,
not in the package. From a checkout of the repository the same install is
`.venv/bin/pip install ".[uvicorn]"`.

<a id="gp-105-010"></a>

## 010 · Folder layout

Block ID: **GP-105-010**.

```text
examples/
  pages/
    hello.py           a page with an inline formula
    greeting.py        a page with named logic
    greeting_aux.js    its companion: the named logic
    greeting.css       its stylesheet
  uvicorn/
    app.py             the ASGI application
```

The page, the companion and the stylesheet share the name `greeting`. The core
`FileHost` finds the two companions beside the page file and adds them to the
bootstrap document.

<a id="gp-105-015"></a>

## 015 · The page

Block ID: **GP-105-015**.

`examples/pages/greeting.py`:

```python
from gramlot import Page as BasePage


class Page(BasePage):
    title = "Greeting"

    def main(self, root):
        pane = root.div(datapath="person", class_="greeting")
        pane.html_label("Name", for_="name")
        pane.input(id="name", value="^.name", live=True)
        pane.p("^.greeting", id="greeting")
        pane.dataFormula(".greeting", func="greet", name="^.name", _init=True)
        pane.dataSetter(".name", "Ada")
```

- `datapath="person"` makes the relative paths of the children start at
  `person` in the Data.
- `value="^.name"` binds the field to `person.name`. `live=True` writes every
  keystroke back into the Data.
- `"^.greeting"` as the text of the paragraph follows `person.greeting`.
- `dataFormula` computes `person.greeting` with the named method `greet` of the
  companion, with `name` bound to `person.name`. `_init=True` computes it once
  at start.
- `dataSetter` gives `person.name` its initial value.

`examples/pages/hello.py` declares the same field and paragraph. Its formula is
the inline expression `"'Hello, ' + name"` instead of a named method.

<a id="gp-105-020"></a>

## 020 · The companion

Block ID: **GP-105-020**.

`examples/pages/greeting_aux.js`:

```javascript
export class Logic {
    greet(kwargs) {
        return `Hello, ${kwargs.name}`;
    }
}
```

The module exports one class `Logic`. A formula method receives the resolved
parameters and returns the value. `func="greet"` in the page names it. The
companion runs in the browser. It is public.

<a id="gp-105-025"></a>

## 025 · The stylesheet

Block ID: **GP-105-025**.

`examples/pages/greeting.css`:

```css
.greeting { font-family: sans-serif; padding: 1rem; }
.greeting p { color: #2a6; }
```

The bootstrap writes a `<link>` to `/greeting.css` before it imports the
companion.

<a id="gp-105-030"></a>

## 030 · Run it

Block ID: **GP-105-030**.

`examples/uvicorn/app.py`:

```python
"""Serve the example pages with Uvicorn: ``uvicorn app:application``."""
from pathlib import Path

from gramlot_py_server.uvicorn import create_application

PAGES = Path(__file__).resolve().parents[1] / "pages"

application = create_application(
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'",
)
```

The application sends the permissive profile because `hello.py` uses inline
code. `greeting.py` uses named logic only, so the strict profile is enough for
it: replace the policy with
`"script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"`. The second
test of `tests/uvicorn/test_uvicorn_examples.py` serves `greeting` under the
strict profile.

From the folder `examples/uvicorn`:

```sh
../../.venv/bin/uvicorn app:application
```

Open <http://127.0.0.1:8000/greeting> or <http://127.0.0.1:8000/hello>. One
opening of `/greeting` makes these requests:

| Request | Made by |
| --- | --- |
| `GET /greeting` | the browser: the bootstrap document |
| `GET /assets/gramlot.js` | the bootstrap script: the runtime |
| `GET /greeting.css` | `PageBootstrap`: the stylesheet |
| `GET /greeting_aux.js` | `PageBootstrap`: the companion module |
| `POST /gramlot/main` | `PageBootstrap`: the Source of `main` |

The browser also asks for `/favicon.ico`. The adapter serves no icon and
answers 404 `Page not found`.

<a id="gp-105-035"></a>

## 035 · What changes when you type

Block ID: **GP-105-035**.

The page declares this behaviour. It shows a field with `Ada` and the green
text `Hello, Ada`. Typing `Grace` in the field changes the text to
`Hello, Grace` at every keystroke: the field writes `person.name`, the formula
sees its `name` parameter change and calls `greet` again, and the paragraph
follows `person.greeting`. These steps run in the browser. No request reaches
the server while you type.

Next: [Writing pages for these hosts](010-writing-pages.md).
