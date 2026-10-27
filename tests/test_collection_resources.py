"""Verified startup resources and page-specific bootstrap across all adapters."""
import re
from urllib.error import HTTPError
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

import pytest
from gramlot.collections.inputs import mygramlot as collection
from gramlot_py_server.base import Adapter, Request as HostRequest, stored
from conformance_checks import served


def pages(folder):
    (folder / 'index.py').write_text('from gramlot import Page as Base\nclass Page(Base):\n    def main(self, root): root.p("Plain")\n')
    (folder / 'input.py').write_text('from gramlot import Page as Base\nfrom gramlot.collections.inputs import mygramlot as collection\nclass Page(Base):\n    gramlots = [collection]\n    def main(self, root): root.textbox(value="^.name")\n')


def module_url(document):
    return re.search(r'"url":"([^"]+/assets/index.js)"', document).group(1)


@pytest.mark.parametrize('framework', ['uvicorn', 'django', 'flask', 'fastapi', 'kajenn'])
def test_verified_resources_through_every_adapter(tmp_path, framework):
    pages(tmp_path)
    with served(framework, tmp_path, '/demo', None) as base:
        with urlopen(base + '/') as response:
            assert '"collections":[]' in response.read().decode()
        with urlopen(base + '/input') as response:
            module = module_url(response.read().decode())
        origin = urlsplit(base)
        url = f'{origin.scheme}://{origin.netloc}{module}'
        with urlopen(url) as response:
            content = response.read()
            assert content == collection.verify()[collection.module]
            assert response.headers['Cache-Control'] == 'public, max-age=31536000, immutable'
            assert int(response.headers['Content-Length']) == len(content)
        with urlopen(Request(url, method='HEAD')) as response:
            assert response.read() == b''
            # Kajenn finalizes HEAD length from its empty body (upstream issue 77).
            assert int(response.headers['Content-Length']) == (0 if framework == 'kajenn' else len(content))
            assert response.headers['Cache-Control'].endswith('immutable')
        with pytest.raises(HTTPError) as error:
            urlopen(Request(url, method='POST'))
        assert error.value.code == 405
        with pytest.raises(HTTPError) as error:
            urlopen(url.replace(collection.build_id[7:], '0' * 64))
        assert error.value.code == 404


@pytest.mark.asyncio
async def test_registry_is_verified_once_and_reused(tmp_path, monkeypatch):
    pages(tmp_path)
    calls = []
    original = type(collection).verify
    def counted(self):
        calls.append(self.name)
        return original(self)
    monkeypatch.setattr(type(collection), 'verify', counted)
    adapter = Adapter(tmp_path)
    assert calls == [collection.name]
    first = await adapter.gramlot_server.open_page('/input')
    # First use prepares and verifies the Python grammar; later openings reuse it.
    assert calls == [collection.name, collection.name]
    calls.clear()
    second = await adapter.gramlot_server.open_page('/input')
    assert first.page_id != second.page_id
    assert calls == []
    url = unquote(module_url(first.html))
    response = await adapter.handle(HostRequest('GET', url, stored(b'')))
    assert response.status == 200
    assert calls == []
    with pytest.raises(ValueError, match='reserved'):
        Adapter(tmp_path, assets={'/gramlot/collections/x': {'file': __file__, 'type': 'text/plain'}})
    adapter.shutdown()
