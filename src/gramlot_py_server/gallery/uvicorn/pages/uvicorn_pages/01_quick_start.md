# Quick start

A field bound to `person.name` and a greeting computed by the method `greet` of
the page's `Logic`, in the page module `01_quick_start.js`. Typing in the field
changes the greeting at every keystroke.

`gramlot uvicorn new my-site` writes this page as `pages/index.py` and
`pages/index.js`, with `requirements.txt` and `app.py`:

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

```sh
cd my-site
python -m pip install -r requirements.txt
uvicorn app:application
```
