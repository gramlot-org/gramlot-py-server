# Quick start

A field bound to `person.name` and a greeting computed by the method `greet` of
the page's `Logic`, in the page module `01_quick_start.js`. Typing in the field
changes the greeting at every keystroke.

`gramlot django new my-site` writes this page as `pages/index.py` and
`pages/index.js`, with `requirements.txt` and `settings.py` and `urls.py`:

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

```sh
cd my-site
python -m pip install -r requirements.txt
django-admin runserver --settings=settings --pythonpath=.
```
