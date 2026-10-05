# gramlot-py-server

[![tests](https://github.com/gramlot-org/gramlot-py-server/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/gramlot-org/gramlot-py-server/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/gh/gramlot-org/gramlot-py-server/branch/main/graph/badge.svg)](https://app.codecov.io/gh/gramlot-org/gramlot-py-server)
[![Documentation](https://readthedocs.org/projects/gramlot-py-server/badge/?version=latest)](https://gramlot-py-server.readthedocs.io/en/latest/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

Gramlot describes web interfaces in Python or JavaScript and keeps them bound to
application state in the browser. See
[The Gramlot family](https://gramlot.readthedocs.io/en/latest/docs/public/055-family.html)
for the core and the other repositories.

## What this repository is

`gramlot-py-server` serves Gramlot pages written in Python from a Python web
server. One package holds one adapter per framework; each comes with its extra:

| Extra | Module | Names |
| --- | --- | --- |
| `uvicorn` | `gramlot_py_server.uvicorn` | `Application`, `create_application(pages, **options)`: an ASGI application for Uvicorn or any ASGI server |
| `django` | `gramlot_py_server.django` | `Pages`: its `urlpatterns` go into a URLconf |
| `flask` | `gramlot_py_server.flask` | `Pages`, `mount_pages(app, pages, **options)` |
| `fastapi` | `gramlot_py_server.fastapi` | `Pages`, `mount_pages(app, pages, **options)`, `Application` |
| `kajenn` | `gramlot_py_server.kajenn` | `Application`: a Kajenn routed application |

Every adapter serves one folder of `Page` modules through the core `FileHost`:
it sends the bootstrap document, answers the main and remote Source requests,
serves the page companions (`.css` and `.js`), an optional map of assets and
the browser runtime, with a mount prefix and a Content Security Policy of your
choice. It does not serve JavaScript pages
([gramlot-js-server](https://github.com/gramlot-org/gramlot-js-server) does)
and it does not talk to a database.

## Quick start

Python 3.11 or later. Install the package with the extra of your framework,
then create a project with `gramlot <framework> new <folder>`:

```sh
python -m pip install "gramlot-py-server[uvicorn]"
gramlot uvicorn new hello
cd hello
uvicorn app:application
```

Open <http://127.0.0.1:8000/>. The page shows a field with `Ada` and the text
`Hello, Ada`. Typing `Grace` in the field changes the text to `Hello, Grace` at
every keystroke.

The command writes the same page for every framework, `pages/index.py`:

```python
from gramlot import Page as BasePage


class Page(BasePage):
    title = "Hello"

    def main(self, root):
        pane = root.div(datapath="person")
        pane.html_label("Name", for_="name")
        pane.input(id="name", value="^.name", live=True)
        pane.p("^.greeting")
        pane.dataFormula(".greeting", func="greeting", name="^.name", _init=True)
        pane.dataSetter(".name", "Ada")
```

and its page module `pages/index.js`. The formula names its method with
`func="greeting"`; the method is in the `Logic` export and runs in the browser:

```js
export class Logic {
    greeting(kwargs) { return 'Hello, ' + kwargs.name; }
}
```

The page has no inline code, so every project sends the strict Content Security
Policy profile. Beside `pages/` the command writes `requirements.txt`, with the
extra of the framework, and the files of the framework below. The docstring of
each file gives the command that starts it, which `gramlot` also prints.

Uvicorn, `gramlot uvicorn new`, `app.py`:

```python
"""Serve the pages with Uvicorn: ``uvicorn app:application``."""
from pathlib import Path

from gramlot_py_server.uvicorn import create_application

PAGES = Path(__file__).resolve().parent / "pages"

application = create_application(
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)
```

Django, `gramlot django new`, `settings.py` and `urls.py`:

```python
"""Django settings: ``django-admin runserver --settings=settings --pythonpath=.``."""

SECRET_KEY = "development-only-change-me"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
ROOT_URLCONF = "urls"
INSTALLED_APPS: list[str] = []
MIDDLEWARE = ["django.middleware.csrf.CsrfViewMiddleware"]
```

```python
"""URLconf: the Gramlot pages at the site root."""
from pathlib import Path

from gramlot_py_server.django import Pages

PAGES = Path(__file__).resolve().parent / "pages"

pages = Pages(
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)

urlpatterns = [*pages.urlpatterns]
```

Flask, `gramlot flask new`, `app.py`:

```python
"""Serve the pages inside a Flask app: ``flask --app app run --port 8000``."""
from pathlib import Path

from flask import Flask

from gramlot_py_server.flask import mount_pages

PAGES = Path(__file__).resolve().parent / "pages"

app = Flask(__name__)
mount_pages(
    app,
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)
```

FastAPI, `gramlot fastapi new`, `app.py`; `requirements.txt` installs FastAPI
with Uvicorn:

```python
"""Serve the pages inside a FastAPI app: ``uvicorn app:app``."""
from pathlib import Path

from fastapi import FastAPI

from gramlot_py_server.fastapi import mount_pages

PAGES = Path(__file__).resolve().parent / "pages"

app = FastAPI()
mount_pages(
    app,
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)
```

Kajenn, `gramlot kajenn new`, `config.py`; the page opens at
<http://127.0.0.1:8000/pages/>:

```python
"""Kajenn site: ``kajenn serve config.py --port 8000``, pages under ``/pages/``."""
from pathlib import Path

from kajenn.config.templates import DefaultConfiguration

from gramlot_py_server.kajenn import Application

PAGES = Path(__file__).resolve().parent / "pages"


class Site(DefaultConfiguration):
    def applications_section(self, cfg):
        cfg.applications().application(
            code="pages",
            mount="pages",
            app_class=Application,
            pages=PAGES,
            content_security_policy=(
                "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"
            ),
        ).request(body="raw")
```

The tests `tests/<framework>/test_<framework>_project.py` create each project
with `gramlot <framework> new` and serve it, and `tests/test_readme.py` checks
that this README shows the same files. A project that already exists, such as a
Django site, needs no `new`: the guide of its framework shows how to add the
pages to it.

## Next steps

- The guides on Read the Docs, sources in [docs/](docs/) and the paired view
  in [docs_llm/](docs_llm/):
  - common: [Introduction](https://gramlot-py-server.readthedocs.io/en/latest/005-introduction.html),
    [Writing pages for these hosts](https://gramlot-py-server.readthedocs.io/en/latest/010-writing-pages.html),
    [Troubleshooting](https://gramlot-py-server.readthedocs.io/en/latest/015-troubleshooting.html),
    [The gramlot command](https://gramlot-py-server.readthedocs.io/en/latest/020-command.html): `new` and `gallery`;
  - Uvicorn: [Tutorial](https://gramlot-py-server.readthedocs.io/en/latest/105-tutorial.html),
    [Configuration](https://gramlot-py-server.readthedocs.io/en/latest/110-configuration.html),
    [Deployment](https://gramlot-py-server.readthedocs.io/en/latest/115-deployment.html),
    [Reference](https://gramlot-py-server.readthedocs.io/en/latest/120-reference.html);
  - [Django](https://gramlot-py-server.readthedocs.io/en/latest/205-django.html), [Flask](https://gramlot-py-server.readthedocs.io/en/latest/305-flask.html),
    [FastAPI](https://gramlot-py-server.readthedocs.io/en/latest/405-fastapi.html), [Kajenn](https://gramlot-py-server.readthedocs.io/en/latest/505-kajenn.html).
- The core: [The Gramlot family](https://gramlot.readthedocs.io/en/latest/docs/public/055-family.html),
  [Classes, repository and server adapters](https://gramlot.readthedocs.io/en/latest/docs/public/090-classes-and-hosts.html)
  (the shared adapter contract: mount prefix, companions, CSP profiles),
  [Writing pages](https://gramlot.readthedocs.io/en/latest/docs/public/095-writing-pages.html).

## Compatibility

| | Verified |
| --- | --- |
| Gramlot core | 0.2.6 (PyPI `gramlot`) |
| Gallery | `gramlot-examples` 0.2.5 (extra `gallery`) |
| Python | 3.11 and 3.12 in CI; 3.11.11 and 3.12.9 locally |
| Frameworks | Uvicorn 0.54.0, Django 6.1.1 with asgiref 3.12.1, Flask 3.1.3, FastAPI 0.142.2, Kajenn 0.1.1 |
| Browsers | Chromium 153 in CI; Chromium 153 and WebKit 26.6 locally, with Playwright 1.63.0 |

## Tests and contributing

```sh
python -m pip install -e ".[uvicorn,django,flask,fastapi,kajenn,gallery,test]"
python -m pytest -q                      # every adapter
python -m pytest -q tests/flask          # one adapter, with its extra only
python scripts/check_docs.py             # paired guides and Sphinx build
```

The browser checks need Node.js and Playwright; `PLAYWRIGHT_ENTRY` is the path
of `playwright/index.mjs`:

```sh
node scripts/verify_browser.mjs "$(command -v python)" "$PLAYWRIGHT_ENTRY" chromium
node scripts/verify_gallery_browser.mjs "$(command -v python)" "$PLAYWRIGHT_ENTRY" chromium
python scripts/verify_install.py flask dist/gramlot_py_server-*.whl "$PLAYWRIGHT_ENTRY"
```

CI runs each adapter with its own extra against the released core and, as an
informational job, every adapter against the core's `main` checkout; it runs the
browser checks in Chromium and a clean install of each environment from the
built wheel, and builds the documentation; coverage goes to Codecov with one
flag per framework. See
[CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md); the internal
notes are in [docs/internal/](docs/internal/).

Apache License 2.0. Copyright 2026 Softwell S.r.l. See [LICENSE](LICENSE) and
[NOTICE](NOTICE).
