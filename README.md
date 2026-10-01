# Gramlot Uvicorn

[![tests](https://github.com/gramlot-org/gramlot-uvicorn/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/gramlot-org/gramlot-uvicorn/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/gh/gramlot-org/gramlot-uvicorn/branch/main/graph/badge.svg)](https://app.codecov.io/gh/gramlot-org/gramlot-uvicorn)
[![Documentation](https://readthedocs.org/projects/gramlot-uvicorn/badge/?version=latest)](https://gramlot-uvicorn.readthedocs.io/en/latest/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

Gramlot describes web interfaces in Python or JavaScript and keeps them bound to
application state in the browser. See
[The Gramlot family](https://gramlot.readthedocs.io/en/latest/docs/public/055-family.html)
for the core and the other repositories.

## What this repository is

`gramlot-uvicorn` serves Gramlot pages written in Python from a Python web
server. It is an ASGI application: Uvicorn runs it, and so does any other ASGI
server. Choose it when your pages are Python classes and you want a server to
open them for the browser. It does not serve JavaScript pages
([gramlot-js-server](https://github.com/gramlot-org/gramlot-js-server) does)
and it does not produce a page that opens without a server
([gramlot-serverless](https://github.com/gramlot-org/gramlot-serverless) does).

## Quick start

Install the released core and the adapter from this checkout (Python 3.11 or
later):

```sh
python -m pip install "gramlot>=0.2.0" ".[uvicorn]"
```

Create a folder `pages` and write `pages/hello.py`:

```python
from gramlot import Page as BasePage


class Page(BasePage):
    title = "Hello"

    def main(self, root):
        pane = root.div(datapath="person")
        pane.html_label("Name", for_="name")
        pane.input(id="name", value="^.name", live=True)
        pane.p("^.greeting")
        pane.dataFormula(".greeting", "'Hello, ' + name", name="^.name", _init=True)
        pane.dataSetter(".name", "Ada")
```

Write `app.py` beside the folder. The formula of this page is inline code, so
the page needs the permissive Content Security Policy profile:

```python
from gramlot_uvicorn import create_asgi_application

application = create_asgi_application(
    "pages",
    content_security_policy="script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'",
)
```

Serve it and open <http://127.0.0.1:8000/hello>:

```sh
uvicorn app:application
```

The page shows a field with `Ada` and the text `Hello, Ada`. Typing `Grace` in
the field changes the text to `Hello, Grace` at every keystroke. The test
`tests/test_examples.py` serves this page in CI and checks that the README
shows the same file.

## Next steps

- [Introduction](https://gramlot-uvicorn.readthedocs.io/en/latest/105-introduction.html),
  [Tutorial](https://gramlot-uvicorn.readthedocs.io/en/latest/110-tutorial.html),
  [Writing pages for this host](https://gramlot-uvicorn.readthedocs.io/en/latest/115-writing-pages.html),
  [Configuration](https://gramlot-uvicorn.readthedocs.io/en/latest/120-configuration.html),
  [Deployment](https://gramlot-uvicorn.readthedocs.io/en/latest/125-deployment.html),
  [Reference](https://gramlot-uvicorn.readthedocs.io/en/latest/130-reference.html),
  [Troubleshooting](https://gramlot-uvicorn.readthedocs.io/en/latest/140-troubleshooting.html):
  the guides of this repository (sources in `docs/`, concise view in `docs_llm/`).
- Core guides: [The Gramlot family](https://gramlot.readthedocs.io/en/latest/docs/public/055-family.html),
  [Classes and server adapters](https://gramlot.readthedocs.io/en/latest/docs/public/090-classes-and-hosts.html)
  (the adapter contract: mount prefix, companions, Content Security Policy profiles),
  [Writing pages](https://gramlot.readthedocs.io/en/latest/docs/public/095-writing-pages.html)
  (the binding).
- Core example families, every page in Python and JavaScript:
  [examples/binding](https://github.com/gramlot-org/gramlot/tree/main/examples/binding) and
  [examples/controllers](https://github.com/gramlot-org/gramlot/tree/main/examples/controllers).

## Compatibility

| | Verified |
| --- | --- |
| Gramlot core | 0.2.0 (PyPI `gramlot`) |
| Python | 3.11 and 3.12 in CI; 3.12.9 in the 0.2.0 qualification |
| Browsers | Chromium 153, WebKit 26.6, Firefox 155 (0.2.0 qualification of the core, acceptance pages under the strict and the permissive profile) |

## Contributing

`AGENTS.md` and `CONTRIBUTING.md` hold the rules; `docs/internal/` holds the
architecture notes and the verification records.
