# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""FastAPI serves the shared showcase without owning its lesson declarations."""
import importlib.util
import json
from pathlib import Path

from fastapi.testclient import TestClient
from gramlot.showcase import get_showcase_directory


def create_showcase_app():
    path = Path(__file__).resolve().parents[1] / 'examples/showcase/serve.py'
    spec = importlib.util.spec_from_file_location('showcase_host', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.create_app()


def test_shared_showcase_pages_are_served_by_fastapi():
    app = create_showcase_app()
    assert app.gramlot_pages.directory == get_showcase_directory().resolve()
    assert len(app.gramlot_pages.pages) == 12
    with TestClient(app) as client:
        assert client.get('/', follow_redirects=False).headers['location'] == '/page/index/'
        for name in app.gramlot_pages.pages:
            document = client.get(f'/page/{name}/')
            assert document.status_code == 200, name
            assert client.get(f'/page/{name}/recipe').status_code == 200, name
            startup = document.text.split('id="startup">', 1)[1].split('</script>', 1)[0]
            inspection = json.loads(startup)['inspector']
            if name == 'index':
                assert inspection is False
            else:
                assert inspection['data_root'] == 'data_root'
                assert inspection['source_root'] == 'source_root'
