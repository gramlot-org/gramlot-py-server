# 090 · Native HTML integration

Document ID: **GD-090**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-django/blob/develop/docs_llm/090-native-html.md).

<a id="gd-090-005"></a>

## 005 · Scope

Block ID: **GD-090-005**.

The native package translates Gramlot 0.1.0 `Host` requests into Django URLs
and responses. It does not implement the old DjangoPage or ORM APIs. This is local
development work awaiting further PoC transfer, cleanup and acceptance; no new
GitHub publication or registry release has been made.

<a id="gd-090-010"></a>

## 010 · URL configuration

Block ID: **GD-090-010**.

Create Python `Page` files using `gramlot.Page`, with an `index.py` for the
mount root. Mount the adapter on a Django URLconf:

```python
from pathlib import Path
from django.urls import include, path
from gramlot_django import NativeHtmlPages

pages = NativeHtmlPages(Path(__file__).parent / "pages", prefix="/hello")
urlpatterns = [path("hello/", include(pages.urls))]
```

The `prefix` must match the URLconf mount. The adapter serves the bootstrap
at `/hello/`, the packaged runtime at `/hello/assets/gramlot.js`, and JSON
POST endpoints at `/hello/gramlot/main`, `source` and `close`. It maps
missing pages and expired/unowned page IDs to 404, registry capacity to 503,
invalid JSON to 400, wrong media type to 415 and excessive bodies to 413.

<a id="gd-090-015"></a>

## 015 · Lifecycle and limits

Block ID: **GD-090-015**.

Each `NativeHtmlPages` instance owns an in-process, expiring `Host` registry.
The same-site HttpOnly cookie associates browser requests with page records;
it is not a login or permission mechanism. The current Gramlot transport sends
JSON without Django CSRF tokens, so main, source and close are CSRF-exempt.
The site must enforce its own access policy around the pages it exposes.
The pages directory contains trusted Python application code. A shared registry
across workers is not implemented.

<a id="gd-090-020"></a>

## 020 · Verification boundary

Block ID: **GD-090-020**.

The native test suite exercises Django's test client with CSRF checks enabled:
bootstrap, packaged runtime, Source transport, owner isolation and close.
The historical PoC suite is retained separately and does not verify this
native contract. Run `python scripts/check.py` in an environment with native
Gramlot, Django, Ruff, pytest and Sphinx installed.
