# 110 · Tutorial

Document ID: **GS-110**.

[Paired view](../docs_llm/110-tutorial.md).

Every step of this tutorial is the content of `tests/pages` and
`tests/test_examples.py` of the repository, served by Uvicorn 0.54.0 with
`gramlot` 0.2.0 and checked in Chromium 153 on 2026-10-01.

<a id="gs-110-005"></a>

## 005 · Install

Block ID: **GS-110-005**.

Python 3.11 or later. From a checkout of this repository:

```sh
python -m venv .venv
.venv/bin/pip install "gramlot>=0.2.0" ".[uvicorn]"
```

`gramlot-uvicorn` is not published on PyPI; the core is.

<a id="gs-110-010"></a>

## 010 · Folder layout

Block ID: **GS-110-010**.

```text
app.py
pages/
  greeting.py        the page
  greeting_aux.js    its companion: named logic
  greeting.css       its stylesheet
```

The page, the companion and the stylesheet share the name `greeting`. The
`FileHost` of the core finds the two companions beside the page file and adds
them to the bootstrap document.

<a id="gs-110-015"></a>

## 015 · The page

Block ID: **GS-110-015**.

`pages/greeting.py`:

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
- `value="^.name"` binds the field to `person.name`; `live=True` writes every
  keystroke back into the Data.
- `"^.greeting"` as the text of the paragraph follows `person.greeting`.
- `dataFormula` computes `person.greeting` with the named method `greet` of the
  companion, with `name` bound to `person.name`; `_init=True` computes it once
  at start.
- `dataSetter` gives `person.name` its initial value.

<a id="gs-110-020"></a>

## 020 · The companion

Block ID: **GS-110-020**.

`pages/greeting_aux.js`:

```javascript
export class Logic {
    greet(kwargs) {
        return `Hello, ${kwargs.name}`;
    }
}
```

The module exports one class `Logic`. A formula method receives the resolved
parameters and returns the value. `func="greet"` in the page names it. The
companion runs in the browser; it is public.

<a id="gs-110-025"></a>

## 025 · The stylesheet

Block ID: **GS-110-025**.

`pages/greeting.css`:

```css
.greeting { font-family: sans-serif; padding: 1rem; }
.greeting p { color: #2a6; }
```

The bootstrap writes a `<link>` to `/greeting.css` before it imports the
companion.

<a id="gs-110-030"></a>

## 030 · Run it

Block ID: **GS-110-030**.

`app.py`, with the strict Content Security Policy profile. The page uses named
logic only, so the strict profile is enough:

```python
from gramlot_uvicorn import create_asgi_application

application = create_asgi_application(
    "pages",
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)
```

```sh
.venv/bin/uvicorn app:application
```

Open <http://127.0.0.1:8000/greeting>. The server log shows the requests of one
opening:

```text
INFO:     127.0.0.1:57903 - "GET /greeting HTTP/1.1" 200 OK
INFO:     127.0.0.1:57903 - "GET /assets/gramlot.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:57903 - "GET /greeting.css HTTP/1.1" 200 OK
INFO:     127.0.0.1:57903 - "GET /greeting_aux.js HTTP/1.1" 200 OK
INFO:     127.0.0.1:57903 - "POST /gramlot/main HTTP/1.1" 200 OK
INFO:     127.0.0.1:57903 - "GET /favicon.ico HTTP/1.1" 404 Not Found
```

The `favicon.ico` request comes from the browser; the adapter serves no icon.

<a id="gs-110-035"></a>

## 035 · What changes when you type

Block ID: **GS-110-035**.

The page shows a field with `Ada` and the green text `Hello, Ada`. Typing
`Grace` in the field changes the text to `Hello, Grace` at every keystroke: the
field writes `person.name`, the formula sees its `name` parameter change and
calls `greet` again, and the paragraph follows `person.greeting`. No request
reaches the server while you type; the server log stays as above.

Next: [Writing pages for this host](115-writing-pages.md).
