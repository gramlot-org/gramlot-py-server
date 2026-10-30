"""Read-only invoice data with cache writes confined to the prepared trial schema."""
import importlib.util
import os

import pytest
from pathlib import Path

import gramlot_examples
from gramlot_py_server.gallery.base.cached_trial import create_database


def page_module():
    path=Path(gramlot_examples.__file__).parent/'base/pages/84-cached-selection/01-invoice_rows.py'
    spec=importlib.util.spec_from_file_location('cached_trial_page',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(os.environ.get("GRAMLOT_CACHED_TRIAL_DB") != "1", reason="requires the explicitly prepared local XL cache database")
def test_cached_trial_resident_windows_server_criteria_and_cleanup():
    module=page_module();database=create_database();store=module.PageStore();store.database=database;store.start()
    def request(limit='500000',seed='',sorted_by='',start=0,count=200,refresh=False):
        store.publish('selection_request',dict(request_id='test',limit=limit,seed=seed,sorted_by=sorted_by,start=start,count=count,refresh=refresh))
        result=store.data['selection_window']
        assert not result['error'],result['error']
        return result
    try:
        for limit in ('500','1000'):
            result=request(limit=limit)
            assert result['mode']=='resident' and len(result['rows'])==int(limit)
            with database.session() as session:
                assert session.table('_asql_._asql_cached_fetch').query(where='$owner=:owner',owner=store._owner).count()==0
        result=request()
        assert result['mode']=='cachedFetch' and result['window']['total']==410429
        assert len(result['rows'])==200
        first_ids=[row.attr['id'] for row in result['rows'].nodes]
        with database.session() as session:
            expected=session.table('invc.invoice_row').query(columns='$id',order_by='$id',limit=200).fetch()
            assert first_ids==[row['id'] for row in expected]
        last=request(start=410400)
        assert last['window']['start']==410229 and len(last['rows'])==200
        result=request(seed='Parks',sorted_by='quantity:d,unit_price:a')
        assert 0<result['window']['total']<410429
        rows=[row.attr for row in result['rows'].nodes]
        assert all('parks' in ' '.join(value for value in row.values() if isinstance(value,str)).casefold() for row in rows)
        assert [(-row['quantity'],row['unit_price']) for row in rows]==sorted((-row['quantity'],row['unit_price']) for row in rows)
        assert result['window']['start']==0
        assert request()['window']['total']==410429
        assert request(limit='1000')['mode']=='resident'
        request()
        owner=store._owner
    finally:
        store.close()
        with database.session() as session:
            assert session.table('_asql_._asql_cached_fetch').query(where='$owner=:owner',owner=store._owner).count()==0
        database.close()


@pytest.mark.parametrize('order', ['id:x', 'missing:a', 'id:a,id:d', 'id:a;DROP TABLE x', 'id'])
def test_sort_protocol_rejects_unsupported_sql(order):
    with pytest.raises(ValueError):
        page_module().sort_criteria(order)


def test_threshold_uses_actual_count_and_is_configurable():
    from unittest.mock import Mock
    module = page_module()
    store = module.PageStore()
    store.start()
    try:
        session, table = Mock(), Mock()
        table.query.return_value.count.return_value = 1000
        table.query.return_value.fetch.return_value = []
        store._load_selection(session, table, '500000')
        table.query.return_value.fetch.assert_called_once_with()
        assert not store._cached
        table.reset_mock()
        table.query.return_value.count.return_value = 1001
        table.query.return_value.fetch.return_value = 1001
        store._load_selection(session, table, '500000')
        table.query.return_value.fetch.assert_called_once_with(destinationName=store._owner + ':rows')
        assert store._cached
        store._cached = False
        store.cache_threshold = 2000
        table.reset_mock()
        table.query.return_value.fetch.return_value = []
        store._load_selection(session, table, '500000')
        table.query.return_value.fetch.assert_called_once_with()
        assert not store._cached
    finally:
        store.close()
