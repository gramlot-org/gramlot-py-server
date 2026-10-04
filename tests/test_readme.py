"""The README shows the templates that ``gramlot <framework> new`` writes."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "src" / "gramlot_py_server" / "templates"
PYTHON = [
    "pages/index.py",
    "uvicorn/app.py",
    "django/settings.py",
    "django/urls.py",
    "flask/app.py",
    "fastapi/app.py",
    "kajenn/config.py",
]
JAVASCRIPT = ["pages/index.js"]


def test_readme_code_blocks_are_the_templates_in_order():
    readme = (ROOT / "README.md").read_text()
    assert re.findall(r"```python\n(.*?)```", readme, re.S) == [(TEMPLATES / name).read_text() for name in PYTHON]
    assert re.findall(r"```js\n(.*?)```", readme, re.S) == [(TEMPLATES / name).read_text() for name in JAVASCRIPT]
