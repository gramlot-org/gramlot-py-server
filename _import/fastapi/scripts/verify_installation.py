# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Verify installed FastAPI and core wheels outside all source checkouts."""
import argparse
from pathlib import Path
import subprocess
import tempfile

PROBE = r"""
import importlib.metadata as metadata
import json
from pathlib import Path
import sys
from fastapi.testclient import TestClient
import gramlot
import gramlot_fastapi
from gramlot_fastapi import GramlotApplication
from gramlot_fastapi.runtime import RuntimeAssets

for name in ('gramlot', 'gramlot-fastapi'):
    dist = metadata.distribution(name)
    direct = json.loads(dist.read_text('direct_url.json') or '{}')
    assert not direct.get('dir_info', {}).get('editable'), f'{name} is editable'
for module in (gramlot, gramlot_fastapi):
    assert Path(module.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
root = Path.cwd()
(root / 'pages').mkdir()
(root / 'pages' / 'hello.py').write_text('''from gramlot.page import WebPage
class Page(WebPage):
    title = "Installed preview"
    def main(self, root):
        root.h1("Installed FastAPI preview")
''')
app = GramlotApplication(root, prefix='/nested/ui')
runtime = RuntimeAssets('/nested/ui')
assert runtime.browser_manifest, 'Prebuilt browser manifest is required'
with TestClient(app) as client:
    page = client.get('/nested/ui/hello/')
    assert page.status_code == 200
    recipe = client.get('/nested/ui/hello/recipe')
    assert recipe.status_code == 200 and 'Installed FastAPI preview' in recipe.text
    for path in [runtime.entry_url, *runtime.import_map().values()]:
        response = client.get(path)
        assert response.status_code == 200, path
        assert 'immutable' in response.headers.get('cache-control', ''), path
    assert client.get('/nested/ui/missing/').status_code == 404
assert not any(name == 'gnr' or name.startswith('gnr.') for name in sys.modules)
print('Installed page, recipe and prebuilt runtime passed; plain host needs no Genropy.')
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python', required=True)
    args = parser.parse_args()
    python = str(Path(args.python).absolute())
    with tempfile.TemporaryDirectory(prefix='gramlot-fastapi-consumer-') as directory:
        subprocess.run([python, '-I', '-c', PROBE], cwd=directory, check=True)
        subprocess.run([python, '-I', '-m', 'gramlot_fastapi', '--help'],
                       cwd=directory, check=True, stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    main()
