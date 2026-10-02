"""The README shows the example files that the framework tests serve."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
SHOWN = [
    "pages/hello.py",
    "uvicorn/app.py",
    "django/settings.py",
    "django/urls.py",
    "flask/app.py",
    "fastapi/app.py",
    "kajenn/config.py",
]


def test_readme_python_blocks_are_the_example_files_in_order():
    readme = (ROOT / "README.md").read_text()
    blocks = re.findall(r"```python\n(.*?)```", readme, re.S)
    assert blocks == [(EXAMPLES / name).read_text() for name in SHOWN]
