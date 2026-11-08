"""The original reports remain usable through the ordinary gallery wrapper."""
import json
from pathlib import Path
from types import SimpleNamespace
from gramlot.server import GramlotFileServer
from gramlot_examples import build_gallery
from gramlot_examples.base.chart_report import FixtureChartReport, fixture_geography
from gramlot_py_server.gallery.base import chart_reports, sales_charts


def test_chart_gallery_preserves_reports_and_companions(tmp_path, monkeypatch):
    provider = FixtureChartReport('attributes')
    geometry = fixture_geography()
    monkeypatch.setattr(sales_charts, 'report_provider', provider, raising=False)
    monkeypatch.setattr(sales_charts, 'report_geojson', geometry, raising=False)
    monkeypatch.setattr(sales_charts, 'geography_provider', SimpleNamespace(states=geometry), raising=False)
    assets = chart_reports.stage_gallery(tmp_path)
    server = GramlotFileServer(tmp_path)
    for name in ('sales', 'australian_timeline', 'australian_geography', 'attributes', 'values', 'time_snapshots'):
        cls = server.resolve_page('pages/85-chart-reports/' + name)
        page = cls()
        builder = page.source_builder('main')
        server._load_collections(builder, server.page_collections(cls))
        page.main(builder.root)
        assert builder.to_tytx()
    sales = server.resolve_page('pages/85-chart-reports/sales')
    assert sales.provider is provider
    assert sales.report_links[0][0] == '/pages/85-chart-reports/sales'
    root = Path(chart_reports.files('gramlot_examples'))
    gallery = build_gallery([(root / 'base/chart-reports-catalog.json', root / 'base/pages')])
    for i in (1, 2, 3, 5, 6, 7):
        route = gallery['routes'][f'chart-reports-{i:02}']
        assert route['page'].exists()
    assert (root / 'base/pages/85-chart-reports/00-index.md').exists()
