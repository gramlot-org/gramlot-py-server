"""The common preview keeps existing catalogues while mounting optional mobile pages."""
import importlib.util
import json
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from serve_release_gallery import prepare_gallery


@pytest.mark.parametrize("selection_trials,cached_trial", [(False,False),(True,False),(True,True)])
def test_release_preview_mounts_mobile_without_private_pages(tmp_path, monkeypatch, selection_trials, cached_trial):
    monkeypatch.setattr(sys, 'path', list(sys.path))
    module = tmp_path / 'modules/mobile_application'
    pages = module / 'pages'
    pages.mkdir(parents=True)
    assets = module / 'assets'
    assets.mkdir()
    catalog = dict(id='mobileApplication', title='Mobile application', visibility='native', entries=[
        dict(id='app', title='App information', path='app', capabilities=['appinfo'], requires=[]),
        dict(id='push', title='Server push', path='push', capabilities=['push'], requires=['pushRegistration'])])
    (module / 'catalog.json').write_text(json.dumps(catalog))
    for name in ('app', 'push'):
        (pages / f'{name}.py').write_text('from gramlot import Page as BasePage\nclass Page(BasePage):\n    def main(self,root): root.p("Mobile")\n')
    (pages / 'app.js').write_text('export class Logic {}')
    (pages / 'index.css').write_text('')
    for name in ('device-provider.js', 'barcode-test.png', 'barcode-test-code128.png'):
        (assets / name).write_bytes(b'public fixture')
    (assets / 'private.p8').write_text('private fixture')
    root = tmp_path / 'site'
    root.mkdir()
    resources, _ = prepare_gallery(root, tmp_path / 'customers.sqlite', module.parent, selection_trials=selection_trials, cached_trial=cached_trial, cached_threshold=1200)
    assert '/mobile-application/device-provider.js' in resources
    assert '/mobile-application/private.p8' not in resources
    assert (root / 'mobile-application/app.py').exists()
    assert not (root / 'mobile-application/push.py').exists()
    for path in ('80-database/01-customers', '81-asqueel/01-state_customers', '82-grid-database/01-customers', '82-grid-database/02-invoice_rows', '92-chat/01-echo'):
        assert (root / f'pages/{path}.py').exists()
    assert (root / 'pages/83-selection-trials/02-jsonl.py').exists() is selection_trials
    for path in ('01-json', '03-websocket-rpc'):
        assert not (root / f'pages/83-selection-trials/{path}.py').exists()
    for page in ('01-customers', '02-invoice_rows'):
        assert 'Page.database = database' in (root / f'pages/82-grid-database/{page}.py').read_text()
    spec = importlib.util.spec_from_file_location('release_index', root / 'index.py')
    page = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(page)
    assert page.Page.gallery_modules[0]['catalog'] == catalog
    assert page.Page.gallery_modules[0]['prerequisites'] == []
    assert 'remote_edit = False' in (root / '.gallery-tools/07-tools/index.py').read_text()
    assert not list((root / 'pages').glob('*invoice*'))

    cached_page = root / 'pages/84-cached-selection/01-invoice_rows.py'
    assert cached_page.exists() is cached_trial
    if cached_trial:
        assert 'PageStore.database = cached_database' in cached_page.read_text()
        assert 'PageStore.cache_threshold = 1200' in cached_page.read_text()
