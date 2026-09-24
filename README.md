<p><img src="docs/_static/gramlot-logo.png" alt="Gramlot logo" width="120"></p>

# gramlot-django

Django integration for the native Gramlot 0.1.0 `Page` and `Host` contract. This is local development work on `develop`; it has not been published or accepted as a release.

The installable package exports `NativeHtmlPages`. It mounts Gramlot's page HTML, browser runtime, Source requests and page-close endpoint on a normal Django URLconf. Page definitions use `gramlot.Page`, `gramlot.source` and Gramlot's Source builder. The adapter adds no ORM or database capability.

```python
# project/urls.py
from pathlib import Path
from django.urls import include, path
from gramlot_django import NativeHtmlPages

pages = NativeHtmlPages(Path(__file__).parent / "pages", prefix="/hello")
urlpatterns = [path("hello/", include(pages.urls))]
```

```python
# project/pages/index.py
from gramlot import Page as Base, source

class Page(Base):
    title = "Hello Django"

    def main(self, root):
        root.h1("Hello Django")

    @source
    def detail(self, root, name):
        root.p(name)
```

Open `/hello/`. The declared `prefix` and Django mount path must match. `NativeHtmlPages` owns an in-process, expiring page registry; use one integration instance per mount. Its HttpOnly, same-site cookie associates subsequent browser requests with a page, but does not authenticate users. The JSON endpoints use Django's CSRF exemption because the current shared Gramlot browser transport sends JSON without a CSRF token. Treat the pages directory as trusted application code and apply Django authorization at the surrounding site boundary. This adapter does not provide a shared registry across workers.

The extracted PoC Page/ORM adapter, its demo, and tests are retained under [historical](historical/) for later bounded transfer and cleanup. The former examples and guides describe that experimental lane; they are not evidence of native 0.1.0 compatibility. The native contract and verification are documented in [GD-090](docs/090-native-html.md). See the [Gramlot constitution](https://github.com/gramlot-org/gramlot/blob/main/docs/00-constitution.md) for ownership rules.

For local verification with native core 0.1.0 and Django installed, run `python scripts/check.py`. No package registry publication or application deployment is part of this work.

Apache License 2.0. Copyright 2026 Softwell S.r.l. See LICENSE and NOTICE.
