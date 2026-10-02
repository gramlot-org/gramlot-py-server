# 205 · Django

Document ID: **GP-205**.

Derived from GD-090 (gramlot-django).

[Paired view](../docs/205-django.md).

`gramlot_py_server.django.Pages` serves a pages folder from a Django project.
Its views go into a URLconf with `include()`. The rules common to every adapter
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

## 010 · Run the example

Block ID: **GP-205-010**.

The example lives in the repository, beside the folder `examples/pages`.

`examples/django/settings.py`:

```python
"""Django settings of the example: ``django-admin runserver --settings=settings --pythonpath=.``."""

SECRET_KEY = "example-only-change-me"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
ROOT_URLCONF = "urls"
INSTALLED_APPS: list[str] = []
MIDDLEWARE = ["django.middleware.csrf.CsrfViewMiddleware"]
```

`examples/django/urls.py`:

```python
"""URLconf of the example: the Gramlot pages at the site root."""
from pathlib import Path

from django.urls import include, path

from gramlot_py_server.django import Pages

PAGES = Path(__file__).resolve().parents[1] / "pages"

pages = Pages(
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'",
)

urlpatterns = [path("", include(pages.urls))]
```

From the folder `examples/django`:

```sh
django-admin runserver --settings=settings --pythonpath=.
```

Open <http://127.0.0.1:8000/hello>. The permissive profile is sent because
`hello.py` uses inline code. The test `tests/django/test_django_examples.py`
serves this example with Django's test client, in a child process configured
from `settings.py`. The adapter tests of `tests/django/test_django.py` run with
`CsrfViewMiddleware` and CSRF checks enabled.

<a id="gp-205-015"></a>

## 015 · Mounting and options

Block ID: **GP-205-015**.

Include `pages.urls` at the same path given as `mount_path`:

```python
pages = Pages(PAGES, mount_path="/py")
urlpatterns = [path("py/", include(pages.urls))]
```

The URLconf removes `py/` from the path before the views of `Pages` see it.
`mount_path` goes to `open_page` as the prefix of the browser URLs and to the
`Path` of the owner cookie. A different value in the two places gives URLs that
the URLconf does not route. The page `index` opens at `/py/`.

`Pages` takes `page_ttl`, `max_pages` and `content_security_policy` with the
meaning of the [Uvicorn options](110-configuration.md). One `Pages` instance
owns one page registry. Create it once, at URLconf import, not per request.

<a id="gp-205-020"></a>

## 020 · What is served and Django specifics

Block ID: **GP-205-020**.

`pages.urls` holds six patterns, in this order: `assets/gramlot.js`,
`gramlot/main`, `gramlot/source`, `gramlot/close`, `""` and
`<path:page_path>`. The last two serve the pages and the companions.

- **CSRF.** The Gramlot runtime posts JSON without a Django CSRF token, so the
  views of `main`, `source` and `close` are wrapped in `csrf_exempt`. The page
  and companion views are not exempt: with `CsrfViewMiddleware` a `POST` on
  them answers 403 before the view runs; without it the view answers 405.
- **Synchronous views.** The views are plain Django functions. They call the
  asynchronous core `FileHost` through `asgiref.sync.async_to_sync`.
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

`Pages(pages, *, mount_path="", page_ttl=1800, max_pages=1000,
content_security_policy=None)`

- `urls`: the list of URL patterns to pass to `include()`.
- `host`: the core `FileHost` built on `pages` with the URLs
  `/assets/gramlot.js`, `/gramlot/main`, `/gramlot/source`, `/gramlot/close`.
- `mount_path`: the normalized prefix (`""` or `/py`).
- `content_security_policy`: the configured policy or `None`.
- `asset`, `page`, `companion`, `main`, `source`, `close`: the views behind
  `urls`.

| Method and path | Answer |
| --- | --- |
| `GET`, `HEAD /<page path>` | 200 `text/html; charset=utf-8`, the bootstrap document, with `Set-Cookie: gramlot_owner=…` and, when configured, `Content-Security-Policy`; 404 `Page not found`; 503 `Page capacity reached` |
| other methods on a page path | 405, or 403 from `CsrfViewMiddleware` for `POST` |
| `GET`, `HEAD /assets/gramlot.js` | 200 `text/javascript`, the runtime; 405 for other methods |
| `GET`, `HEAD /<file>.css`, `/<file>_aux.js` | 200 `text/css; charset=utf-8` or `text/javascript; charset=utf-8` when the real path is below the pages folder; 404 `Not found` otherwise; other methods as on a page path |
| `POST /gramlot/main`, `/gramlot/source`, `/gramlot/close` | as the [Uvicorn endpoints](120-reference.md); 405 for other methods |
