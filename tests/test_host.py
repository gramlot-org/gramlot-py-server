import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from genro_asgi import BaseServer
from gramlot.transport import TYTX_MEDIA_TYPE, from_tytx, to_tytx
from gramlot_kajenn.application import GramlotApplication
from gramlot_kajenn.genropy import GenropyApplication

ROOT = Path(__file__).resolve().parents[1]


def client_for(app):
    server = BaseServer(applications=[app])
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=server), base_url='http://test')


async def rpc(client, page, method, params=None, role='data'):
    response = await client.post(f'/page/{page}/rpc/{role}/{method}',
                                content=to_tytx(params or {}, 'json'),
                                headers={'content-type': TYTX_MEDIA_TYPE})
    return response, from_tytx(response.text, transport='json')


@pytest.mark.asyncio
async def test_plain_source_rpc_and_assets():
    app = GramlotApplication(ROOT / 'examples/plain')
    async with client_for(app) as client:
        document = await client.get('/page/hello/')
        assert document.status_code == 200
        assert app.runtime.entry_url in document.text
        recipe = await client.get('/page/hello/recipe')
        assert recipe.status_code == 200
        assert 'textBox' in recipe.text or 'textbox' in recipe.text
        response, value = await rpc(client, 'hello', 'greet', {'name': 'Ada'})
        assert response.status_code == 200
        assert value == {'ok': True, 'result': 'Hello, Ada!'}
        asset = await client.get(app.runtime.entry_url)
        assert asset.status_code == 200
        assert 'immutable' in asset.headers['cache-control']
        assert (await client.get('/page/missing/')).status_code == 404
        assert (await client.get('/page/hello/rpc/data/greet')).status_code == 405
        response, _ = await rpc(client, 'hello', 'greet', role='source')
        assert response.status_code == 409
        response, _ = await rpc(client, 'hello', '__init__')
        assert response.status_code == 404
        response, _ = await rpc(client, 'hello', 'greet', {'name': []})
        assert response.status_code == 422
        response = await client.post('/page/hello/rpc/data/greet', json={})
        assert response.status_code == 415
        response = await client.post('/page/hello/rpc/data/greet', content='broken',
                                     headers={'content-type': TYTX_MEDIA_TYPE})
        assert response.status_code == 400
        escaped = await app.asset('/_runtime/' + '../' * 8 + 'etc/passwd')
        assert escaped.status_code == 404


class Database:
    def __init__(self):
        self.events = []
        self.local = threading.local()

    def mark(self, action):
        self.events.append((threading.get_ident(), action))

    def clearCurrentEnv(self):
        self.mark('clear')
        self.local.env = {}

    def updateEnv(self, **env):
        self.mark('env')
        self.local.env = env

    def closeConnection(self):
        self.mark('close')

    def read(self):
        self.mark('read')
        return dict(self.local.env)


PAGE = """from gramlot_kajenn.genropy import GenropyPage
from gramlot.page import endpoint
class Page(GenropyPage):
    def main(self, root):
        root.div('Legacy')
    @endpoint
    def read(self):
        return self.db.read()
    @endpoint
    def fail(self):
        self.db.read()
        raise ValueError('private database details')
    @endpoint
    async def invalid(self):
        return self.db.read()
"""


@pytest.mark.asyncio
async def test_legacy_cleanup_success_failure_and_async_guard(tmp_path):
    (tmp_path / 'pages').mkdir()
    (tmp_path / 'pages/legacy.py').write_text(PAGE)
    db = Database()
    app = GenropyApplication(tmp_path, genropy_application=SimpleNamespace(db=db))
    loop_thread = threading.get_ident()
    async with client_for(app) as client:
        response, result = await rpc(client, 'legacy', 'read')
        assert response.status_code == 200
        assert result['result'] == {'pagename': 'legacy', 'gramlot_method': 'read'}
        assert [e[1] for e in db.events] == ['clear', 'env', 'read', 'close', 'clear']
        assert len({e[0] for e in db.events}) == 1
        assert db.events[0][0] != loop_thread
        db.events.clear()
        response, result = await rpc(client, 'legacy', 'fail')
        assert response.status_code == 500
        assert 'private database details' not in response.text
        assert [e[1] for e in db.events][-2:] == ['close', 'clear']
        db.events.clear()
        response, _ = await rpc(client, 'legacy', 'invalid')
        assert response.status_code == 500
        assert not db.events
        replies = await asyncio.gather(*(rpc(client, 'legacy', 'read') for _ in range(8)))
        assert all(response.status_code == 200 for response, _ in replies)
        for thread in {e[0] for e in db.events}:
            sequence = [e[1] for e in db.events if e[0] == thread]
            assert sequence == ['clear', 'env', 'read', 'close', 'clear'] * (len(sequence) // 5)


@pytest.mark.asyncio
async def test_real_legacy_sqlite_when_available(tmp_path, monkeypatch):
    gnrapp = pytest.importorskip('gnr.app.gnrapp')
    from gnr.core.gnrbag import Bag
    config = tmp_path / 'gnr'
    config.mkdir()
    (config / 'environment.xml').write_text(
        f'<GenRoBag><environment/><instances><test path="{tmp_path}" instance_template="default"/></instances></GenRoBag>')
    (config / 'instanceconfig').mkdir()
    (config / 'instanceconfig/default.xml').write_text('<GenRoBag><packages/></GenRoBag>')
    monkeypatch.setenv('GENRO_GNRFOLDER', str(config))
    instance = tmp_path / 'test-instance'
    instance.mkdir()
    (instance / 'instanceconfig.xml').write_text('<GenRoBag/>')
    legacy = gnrapp.GnrApp('test-instance', custom_config=Bag({'packages': Bag()}),
                          db_attrs={'implementation': 'sqlite',
                                    'dbname': str(tmp_path / 'legacy.sqlite')})
    legacy.db.closeConnection()
    app = GenropyApplication(ROOT / 'examples/genropy', genropy_application=legacy)
    async with client_for(app) as client:
        response, value = await rpc(client, 'database', 'check_connection')
        assert response.status_code == 200
        assert value['result'] == 'Connected'
        assert (await client.get('/page/database/recipe')).status_code == 200
