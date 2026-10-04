# Quick start

A field bound to `person.name` and a greeting computed by the method `greeting`
of the page's `Logic`, in the page module `01_quick_start.js`. Typing in the field
changes the greeting at every keystroke.

`gramlot fastapi new my-site` writes this page as `pages/index.py` and
`pages/index.js`, with `requirements.txt` and `app.py`:

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

```sh
cd my-site
python -m pip install -r requirements.txt
uvicorn app:app
```
