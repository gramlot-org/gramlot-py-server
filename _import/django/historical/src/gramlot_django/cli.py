# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Local demonstration launcher using Django's standard development server."""
import argparse
from contextlib import closing
import os
import importlib.util
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path
import threading
import webbrowser


def port_number(value):
    port = int(value)
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError('Port must be between 1 and 65535')
    return port


def restore_bakery(archive_path, database):
    """Restore into a new file; never replace an existing demonstration database."""
    if database.exists():
        return
    handle, temporary = tempfile.mkstemp(prefix='bakery-', suffix='.sqlite3', dir=database.parent)
    os.close(handle)
    try:
        with zipfile.ZipFile(archive_path) as archive, closing(sqlite3.connect(temporary)) as connection:
            connection.executescript(archive.read('bakerydemo.sql').decode('utf-8'))
            if connection.execute('PRAGMA quick_check').fetchone() != ('ok',):
                raise RuntimeError('The Bakery database failed its integrity check')
        try:
            os.link(temporary, database)
        except FileExistsError:
            pass
    finally:
        Path(temporary).unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(prog='gramlot-django')
    commands = parser.add_subparsers(dest='command', required=True)
    demo = commands.add_parser('demo', help='Start a local demonstration')
    demo.add_argument('name', nargs='?', choices=['polls', 'bakery'], default='polls')
    demo.add_argument('--port', type=port_number)
    demo.add_argument('--data-dir', type=Path, help='Directory for persistent demo data')
    demo.add_argument('--open', action='store_true', help='Open the demo in a browser')
    demo.add_argument('--project-dir', type=Path, help='Path to the adapted Bakery project')
    args = parser.parse_args(argv)
    args.port = args.port or (8063 if args.name == 'bakery' else 8064)
    if args.name == 'polls' and args.project_dir:
        parser.error('--project-dir applies only to Bakery')
    if args.name == 'bakery':
        project = (args.project_dir or Path(__file__).resolve().parents[2] / 'examples/bakerydemo').resolve()
        if not (project / 'bakerydemo/settings/gramlot.py').is_file() or not (project / 'bakerydemo.sql.zip').is_file():
            parser.error('Provide --project-dir pointing to the adapted examples/bakerydemo project')
        if importlib.util.find_spec('wagtail') is None:
            parser.error('Install the Bakery project requirements/local.txt in this environment first')
    args.data_dir = args.data_dir or Path.home() / '.gramlot-django' / args.name
    directory = args.data_dir.expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    if args.name == 'bakery':
        database = directory / 'bakery.sqlite3'
        restore_bakery(project / 'bakerydemo.sql.zip', database)
        sys.path.insert(0, str(project))
        os.environ['GRAMLOT_BAKERY_DB'] = str(database)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'bakerydemo.settings.gramlot'
    else:
        database = directory / 'polls.sqlite3'
        os.environ['GRAMLOT_POLLS_DATA_DIR'] = str(directory)
        os.environ['DJANGO_SETTINGS_MODULE'] = 'gramlot_django.demo.settings'
    import django
    django.setup()
    from django.core.management import call_command
    call_command('migrate', interactive=False, verbosity=0)
    if args.name == 'polls':
        from gramlot_django.demo.seed import seed
        seed()
    url = f'http://127.0.0.1:{args.port}/' + ('polls/' if args.name == 'polls' else '')
    print(f'{args.name.title()} demo: {url}\nDatabase: {database}', flush=True)
    if args.open:
        timer = threading.Timer(1, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    call_command('runserver', f'127.0.0.1:{args.port}', use_reloader=False)


if __name__ == '__main__':
    main()
