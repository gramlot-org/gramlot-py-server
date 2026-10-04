"""The Django example serves the pages of the README and the tutorial.

The example runs in a child process: it configures Django from its own
``settings.py``, which the adapter tests of this process cannot share.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "examples" / "django"

CHECK = """
import json, re
import django
django.setup()
from django.test import Client
client = Client()
document = client.get("/hello")
page_id = re.search(r'"pageId":"([0-9a-f]+)"', document.content.decode()).group(1)
main = client.post("/gramlot/main", json.dumps({"pageId": page_id}), content_type="application/json")
print(json.dumps({
    "status": document.status_code,
    "title": "<title>Hello</title>" in document.content.decode(),
    "policy": document["Content-Security-Policy"],
    "main": main.content.decode(),
    "greeting": client.get("/greeting").status_code,
    "css": client.get("/greeting.css")["Content-Type"],
    "aux": b"greet(kwargs)" in client.get("/greeting_aux.js").content,
}))
"""


def test_example_serves_the_quick_start_page_and_the_companions(source_tags):
    paths = [str(EXAMPLE), os.environ.get("PYTHONPATH", "")]
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "settings", "PYTHONPATH": os.pathsep.join(filter(None, paths))}
    completed = subprocess.run([sys.executable, "-c", CHECK], cwd=EXAMPLE, env=env,
                               capture_output=True, text=True, check=True)
    result = json.loads(completed.stdout)
    assert result["status"] == 200
    assert result["title"] is True
    assert "'unsafe-eval'" in result["policy"]
    tags = source_tags(result["main"])
    assert tags["input"]["value"] == "^.name"
    assert tags["dataFormula"]["formula"] == "'Hello, ' + name"
    assert result["greeting"] == 200
    assert result["css"] == "text/css; charset=utf-8"
    assert result["aux"] is True
