"""Run local chart integration checks: python -m gramlot_py_server.gallery.base.chart_reports."""
import argparse
import json
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

from gramlot_py_server.gallery.base import sales_charts
from gramlot_py_server.gallery.base.sales_geography import SalesGeography
from gramlot_py_server.gallery.base.service import create_database
from gramlot_py_server.uvicorn import serve



def stage_gallery(folder, *, prefix=""):
    """Stage the original reports with the ordinary gallery lesson wrapper."""
    from gramlot_py_server.gallery import stage

    examples = Path(str(files('gramlot_examples')))
    catalogs = [(examples / 'base/chart-reports-catalog.json', examples / 'base/pages')]
    assets = stage(folder, catalogs, prefix)
    report_folder = folder / 'pages/85-chart-reports'
    links = [(prefix + '/pages/85-chart-reports/' + name, label)
             for name, label in [('sales', 'Live Australian sales'), ('attributes', 'Attributes fixture'),
                                 ('values', 'Values fixture'), ('streaming', 'Streaming sine waves')]]
    for name in ('sales', 'attributes', 'values'):
        with (report_folder / f'{name}.py').open('a') as stream:
            stream.write(f"\nPage.report_links = {links!r}\n")
    for name in ('sales', 'australian_timeline'):
        with (report_folder / f'{name}.py').open('a') as stream:
            stream.write("\nfrom gramlot_py_server.gallery.base.sales_charts import report_provider, report_geojson\n"
                         "Page.provider = report_provider\nPage.geojson = report_geojson\n")
    with (report_folder / 'australian_geography.py').open('a') as stream:
        stream.write("\nfrom gramlot_py_server.gallery.base.sales_charts import geography_provider\n"
                     "Page.provider = geography_provider\nPage.geojson = geography_provider.states\n")
    return assets


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geojson',type=Path,required=True,help='Australian territory GeoJSON; properties.name must match state names')
    parser.add_argument('--localities',type=Path,help='Directory of ABS SAL 2021 GeoJSON files by State')
    parser.add_argument('--port',type=int,default=8901)
    parser.add_argument('--gallery', action='store_true', help='Open all original reports with gallery navigation, explanation and code')
    args=parser.parse_args()
    if args.gallery and not args.localities:
        parser.error('--gallery requires --localities for the state-to-suburb example')
    sales_charts.report_provider=sales_charts.SalesCharts(create_database('asqueel').database)
    sales_charts.report_geojson=json.loads(args.geojson.read_text())
    if args.localities:
        sales_charts.geography_provider=SalesGeography(sales_charts.report_provider.database,sales_charts.report_geojson,args.localities)
    pages=files('gramlot_examples').joinpath('base/pages/85-chart-reports')
    with TemporaryDirectory(prefix='gramlot-chart-reports-') as folder:
        if args.gallery:
            assets = stage_gallery(Path(folder))
            serve(folder, host='127.0.0.1', port=args.port, assets=assets)
            return
        for name in ('index','attributes','values','streaming','australian_timeline') + (('australian_geography',) if args.localities else ()):
            path=Path(folder)/f'{name}.py'
            path.write_text(pages.joinpath('sales.py' if name == 'index' else f'{name}.py').read_text())
            if name in ('index','australian_timeline'):
                with path.open('a') as stream:
                    stream.write('\nfrom gramlot_py_server.gallery.base.sales_charts import report_provider, report_geojson\nPage.provider = report_provider\nPage.geojson = report_geojson\n')
            if name=='australian_geography':
                with path.open('a') as stream:
                    stream.write('\nfrom gramlot_py_server.gallery.base.sales_charts import geography_provider\nPage.provider = geography_provider\nPage.geojson = geography_provider.states\n')
        (Path(folder)/'streaming.js').write_text(pages.joinpath('streaming.js').read_text())
        serve(folder,host='127.0.0.1',port=args.port)


if __name__=='__main__':main()
