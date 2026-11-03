"""Original-source editing and fresh Python previews in a staged gallery."""
import importlib
import json
import os
import py_compile

import pytest
from gramlot.server import GramlotFileServer
from gramlot_py_server.gallery import stage, add_gallery


def fixture(tmp_path, remote_edit=True):
    original = tmp_path / "original"
    original.mkdir()
    family = original / "01-trial"
    family.mkdir()
    file = family / "01-page.py"
    file.write_text("from gramlot import Page as BasePage\nclass Page(BasePage):\n    title = 'Before'\n    def main(self, root): root.h1(self.title)\n")
    file.with_suffix('.js').write_text("export class Page {}\n")
    file.with_suffix('.md').write_text("# Trial\n")
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps(dict(environment="trial", families=[dict(
        key="trial", title="Trial", folder="01-trial", examples=[dict(
            key="trial-01", title="Trial", folder="01-page", description="Edit trial")])])) )
    staged = tmp_path / "staged"
    staged.mkdir()
    stage(staged, [(catalog, original)], "/py", remote_edit=remote_edit)
    server = GramlotFileServer(staged, reload=True)
    return file, server, server.resolve_page("index")(), staged / "pages/01-trial/01-page.py"


def test_save_original_and_reload_even_with_same_size_same_second_bytecode(tmp_path):
    file, server, gallery, wrapper = fixture(tmp_path)
    source = gallery.source_document("trial-01")
    assert source['writable'] is True
    assert server.resolve_page("pages/01-trial/01-page").title == 'Before'
    py_compile.compile(str(file), doraise=True)
    before_stat = file.stat()
    wrapper_before = wrapper.read_bytes()
    content = source['content'].replace('Before', 'After!')
    saved = gallery.gallery_source_save('trial-01', content, source['revision'])
    os.utime(file, ns=(before_stat.st_atime_ns, before_stat.st_mtime_ns))
    assert file.read_text() == content
    assert wrapper.read_bytes() == wrapper_before
    assert saved['revision'] != source['revision']
    assert server.resolve_page("pages/01-trial/01-page").title == 'After!'


def test_invalid_python_conflicts_and_unknown_targets_do_not_write(tmp_path):
    file, server, gallery, wrapper = fixture(tmp_path)
    source = gallery.source_document('trial-01')
    with pytest.raises(ValueError, match='Python syntax error at line'):
        gallery.gallery_source_save('trial-01', 'class Page(:\n', source['revision'])
    assert file.read_text() == source['content']
    assert server.resolve_page('pages/01-trial/01-page').title == 'Before'
    file.write_text(source['content'] + '# external change\n')
    with pytest.raises(ValueError, match='changed on disk'):
        gallery.gallery_source_save('trial-01', source['content'], source['revision'])
    assert file.read_text().endswith('# external change\n')
    with pytest.raises(ValueError, match='Unknown gallery entry'):
        gallery.gallery_source_save('../arbitrary.py', '', source['revision'])


def test_disabled_flag_rejects_save_on_server(tmp_path):
    file, _, gallery, _ = fixture(tmp_path, remote_edit=False)
    source = gallery.source_document('trial-01')
    assert source['writable'] is False
    with pytest.raises(PermissionError, match='disabled'):
        gallery.gallery_source_save('trial-01', '# changed', source['revision'])
    assert file.read_text() == source['content']


def test_gallery_flag_enables_source_saves_and_module_reload():
    import argparse
    received = {}
    def serve(pages, **kwargs):
        received.update(kwargs)
        gallery = GramlotFileServer(pages).resolve_page('index')
        assert gallery.remote_edit is True
    parser = argparse.ArgumentParser()
    add_gallery(parser.add_subparsers(), 'uvicorn', serve)
    options = parser.parse_args(['gallery', '--remote-edit'])
    assert options.run(options) == 0
    assert received['reload'] is True


@pytest.mark.parametrize('engine', ['uvicorn', 'flask', 'fastapi', 'django', 'kajenn'])
def test_all_adapters_forward_reload(engine, tmp_path):
    module = importlib.import_module('gramlot_py_server.' + engine)
    # Construction only: the same existing core option is forwarded by every adapter.
    if engine == 'kajenn':
        app = module.Application(tmp_path, reload=True, mount='')
        assert app.gramlot_server.reload is True
    else:
        app = module.Application(tmp_path, reload=True) if engine == 'uvicorn' else module.Pages(tmp_path, reload=True)
        assert app.gramlot_server.reload is True

@pytest.mark.parametrize('remote_edit', [False, True])
def test_gallery_save_rpc_respects_remote_edit(tmp_path, remote_edit):
    import re
    from http.cookiejar import CookieJar
    from urllib.request import HTTPCookieProcessor, Request, build_opener
    from genro_tytx import from_tytx
    from conformance_checks import served
    from rpc_checks import envelope

    file, _, gallery, wrapper = fixture(tmp_path, remote_edit=remote_edit)
    source = gallery.source_document('trial-01')
    with served('uvicorn', wrapper.parents[2], '/demo', None) as url:
        client = build_opener(HTTPCookieProcessor(CookieJar()))
        html = client.open(url + '/').read().decode()
        page_id = json.loads(re.search(r'new PageBootstrap\((.+)\)\.run', html)[1])['config']['pageId']
        params = dict(key='trial-01', content=source['content'].replace('Before', 'After!'), revision=source['revision'])
        request = Request(url + '/gramlot/rpc', data=envelope(page_id, 'gallery_source_save', params, 'data').encode(), headers={'Content-Type': 'application/json'})
        result = from_tytx(client.open(request).read().decode())
        if remote_edit:
            assert 'error' not in result
            assert "'After!'" in file.read_text()
        else:
            assert result['error']['name'] == 'PermissionError'
            assert "'Before'" in file.read_text()
