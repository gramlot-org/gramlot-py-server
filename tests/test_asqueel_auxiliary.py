"""On-demand Asqueel auxiliary projections over real isolated databases."""
import pytest
from gramlot_py_server.db.asqueel import AsqueelSelect


@pytest.fixture
def relation_provider(tmp_path):
    from asqueel import AsqueelDb, SqlDatabaseConfig
    recipe = SqlDatabaseConfig()
    db = recipe.source.db('relations', implementation='sqlite')
    db.connection('main', database=str(tmp_path/'relations.sqlite'))
    package = db.packages().package('demo', sqlschema='main', sqlprefix=False)
    country = package.table('country', pkey='code')
    country.column('code', dtype='T')
    country.column('name', dtype='T', name_long='Country')
    state = package.table('state', pkey='code')
    state.column('code', dtype='T')
    state.column('name', dtype='T', name_long='State')
    state.column('country', dtype='T').relation('demo.country.code')
    customer = package.table('customer', pkey='id')
    customer.column('id', dtype='L')
    customer.column('name', dtype='T', name_long='Customer')
    customer.column('state', dtype='T').relation('demo.state.code')
    customer.column('_state_name', dtype='T')
    shared = AsqueelDb(recipe)
    with shared.session() as session:
        for sql in (
            'CREATE TABLE country (code TEXT PRIMARY KEY, name TEXT)',
            'CREATE TABLE state (code TEXT PRIMARY KEY, name TEXT, country TEXT)',
            'CREATE TABLE customer (id INTEGER PRIMARY KEY, name TEXT, state TEXT, _state_name TEXT)',
            "INSERT INTO country VALUES ('AU','Australia')",
            "INSERT INTO state VALUES ('TAS','Tasmania','AU')",
            "INSERT INTO customer VALUES (1,'Alpha','TAS',NULL),(2,'Beta',NULL,NULL)"):
            session.execute(sql).close()
        session.commit()
    provider = AsqueelSelect(shared).register('customers', 'demo.customer',
        identifier='id', caption='name')
    yield provider, shared
    shared.close()


def test_direct_auxiliary_relations_search_lookup_nulls_and_metadata(relation_provider):
    provider, shared = relation_provider
    fields = '@state.name,@state.@country.name'
    result = provider.select(dbtable='customers', _querystring='', auxColumns=fields)
    assert result['columns'] == ['name','_state_name','_state__country_name']
    assert result['headers'] == ['Customer','State','Country']
    assert result['rows'] == [
        {'id':1,'name':'Alpha','_state_name':'Tasmania','_state__country_name':'Australia'},
        {'id':2,'name':'Beta','_state_name':None,'_state__country_name':None}]
    assert provider.select(dbtable='customers', _id=2, auxColumns=fields)['rows'] == [result['rows'][1]]
    assert provider.select(dbtable='customers', _querystring='lph', auxColumns=fields)['rows'] == [result['rows'][0]]
    assert not provider.select(dbtable='customers', _querystring='Tasmania', auxColumns=fields)['rows']
    assert provider.select(dbtable='customers', _querystring='none', auxColumns=fields)['headers'] == result['headers']
    # Returned native alias can be requested for template and selected-field output.
    assert provider.select(dbtable='customers', _id=1, auxColumns=fields, hiddenColumns='_state__country_name')['rows'][0]['_state__country_name'] == 'Australia'
    with shared.session() as session:
        assert session.table('demo.customer').column('state_name') is None


@pytest.mark.parametrize('field', ['@state.name AS hacked', '@state.name; DROP TABLE state', 'COUNT(*)'])
def test_auxiliary_sql_expressions_are_refused(relation_provider, field):
    provider, _ = relation_provider
    with pytest.raises(ValueError, match='model fields or relation paths'):
        provider.select(dbtable='customers', _querystring='', auxColumns=field)


@pytest.mark.parametrize('field', ['missing', '@missing.name', '@state.missing', '@state.@country.missing'])
def test_native_auxiliary_errors_propagate(relation_provider, field):
    provider, shared = relation_provider
    with shared.session() as session:
        with pytest.raises(ValueError) as native:
            session.table('demo.customer').query(
                columns=field if field.startswith('@') else '$'+field).compiled
    with pytest.raises(type(native.value)) as result:
        provider.select(dbtable='customers', _querystring='no matches', auxColumns=field)
    assert str(result.value) == str(native.value)
    # A failed compilation does not poison later requests/sessions.
    assert provider.select(dbtable='customers', _id=1, auxColumns='@state.code')['rows'][0]['_state_code'] == 'TAS'


def test_auxiliary_fields_need_no_registration_and_are_request_local(relation_provider):
    provider, _ = relation_provider
    result = provider.select(dbtable='customers', _id=1, auxColumns='$state,@state.code,@state.code',
                             hiddenColumns='_state_code')
    assert result['columns'] == ['name','state','_state_code']
    assert result['rows'] == [{'id':1,'name':'Alpha','state':'TAS','_state_code':'TAS'}]
    assert provider.select(dbtable='customers', _id=1)['rows'] == [{'id':1,'name':'Alpha'}]
    assert provider.select(dbtable='customers', _id=1, auxColumns='')['columns'] == ['name']
    with pytest.raises(ValueError, match='not exposed'):
        provider.select(dbtable='customers', _id=1, hiddenColumns='_state_code')
    with pytest.raises(ValueError, match='Ambiguous'):
        provider.select(dbtable='customers', _id=1, auxColumns='@state.name,_state_name')


def test_relation_alias_collision_is_refused(relation_provider):
    _, shared = relation_provider
    with pytest.raises(ValueError, match='Ambiguous'):
        AsqueelSelect(shared).register('collision','demo.customer',identifier='id',
            caption='name',columns=('@state.name','_state_name'))


def test_registered_field_cannot_be_overwritten_by_auxiliary_alias(relation_provider):
    _, shared = relation_provider
    provider = AsqueelSelect(shared).register('customers','demo.customer',identifier='id',
        caption='name',columns=('_state_name',))
    with pytest.raises(ValueError, match='Ambiguous'):
        provider.select(dbtable='customers', _id=1, auxColumns='@state.name')
