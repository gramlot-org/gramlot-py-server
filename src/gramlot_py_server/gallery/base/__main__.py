"""Run the Base gallery against a dedicated PostgreSQL copy."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from importlib.resources import files
from gramlot_py_server.gallery import stage
from . import service
from .copy_dataset import BACKENDS


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=BACKENDS, required=True)
    parser.add_argument('--port', type=int, default=61401)
    args=parser.parse_args()
    if args.backend=='django':
        service.configure_django()
    service.database=service.create_database(args.backend)
    examples=Path(str(files('gramlot_examples')))
    catalogs=[(examples/'base/catalog.json',examples/'base/pages')]
    if args.backend == 'asqueel':
        catalogs.append((examples/'base/asqueel-catalog.json', examples/'base/pages'))
    with TemporaryDirectory(prefix='gramlot-base-') as directory:
        folder=Path(directory)
        assets=stage(folder,catalogs,'')
        index=folder/'index.py'
        index.write_text(index.read_text()+"    title = 'Base gallery'\n")
        page=folder/'pages/80-database/01-customers.py'
        page.write_text(page.read_text()+"\nfrom gramlot_py_server.gallery.base.service import database\nPage.database = database\n")
        if args.backend == 'asqueel':
            for path in ('81-asqueel/01-state_customers', '82-grid-database/01-customers', '82-grid-database/02-invoice_rows'):
                dependent = folder/f'pages/{path}.py'
                dependent.write_text(dependent.read_text()+"\nfrom gramlot_py_server.gallery.base.service import database\nPage.database = database\n")
        if args.backend != 'asqueel':
            page.write_text(page.read_text()+"\nPage.selector_parameters = {'auxColumns': 'state_name', 'selected_state_name': '.state_name'}\n")
        if args.backend=='django':
            from django.conf import settings
            from django.core.management import call_command
            from gramlot_py_server.django import Pages, _URLconf
            settings.ROOT_URLCONF=_URLconf(Pages(folder,assets=assets).urlpatterns)
            print(f'Base gallery · Django: http://127.0.0.1:{args.port}/',flush=True)
            call_command('runserver',f'127.0.0.1:{args.port}',use_reloader=False)
        else:
            if args.backend=='asqueel':
                from .selection_trial import serve
            else:
                from gramlot_py_server.uvicorn import serve
            print(f'Base gallery · {args.backend}: http://127.0.0.1:{args.port}/',flush=True)
            serve(folder,host='127.0.0.1',port=args.port,assets=assets)


if __name__=='__main__':
    main()
