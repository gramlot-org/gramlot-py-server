import json
import re

import httpx
import pytest
from genro_tytx import from_tytx, to_tytx

from gramlot_py_server.uvicorn import Application
from lifespan_transport import LifespanTransport

PAGE = '''from gramlot import Page as BasePage, upload
from gramlot.server import UploadTarget
class Sink(UploadTarget):
    def __init__(self, fields, context):
        self.fields = fields
        self.context = context
        super().__init__(max_bytes=10)
        self.data = bytearray()
    def write(self, chunk): self.data.extend(chunk)
    def finish(self): return {"state": "completed", "result": {"content": self.data.decode(), "fields": self.fields, "context": self.context}}
    def abort(self): return {"state": "unsaved"}
    def status(self): return {"state": "pending"}
class Page(BasePage):
    def main(self, root): root.div('Upload')
    @upload
    def import_source(self, metadata): return Sink(metadata["fields"], metadata["context"])
'''


@pytest.mark.asyncio
async def test_stream_upload_and_reconcile_with_ownership_and_single_use(tmp_path):
    (tmp_path / 'index.py').write_text(PAGE)
    app = Application(tmp_path, mount_path='/py')
    transport = LifespanTransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        response = await client.get('/py/')
        match = re.search(r'await new PageBootstrap\((.+)\)\.run\(\);</script>', response.text)
        config = json.loads(match.group(1))['config']
        assert config['uploadUrl'] == '/py/gramlot/upload'
        assert 'upload' in config['capabilities']
        async def rpc(name, params):
            request = {'id':'id', 'pageId':config['pageId'], 'contentType':'upload', 'name':name, 'params':params}
            response = await client.post('/py/gramlot/rpc', content=to_tytx(request), headers={'content-type':'application/json'})
            return from_tytx(response.text)
        result = await rpc('prepare', {'operation':'import_source', 'metadata':{'name':'a.txt','size':2,'mediaType':'text/plain','context':{'recordId':'saved-123'},'fields':{'title':'Example','nested':{'rank':2}}}})
        grant = result['value']
        headers = {'content-type':'application/octet-stream', 'x-gramlot-page-id':config['pageId'],
                   'x-gramlot-transfer-id':grant['transferId'], 'x-gramlot-upload-token':grant['authorization']}
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as other:
            assert (await other.post(config['uploadUrl'], headers=headers, content=b'ok')).status_code == 403
        response = await client.post(config['uploadUrl'], headers=headers, content=b'ok')
        assert response.status_code == 200
        assert from_tytx(response.text) == {'state':'completed', 'result':{'content':'ok', 'context':{'recordId':'saved-123'}, 'fields':{'title':'Example','nested':{'rank':2}}}}
        assert (await client.post(config['uploadUrl'], headers=headers, content=b'ok')).status_code == 403
        assert (await rpc('status', {'transferId':grant['transferId']}))['value'] == {'state':'completed', 'result':{'content':'ok', 'context':{'recordId':'saved-123'}, 'fields':{'title':'Example','nested':{'rank':2}}}}


@pytest.mark.asyncio
async def test_upload_over_declared_size_fails_and_cleans_partial(tmp_path):
    (tmp_path / 'index.py').write_text(PAGE)
    app = Application(tmp_path)
    transport = LifespanTransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        document = await client.get('/')
        match = re.search(r'await new PageBootstrap\((.+)\)\.run\(\);</script>', document.text)
        config = json.loads(match.group(1))['config']
        async def rpc(name, params):
            req = {'id':'id', 'pageId':config['pageId'], 'contentType':'upload', 'name':name, 'params':params}
            response = await client.post('/gramlot/rpc', content=to_tytx(req), headers={'content-type':'application/json'})
            return from_tytx(response.text)
        grant = (await rpc('prepare', {'operation':'import_source', 'metadata':{'name':'a','size':2,'mediaType':'text/plain','context':{},'fields':{}}}))['value']
        headers = {'content-type':'application/octet-stream', 'x-gramlot-page-id':config['pageId'],
                   'x-gramlot-transfer-id':grant['transferId'], 'x-gramlot-upload-token':grant['authorization']}
        assert (await client.post('/gramlot/upload', headers=headers, content=b'oversize')).status_code == 400
        assert (await rpc('status', {'transferId':grant['transferId']}))['value'] == {'state':'unsaved'}


@pytest.mark.asyncio
async def test_trusted_identity_provider_is_called_for_control_and_binary_requests(tmp_path):
    (tmp_path / 'index.py').write_text('''from gramlot import Page as BasePage, endpoint, upload
from gramlot.server import UploadTarget
class Sink(UploadTarget):
    def __init__(self, identity):
        super().__init__(max_bytes=1)
        self.identity = identity
    def write(self, chunk): pass
    def finish(self): return {"state":"completed", "result":self.identity}
    def abort(self): return {"state":"unsaved"}
    def status(self): return {"state":"pending"}
class Page(BasePage):
    def main(self, root): root.div('Upload')
    @endpoint
    def who(self, identity): return {"trusted":self.request_identity, "client":identity}
    @upload
    def receive(self, metadata): return Sink(self.request_identity)
''')
    paths = []
    async def identity_provider(scope):
        paths.append(scope['path'])
        return scope['authenticated_identity']
    app = Application(tmp_path, identity_provider=identity_provider)
    async def trusted_middleware(scope, receive, send):
        if scope['type'] == 'http':
            scope = {**scope, 'authenticated_identity': 'alice'}
        await app(scope, receive, send)
    transport = LifespanTransport(app=trusted_middleware)
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        document = await client.get('/')
        config = json.loads(re.search(r'await new PageBootstrap\((.+)\)\.run\(\);</script>', document.text).group(1))['config']
        async def call(kind, name, params):
            request = {'id':'id', 'pageId':config['pageId'], 'contentType':kind, 'name':name, 'params':params}
            response = await client.post('/gramlot/rpc', content=to_tytx(request), headers={'content-type':'application/json'})
            return from_tytx(response.text)
        result = await call('data', 'who', {'identity':'forged'})
        assert result['value'] == {'trusted':'alice', 'client':'forged'}
        grant = (await call('upload', 'prepare', {'operation':'receive', 'metadata':{'name':'x','size':0,'mediaType':'','context':{},'fields':{}}}))['value']
        headers = {'content-type':'application/octet-stream', 'x-gramlot-page-id':config['pageId'],
                   'x-gramlot-transfer-id':grant['transferId'], 'x-gramlot-upload-token':grant['authorization']}
        response = await client.post('/gramlot/upload', headers=headers, content=b'')
        assert from_tytx(response.text) == {'state':'completed', 'result':'alice'}
        assert paths == ['/gramlot/rpc', '/gramlot/rpc', '/gramlot/upload']


@pytest.mark.asyncio
async def test_host_rechecks_current_identity_against_operation_rule_on_binary_admission(tmp_path):
    (tmp_path / 'index.py').write_text(PAGE.replace('@upload\n', '@upload(auth="editor")\n'))
    principal = {'identity': 'alice'}
    app = Application(tmp_path, identity_provider=lambda scope: principal['identity'])
    app.gramlot_server.evaluate_auth = lambda rule, *, owner, identity: None if rule is None or identity == 'alice' else 'not_authorized'
    transport = LifespanTransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        document = await client.get('/')
        config = json.loads(re.search(r'await new PageBootstrap\((.+)\)\.run\(\);</script>', document.text).group(1))['config']
        request = {'id':'id', 'pageId':config['pageId'], 'contentType':'upload', 'name':'prepare',
                   'params':{'operation':'import_source', 'metadata':{'name':'x','size':2,'mediaType':'','context':{},'fields':{}}}}
        grant = from_tytx((await client.post('/gramlot/rpc', content=to_tytx(request), headers={'content-type':'application/json'})).text)['value']
        headers = {'content-type':'application/octet-stream', 'x-gramlot-page-id':config['pageId'],
                   'x-gramlot-transfer-id':grant['transferId'], 'x-gramlot-upload-token':grant['authorization']}
        principal['identity'] = 'bob'
        assert (await client.post('/gramlot/upload', headers=headers, content=b'ok')).status_code == 403
        principal['identity'] = 'alice'
        assert (await client.post('/gramlot/upload', headers=headers, content=b'ok')).status_code == 200


@pytest.mark.asyncio
async def test_close_cleans_prepared_upload_after_checking_owner(tmp_path):
    (tmp_path / 'index.py').write_text(PAGE)
    app = Application(tmp_path)
    transport = LifespanTransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
        document = await client.get('/')
        config = json.loads(re.search(r'await new PageBootstrap\((.+)\)\.run\(\);</script>', document.text).group(1))['config']
        request = {'id':'id', 'pageId':config['pageId'], 'contentType':'upload', 'name':'prepare',
                   'params':{'operation':'import_source', 'metadata':{'name':'x','size':0,'mediaType':'','context':{},'fields':{}}}}
        grant = from_tytx((await client.post('/gramlot/rpc', content=to_tytx(request), headers={'content-type':'application/json'})).text)['value']
        record = app.gramlot_server._uploads._records[grant['transferId']]
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as other:
            await other.post('/gramlot/close', json={'pageId':config['pageId']})
            assert grant['transferId'] in app.gramlot_server._uploads._records
        await client.post('/gramlot/close', json={'pageId':config['pageId']})
        assert await record['transfer'].status() == {'state':'unsaved'}
        assert grant['transferId'] not in app.gramlot_server._uploads._records
