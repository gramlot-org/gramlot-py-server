"""Serve the read-only Invoice Application gallery through Kajenn/Asqueel."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from importlib.resources import files
from gramlot_py_server.gallery import stage, subclass_module
from gramlot_py_server.kajenn import serve


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=61404)
    args = parser.parse_args()
    examples = Path(str(files('gramlot_examples')))
    catalogs = [(examples/'application/catalog.json',examples/'application/pages')]
    with TemporaryDirectory(prefix='gramlot-application-') as directory:
        folder = Path(directory)
        assets = stage(folder,catalogs,'')
        listed = [(str(a),str(b)) for a,b in catalogs]
        (folder/'index.py').write_text(subclass_module(examples/'application/gallery_page.py',
            'invoice_gallery_index',f'    catalogs = {listed!r}\n'))
        (folder/'pages/00-index.py').write_text(subclass_module(examples/'application/overview.py',
            'invoice_overview','    pass\n'))
        page = folder/'pages/invoice/01-customers.py'
        page.write_text(page.read_text()+'\nfrom gramlot_py_server.gallery.application.test_invoice_pg.invoice_service import database\nPage.database = database\n')
        print(f'Application gallery · Invoice: http://127.0.0.1:{args.port}/',flush=True)
        serve(folder,host='127.0.0.1',port=args.port,assets=assets)


if __name__=='__main__':
    main()
