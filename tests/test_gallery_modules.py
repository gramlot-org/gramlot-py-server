"""Independent modules reuse the host launch and frame-theme lifecycle."""
from pathlib import Path
import importlib.util
import json
from gramlot_py_server.gallery.modules import stage_module


def test_module_wrappers_keep_companions_and_use_one_theme_payload(tmp_path):
    source = tmp_path / 'source'; source.mkdir()
    assets = tmp_path / 'assets'; assets.mkdir()
    (source / 'app.py').write_text('from gramlot import Page as BasePage\nclass Page(BasePage):\n    def main(self,root): root.p("App information")\n')
    (source / 'app.js').write_text('export {Logic} from "./index.js";')
    (source / 'index.js').write_text('export class Logic {}')
    (source / 'index.css').write_text('.device-page {color:var(--gramlot-ink)}')
    for name in ('device-provider.js','barcode-test.png','barcode-test-code128.png'):
        (assets / name).write_bytes(b'public fixture')
    (assets / 'private-key.p8').write_text('must not be staged')
    catalog = tmp_path / 'catalog.json'
    catalog.write_text(json.dumps(dict(id='mobile', title='Mobile application', visibility='native', entries=[
        dict(id='app', title='App', path='app', capabilities=['appinfo'], requires=[]),
        dict(id='push', title='Server push', path='push', capabilities=['push'], requires=['pushRegistration'])])))
    (source / 'push.py').write_text('raise RuntimeError("Unavailable page must not be imported")')
    target = tmp_path / 'mounted' 
    resources = stage_module(target,pages=source,assets=assets,prefix='/mobile-application',frame_script_url='/gallery/dist/frame.js',catalog_file=catalog)
    assert set(resources) == {'/catalog.json','/app.js','/index.js','/index.css','/device-provider.js','/barcode-test.png','/barcode-test-code128.png'}
    assert '/private-key.p8' not in resources
    assert (target / 'app_aux.js').read_text() == "export * from '/mobile-application/app.js';\n"
    spec = importlib.util.spec_from_file_location('module_test_app',target/'app.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    page=module.Page()
    assert page.css == ('/themes/gramlot-base/theme.css','/mobile-application/index.css')
    builder=page.source_builder('main');page.main(builder.root)
    scripts=[node for node in builder.source.nodes if node.node_tag=='script']
    assert len(scripts)==1
    assert scripts[0].attr['src']=='/gallery/dist/frame.js'
    assert scripts[0].attr['data_appearance']=='mela'

    assert not (target / 'push.py').exists()
    assert 'unavailable in this beta' in (target / 'index.py').read_text()
    assert resources['/catalog.json']['file'].read_bytes() == catalog.read_bytes()
