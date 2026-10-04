# Quick start

A field bound to `person.name` and a greeting computed by the method `greeting`
of the page's `Logic`, in the page module `01_quick_start.js`. Typing in the field
changes the greeting at every keystroke.

`gramlot kajenn new my-site` writes this page as `pages/index.py` and
`pages/index.js`, with `requirements.txt` and `config.py`:

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

```sh
cd my-site
python -m pip install -r requirements.txt
kajenn serve config.py --port 8000
```
