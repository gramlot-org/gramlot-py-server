# 205 · Django

Document ID: **GP-205**.

Derived from GD-090 (gramlot-django).

[Paired view](../docs_llm/205-django.md).

`gramlot_py_server.django.Pages` serves a pages folder from a Django project.
Its `urlpatterns` go into a URLconf. The rules common to every adapter
are in the [Introduction](005-introduction.md) and in
[Writing pages for these hosts](010-writing-pages.md).

<a id="gp-205-005"></a>

## 005 · Install

Block ID: **GP-205-005**.

```sh
python -m pip install "gramlot-py-server[django]"
```

The extra `django` installs `Django>=5.2,<6.2` and `asgiref>=3.8.1,<4`.

<a id="gp-205-010"></a>

## 010 · Create a project

Block ID: **GP-205-010**.

`gramlot django new` writes the quick start project of the README
([The gramlot command](020-command.md)):

```sh
gramlot django new my-site
cd my-site
python -m pip install -r requirements.txt
django-admin runserver --settings=settings --pythonpath=.
```

Beside `pages/index.py`, `pages/index.js` and `requirements.txt` the project has
`settings.py` and `urls.py`:

`settings.py`:

```python
"""Django settings: ``django-admin runserver --settings=settings --pythonpath=.``."""

SECRET_KEY = "development-only-change-me"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
ROOT_URLCONF = "urls"
INSTALLED_APPS: list[str] = []
MIDDLEWARE = ["django.middleware.csrf.CsrfViewMiddleware"]
```

`urls.py`:

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

Open <http://127.0.0.1:8000/>. The page shows a field with `Ada` and the text
`Hello, Ada`. It has no inline code, so the project sends the strict profile.
The test `tests/django/test_django_project.py` creates the project and serves it
with Django's test client, in a child process configured from its `settings.py`.
The adapter tests of `tests/django/test_django.py` run with `CsrfViewMiddleware`
and CSRF checks enabled.

`gramlot django gallery` serves the example gallery with this adapter.

<a id="gp-205-015"></a>

## 015 · Mounting and options

Block ID: **GP-205-015**.

Add `pages.urlpatterns` to the URLconf:

```python
pages = Pages(PAGES, mount_path="/py")
urlpatterns = [*pages.urlpatterns]
```

`pages.urlpatterns` is `[path("py", …), path("py/", include(pages.urls))]`.
The first pattern answers `/py` with 301 to `/py/`, with the query string:
pages link each other with relative URLs. The URLconf removes `py/` from the
path before the views of `Pages` see it. `mount_path` goes to `open_page` as
the prefix of the browser URLs and to the `Path` of the owner cookie. The page
`index` opens at `/py/`. Without a prefix `pages.urlpatterns` is
`[path("", include(pages.urls))]`, the URLconf of the quick start.

`include(pages.urls)` written by hand at the path of `mount_path` serves the
same pages without the 301 of `/py`. A different path in `include()` and in
`mount_path` gives browser URLs that the URLconf does not route.

`Pages` takes `page_ttl`, `max_pages`, `content_security_policy` and `assets`
with the meaning of the [Uvicorn options](110-configuration.md). One `Pages` instance
owns one page registry. Create it once, at URLconf import, not per request.

<a id="gp-205-020"></a>

## 020 · What is served and Django specifics

Block ID: **GP-205-020**.

`pages.urls` holds six patterns, in this order: `assets/gramlot.js`,
`gramlot/main`, `gramlot/source`, `gramlot/close`, `""` and
`<path:page_path>`. The last two serve the pages, the files of `assets` and
the companions.

- **CSRF.** The Gramlot runtime posts JSON without a Django CSRF token, so the
  views of `main`, `source` and `close` are wrapped in `csrf_exempt`. The
  runtime, page and companion views are exempt too: they accept no `POST`, and
  the view answers 405 where `CsrfViewMiddleware` would answer 403, as GC-230
  of the core requires.
- **Synchronous views.** The views are plain Django functions. They call the
  asynchronous core `GramlotFileServer` through `asgiref.sync.async_to_sync`.
- **`HEAD` on a page.** The page view accepts `GET` and `HEAD`. A `HEAD` opens
  a page and sets the cookie; Django sends no body.
- **Responses.** Pages, companions and protocol answers carry
  `Cache-Control: no-store`. The runtime is a `FileResponse` with
  `Content-Type: text/javascript` and `Cache-Control: no-cache`. Error
  messages are plain text in a response with Django's default content type
  `text/html; charset=utf-8`. 405 answers carry no `Allow` header.
- **Request body.** The protocol views read `request.body` and answer 413 when
  it is longer than 4096 bytes. `request.content_type` is compared with
  `application/json`; parameters such as `charset` are not part of it.
- **Errors.** An exception of the page's own code reaches Django, which
  answers 500.
- **Workers.** The page registry lives in the process. Run one worker, or keep
  a browser on the same worker.

<a id="gp-205-025"></a>

## 025 · API reference

Block ID: **GP-205-025**.

`from gramlot_py_server.django import Pages`

Module functions, outside `__all__`:

- `serve(pages, *, host="127.0.0.1", port=8000, **options)`: configures Django
  with a `ROOT_URLCONF` that holds `Pages(pages, **options).urlpatterns` and runs
  `runserver` without the reloader. The process must not have configured Django
  before.
- `commands(verbs)`: adds the verbs `new` and `gallery` of `gramlot django`, an
  entry point of `gramlot_py_server.commands` ([The gramlot command](020-command.md)).

`Pages(pages, *, mount_path="", page_ttl=1800, max_pages=1000,
content_security_policy=None, assets=None)`

- `urlpatterns`: the URL patterns for the URLconf, `urls` included at
  `mount_path` and the 301 of the bare prefix.
- `urls`: the list of URL patterns to pass to `include()`.
- `server`: the core `GramlotFileServer` built on `pages` with the URLs
  `/assets/gramlot.js`, `/gramlot/main`, `/gramlot/source`, `/gramlot/close`.
- `mount_path`: the normalized prefix (`""` or `/py`).
- `content_security_policy`: the configured policy or `None`.
- `assets`: the map of URLs to files, `{}` when not given.
- `asset`, `page`, `static`, `companion`, `main`, `source`, `close`: the views
  behind `urls`; `redirect`: the view of the bare prefix.

| Method and path | Answer |
| --- | --- |
| `GET`, `HEAD /<page path>` | 200 `text/html; charset=utf-8`, the bootstrap document, with `Set-Cookie: gramlot_owner=…` and, when configured, `Content-Security-Policy`; 404 `Page not found`; 503 `Page capacity reached` |
| `GET`, `HEAD /<page path>/index.html`, `/index.html` | as `GET /<page path>` for the page `<page path>`, as `GET /` for the page `index` |
| other methods on a page path | 405 |
| `GET`, `HEAD /assets/gramlot.js` | 200 `text/javascript`, the runtime; 405 for other methods |
| `GET /py` (the bare prefix) | 301, `Location: /py/` with the query string |
| `GET`, `HEAD /themes/<file>` | 200, the file of the core themes with the media type of its extension; a file the core does not have goes on to the rows below |
| `GET`, `HEAD` of a URL of `assets` | 200, the file with the media type of the map; 405 for other methods |
| `GET`, `HEAD /<file>.css`, `/<file>.js` | 200 `text/css; charset=utf-8` or `text/javascript; charset=utf-8` when the real path is below the pages folder; 404 `Not found` otherwise; other methods as on a page path |
| `POST /gramlot/main`, `/gramlot/source`, `/gramlot/close` | as the [Uvicorn endpoints](120-reference.md); 405 for other methods |

Source methods (`@source`, `remoteSource`) are not yet part of the page-writing API: they arrive together with the `remote` grammar attribute and `@endpoint`.
