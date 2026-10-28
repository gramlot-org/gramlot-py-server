"""Serve the optional Kajenn/Asqueel gallery against a dedicated SQLite file."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from asqueel import AsqueelDb
from kajenn import AsgiServer
from kajenn.config.templates import DefaultConfiguration
from kajenn_db.asqueel import AsqueelDbHandler
from gramlot_examples.trials.kajenn_db import model
from gramlot_py_server.gallery import stage, environment_catalogs
from gramlot_py_server.kajenn import Application


TRIAL = Path(model.__file__).parent


def prepare_database(database):
    """Seed a new demo database once; an existing file is never reset or reseeded."""
    database = Path(database).resolve()
    source = model.customer_model(database)
    if not database.exists():
        database.parent.mkdir(parents=True, exist_ok=True)
        db = AsqueelDb(source)
        try:
            with db.session() as session:
                session.migrate()
                table = session.table('app.customer')
                for customer in model.CUSTOMERS:
                    table.insert(dict(customer))
                session.commit()
        finally:
            db.close()
    return source


def create_site(database, folder, *, mount_path='/py'):
    source = prepare_database(database)
    catalogs = environment_catalogs('kajenn') + [(TRIAL / 'catalog.json', TRIAL / 'pages')]
    assets = stage(Path(folder), catalogs, mount_path)
    class Site(DefaultConfiguration):
        def applications_section(self, cfg):
            cfg.databases(handler_class=AsqueelDbHandler).database(code='default', source=source)
            cfg.applications().application(
                code='pages', mount=mount_path.strip('/'), app_class=Application,
                pages=folder, assets=assets, websocket=True,
            ).request(body='raw')
    return AsgiServer(config=Site)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True, help='dedicated demonstration SQLite file')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8768)
    options = parser.parse_args()
    with TemporaryDirectory(prefix='gramlot-kajenn-db-gallery-') as folder:
        server = create_site(options.database, folder)
        print(f'Kajenn/Asqueel gallery: http://{options.host}:{options.port}/py/', flush=True)
        print(f'SQLite: {options.database.resolve()} (existing records are preserved)', flush=True)
        server.serve(host=options.host, port=options.port)


if __name__ == '__main__':
    main()
