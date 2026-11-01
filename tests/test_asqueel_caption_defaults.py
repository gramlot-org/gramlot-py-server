"""Model caption defaults and explicit overrides over actual Asqueel queries."""
from contextlib import contextmanager

import pytest
from asqueel import AsqueelDb, SqlDatabaseConfig
from gramlot_py_server.db.asqueel import AsqueelSelect


@contextmanager
def caption_database(caption_field=None):
    config = SqlDatabaseConfig()
    db = config.source.db('captions', implementation='sqlite')
    db.connection('main', database=':memory:')
    table = db.packages().package('demo', sqlschema='main', sqlprefix=False).table(
        'customer', pkey='id', caption_field=caption_field, rowcaption='$code')
    table.column('id', dtype='L')
    table.column('name', dtype='T', name_long='Customer')
    table.column('code', dtype='T', name_long='Code')
    table.formulaColumn('display', sql_formula="$name || ' (' || $code || ')'", dtype='T')
    shared = AsqueelDb(config)
    try:
        with shared.session() as session:
            session.execute('CREATE TABLE customer (id INTEGER PRIMARY KEY, name TEXT, code TEXT)').close()
            session.table('demo.customer').sql_insert([
                {'id':0, 'name':'Zoe', 'code':'A01'},
                {'id':1, 'name':'Ada', 'code':'Z02'}])
            session.commit()
        yield shared
    finally:
        shared.close()


def test_model_caption_controls_search_lookup_order_and_auxiliary_metadata():
    with caption_database('name') as shared:
        provider = AsqueelSelect(shared).register('customers','demo.customer',identifier='id')
        result = provider.select(dbtable='customers', _querystring='', auxColumns='code')
        assert result['caption'] == 'name'
        assert result['columns'] == ['name','code']
        assert result['headers'] == ['Customer','Code']
        assert [row['id'] for row in result['rows']] == [1,0]
        assert provider.select(dbtable='customers', _id=0)['rows'] == [{'id':0,'name':'Zoe'}]
        assert provider.select(dbtable='customers', _querystring='Zoe')['rows'] == [{'id':0,'name':'Zoe'}]
        assert provider.select(dbtable='customers', _querystring='A01')['rows'] == []


@pytest.mark.parametrize('model_caption', ['name', None, 'missing'])
def test_explicit_caption_wins_even_without_a_usable_model_default(model_caption):
    with caption_database(model_caption) as shared:
        provider = AsqueelSelect(shared).register('customers','demo.customer',identifier='id',caption='code')
        result = provider.select(dbtable='customers', _querystring='A01')
        assert result == {'rows':[{'id':0,'code':'A01'}], 'identifier':'id', 'caption':'code'}
        assert provider.select(dbtable='customers', _id=0)['rows'] == result['rows']


def test_model_formula_caption_and_explicit_search_remain_independent():
    with caption_database('display') as shared:
        provider = AsqueelSelect(shared).register('customers','demo.customer',identifier='id',search=('code',))
        assert provider.select(dbtable='customers', _querystring='A01')['rows'] == [{'id':0,'display':'Zoe (A01)'}]
        assert provider.select(dbtable='customers', _querystring='Zoe')['rows'] == []


def test_missing_caption_is_a_configuration_error_not_a_rowcaption_fallback():
    with caption_database() as shared:
        provider = AsqueelSelect(shared)
        with pytest.raises(ValueError, match='requires caption or model caption_field'):
            provider.register('customers','demo.customer',identifier='id')
        assert provider.tables == {}


@pytest.mark.parametrize('caption', ['', False, 'missing'])
def test_invalid_explicit_caption_does_not_fall_back_to_model(caption):
    with caption_database('name') as shared:
        with pytest.raises(ValueError):
            AsqueelSelect(shared).register('customers','demo.customer',identifier='id',caption=caption)


def test_invalid_model_caption_is_rejected():
    with caption_database('missing') as shared:
        with pytest.raises(ValueError, match='Unknown registered field: missing'):
            AsqueelSelect(shared).register('customers','demo.customer',identifier='id')
