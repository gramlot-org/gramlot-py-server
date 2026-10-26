"""Stage an independently owned Python module on the gallery's HTTPS origin."""
import json
from pathlib import Path
from gramlot_py_server.gallery import subclass_module, JAVASCRIPT


def stage_module(folder, *, pages, assets, prefix, frame_script_url, catalog_file, prerequisites=()):
    """Prepare launch wrappers; the host owns mount, TLS, session and prerequisites.

    The caller registers catalogue metadata separately with gallery.stage(modules=...).
    No provider bundle is imported by ordinary gallery visitors.
    """
    from gramlot_examples.gallery.modules import local_path
    local_path(prefix, absolute=True)
    local_path(frame_script_url, absolute=True)
    folder, pages, assets = Path(folder), Path(pages), Path(assets)
    folder.mkdir(parents=True, exist_ok=True)
    catalog_file = Path(catalog_file)
    catalog = json.loads(catalog_file.read_text(encoding='utf-8'))
    from gramlot_examples.gallery.modules import registered_modules
    registration = dict(catalog=catalog, mount=prefix,
                        integration=prefix + '/device-provider.js', prerequisites=prerequisites)
    available = {entry['id'] for entry in registered_modules([registration])[0]['entries']}
    resources = {'/catalog.json': {'file': catalog_file, 'type': 'application/json; charset=utf-8'}}
    index = ["from gramlot import Page as BasePage", "class Page(BasePage):",
             f"    title = {catalog['title']!r}",
             f"    css = ('/themes/gramlot-base/theme.css', {prefix + '/index.css'!r})",
             "    def main(self, root):", "        pane = root.main(class_='device-page')",
             f"        pane.h1({catalog['title']!r})",
             "        pane.p('Native examples require the Capacitor application.')",
             f"        root.script(src={frame_script_url!r}, data_appearance='mela')"]
    for entry in catalog['entries']:
        page = pages / (entry['path'] + '.py')
        if not page.is_file():
            raise FileNotFoundError(page)
        if entry['id'] not in available:
            explanations = {
                'pushRegistration': 'The public production push service is not configured.',
                'topLevelEntry': 'Native shortcut entry must run in the app, outside gallery frames.',
            }
            missing = ' '.join(explanations.get(item, 'The required site integration is not configured.') for item in entry['requires'] if item not in prerequisites)
            index.append(f"        pane.p({entry['title'] + ' — unavailable in this beta. ' + missing!r})")
            continue
        index.append(f"        pane.p().a({entry['title']!r}, href={prefix + '/' + entry['path']!r})")
        (folder / page.name).write_text(subclass_module(page, f'gallery_module_{page.stem}', (
            f'    css = ("/themes/gramlot-base/theme.css", {prefix + "/index.css"!r})\n'
            '    def main(self, root):\n'
            '        super().main(root)\n'
            f'        root.script(src={frame_script_url!r}, data_appearance="mela")\n'
        )), encoding='utf-8')
        logic = page.with_suffix('.js')
        if logic.is_file():
            (folder / f'{page.stem}_aux.js').write_text(
                f'export * from {repr(prefix + "/" + logic.name)};\n', encoding='utf-8')
    (folder / 'index.py').write_text('\n'.join(index) + '\n', encoding='utf-8')
    for file in pages.glob('*.js'):
        resources['/' + file.name] = {'file': file, 'type': JAVASCRIPT}
    resources['/index.css'] = {'file': pages / 'index.css', 'type': 'text/css; charset=utf-8'}
    # Only public integration code and synthetic scanner targets from the module.
    for name, kind in [('device-provider.js', JAVASCRIPT), ('barcode-test.png', 'image/png'),
                       ('barcode-test-code128.png', 'image/png')]:
        file = assets / name
        if not file.is_file():
            raise FileNotFoundError(file)
        resources['/' + name] = {'file': file, 'type': kind}
    return resources
