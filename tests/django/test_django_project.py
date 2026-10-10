"""``gramlot django new`` creates the quick start project, which serves its page.

The project runs in a child process: it configures Django from its own
``settings.py``, which the adapter tests of this process cannot share.
"""
import json
import os
import subprocess
import sys

from project_checks import check_document, check_files, check_main
from rpc_checks import rpc_source

CHECK = """
import json, re
import django
django.setup()
from django.test import Client
client = Client()
document = client.get("/")
page_id = re.search(r'"pageId":"([0-9a-f]+)"', document.content.decode()).group(1)
envelope = json.dumps({"id": "1", "pageId": page_id, "contentType": "source", "name": "main", "params": {}})
main = client.post("/gramlot/rpc", envelope, content_type="application/json")
logic = client.get("/index.js")
print(json.dumps({
    "status": document.status_code,
    "document": document.content.decode(),
    "policy": document["Content-Security-Policy"],
    "main": main.content.decode(),
    "logic_type": logic["Content-Type"],
    "logic": logic.content.decode(),
}))
"""


def test_new_project_serves_the_page_and_its_logic(new_project, capsys, source_tags):
    folder, _ = new_project("django")
    check_files(folder, "settings.py", "gramlot-py-server[django]>=0.2.3",
                "django-admin runserver --settings=settings --pythonpath=.", capsys.readouterr().out)
    paths = [str(folder), os.environ.get("PYTHONPATH", "")]
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "settings", "PYTHONPATH": os.pathsep.join(filter(None, paths))}
    completed = subprocess.run([sys.executable, "-c", CHECK], cwd=folder, env=env,
                               capture_output=True, text=True, check=True)
    result = json.loads(completed.stdout)
    assert result["status"] == 200
    check_document(result["document"], result["policy"])
    assert result["logic_type"] == "text/javascript; charset=utf-8"
    assert "greeting(kwargs)" in result["logic"]
    check_main(source_tags(rpc_source(result["main"])))
