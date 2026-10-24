"""The root manifest resource has the same HTTP contract in all adapters."""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import pytest
from conformance_checks import served

@pytest.mark.parametrize('framework',['uvicorn','flask','fastapi','django','kajenn'])
def test_root_manifest(tmp_path,framework):
    (tmp_path/'index.py').write_text('''from gramlot import Page as BasePage
class Page(BasePage):
    installable = True
    app_icon = '/icon.png'
    title = 'Root application'
    def main(self, root): root.p('Root')
    def manifest(self, *, base_url='./'):
        return {**super().manifest(base_url=base_url), 'description':'Custom manifest'}
''')
    (tmp_path/'child.py').write_text('from gramlot import Page\n')
    with served(framework,tmp_path,'/demo',None) as base:
        url=base+'/app.webmanifest'
        with urlopen(url) as response:
            assert response.headers.get_content_type()=='application/manifest+json'
            manifest=json.load(response)
        assert manifest['start_url']=='/demo/'
        assert manifest['description']=='Custom manifest'
        assert manifest['icons'][0]['src']=='/demo/icon.png'
        with urlopen(Request(url,method='HEAD')) as response:
            assert response.status==200
            assert response.read()==b''
        with pytest.raises(HTTPError) as error:urlopen(Request(url,method='POST'))
        assert error.value.code==405
        with pytest.raises(HTTPError) as error:urlopen(base+'/child/app.webmanifest')
        assert error.value.code==404
        with urlopen(base+'/') as response:
            assert b'href="/demo/app.webmanifest"' in response.read()
