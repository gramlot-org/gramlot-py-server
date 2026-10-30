"""Local release preview: standard, Base, PageStore and Kajenn database catalogues."""
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import json
import sys

from serve_kajenn_db_gallery import prepare_database
from gramlot_py_server.gallery.modules import stage_module

from kajenn import AsgiServer
from kajenn.config.templates import DefaultConfiguration
from kajenn_db.asqueel import AsqueelDbHandler
from gramlot_py_server.gallery import stage
from gramlot_py_server.gallery.base import service
from gramlot_py_server.gallery.base.selection_trial import SelectionTrialApplication

EXAMPLES = Path(str(files('gramlot_examples')))


def prepare_gallery(root, database, modules=None, *, selection_trials=False, cached_trial=False, cached_threshold=1000):
    service.database = service.create_database('asqueel')
    demo_source = prepare_database(database)
    catalogs = [(EXAMPLES / 'base' / name, EXAMPLES / 'base/pages')
                for name in ('catalog.json', 'asqueel-catalog.json')]
    if selection_trials:
        catalogs.append((EXAMPLES / 'base/selection-trial-catalog.json', EXAMPLES / 'base/pages'))
    if cached_trial:
        catalogs.append((EXAMPLES / 'base/cached-trial-catalog.json', EXAMPLES / 'base/pages'))
    catalogs += [(EXAMPLES / 'trials' / name / 'catalog.json', EXAMPLES / 'trials' / name / 'pages')
                 for name in ('page_store', 'kajenn_db', 'chat_base')]
    registrations = []
    if modules is not None:
        modules = Path(modules).resolve()
        sys.path.insert(0, str(modules))
        module = modules / 'mobile_application'
        catalog = json.loads((module / 'catalog.json').read_text())
        registrations.append(dict(catalog=catalog, mount='/mobile-application',
                                  integration='/mobile-application/device-provider.js', prerequisites=[]))
    assets = stage(root, catalogs, '', remote_edit=False, modules=registrations)
    if modules is not None:
        resources = stage_module(root / 'mobile-application', pages=module / 'pages',
                                 assets=module / 'assets', catalog_file=module / 'catalog.json',
                                 prefix='/mobile-application', frame_script_url='/gallery/dist/frame.js')
        assets.update({'/mobile-application' + path: resource for path, resource in resources.items()})
    with (root / 'index.py').open('a') as stream:
        stream.write("    title = 'Gramlot release preview'\n")
    dependencies = ['80-database/01-customers', '81-asqueel/01-state_customers', '82-grid-database/01-customers', '82-grid-database/02-invoice_rows']
    if selection_trials:
        dependencies.append('83-selection-trials/02-jsonl')
    for path in dependencies:
        with (root / f'pages/{path}.py').open('a') as stream:
            stream.write('\nfrom gramlot_py_server.gallery.base.service import database\nPage.database = database\n')
    if cached_trial:
        from gramlot_py_server.gallery.base.cached_trial import create_database
        import atexit
        service.cached_database = create_database()
        atexit.register(service.cached_database.close)
        with (root / 'pages/84-cached-selection/01-invoice_rows.py').open('a') as stream:
            stream.write('\nfrom gramlot_py_server.gallery.base.service import cached_database\nPageStore.database = cached_database\n')
            stream.write(f'PageStore.cache_threshold = {cached_threshold!r}\n')
    return assets, demo_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--modules', type=Path, help='Parent of the prepared public mobile_application module')
    parser.add_argument('--selection-trials', action='store_true', help='Enable the JSONL loading/timing lesson')
    parser.add_argument('--cached-trial', action='store_true', help='Enable the Asqueel-only cachedFetch experiment (cache schema must be prepared)')
    parser.add_argument('--cached-threshold', type=int, default=1000)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=61505)
    options = parser.parse_args()
    if options.cached_threshold < 1:
        parser.error("cached threshold must be positive")
    with TemporaryDirectory(prefix='gramlot-release-gallery-') as directory:
        root = Path(directory)
        assets, demo_source = prepare_gallery(root, options.database, options.modules, selection_trials=options.selection_trials, cached_trial=options.cached_trial, cached_threshold=options.cached_threshold)

        class Site(DefaultConfiguration):
            def applications_section(self, cfg):
                cfg.databases(handler_class=AsqueelDbHandler).database(code='default', source=demo_source)
                cfg.applications().application(code='pages', mount='', app_class=SelectionTrialApplication,
                    pages=root, assets=assets, websocket=True).request(body='raw')

        print(f'Release gallery: http://{options.host}:{options.port}/ (Remote Edit disabled; Invoice excluded)', flush=True)
        print('Native gallery modules require a same-origin HTTPS frontend.', flush=True)
        AsgiServer(config=Site).serve(host=options.host, port=options.port)


if __name__ == '__main__':
    main()
