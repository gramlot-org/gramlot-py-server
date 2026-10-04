# Quick start

A field bound to `person.name` and a greeting computed by the method `greeting`
of the page's `Logic`, in the page module `01_quick_start.js`. Typing in the field
changes the greeting at every keystroke.

`gramlot flask new my-site` writes this page as `pages/index.py` and
`pages/index.js`, with `requirements.txt` and `app.py`:

```python
"""Serve the pages inside a Flask app: ``flask --app app run``."""
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

```sh
cd my-site
python -m pip install -r requirements.txt
flask --app app run
```
