# 090 · Native HTML integration

Document ID: **GD-090**.

[Expanded counterpart](../docs/090-native-html.md).

<a id="gd-090-005"></a>

## 005 · Scope

Block ID: **GD-090-005**.

The installable package maps native Gramlot 0.1.0 `Host` to Django. No
DjangoPage or ORM capability is included. The work is local and unaccepted;
further PoC transfer and cleanup precede publication.

<a id="gd-090-010"></a>

## 010 · URL configuration

Block ID: **GD-090-010**.

```python
from django.urls import include, path
from gramlot_django import NativeHtmlPages

pages = NativeHtmlPages("project/pages", prefix="/hello")
urlpatterns = [path("hello/", include(pages.urls))]
```

The prefix must equal the mount. GET serves page HTML and the packaged runtime;
JSON POST handles main, source and close. HTTP errors distinguish bad bodies,
unsupported media, missing pages, unowned IDs and capacity.

<a id="gd-090-015"></a>

## 015 · Lifecycle and limits

Block ID: **GD-090-015**.

Each adapter instance has an expiring process-local registry. Its same-site
HttpOnly owner cookie is not authentication. JSON routes are CSRF-exempt because
the current shared browser transport sends no CSRF token. Sites own access policy;
page files are trusted code. There is no shared multi-worker registry.

<a id="gd-090-020"></a>

## 020 · Verification boundary

Block ID: **GD-090-020**.

Native Django client tests cover bootstrap, runtime, Source, owner isolation
and close. Historical PoC tests remain separate. Run `python scripts/check.py`
with native Gramlot, Django, Ruff, pytest and Sphinx installed.
