"""Safety boundaries and portable prefix/containment contract."""
import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine
from gramlot_py_server.db.sqlalchemy import SQLAlchemySelect
from gramlot_py_server.gallery.base.copy_dataset import database_name, specification


def test_copy_destinations_cannot_name_the_source():
    for name in ('test_invoice_pg','test_invoice_pg_xl','postgres','other',None):
        with pytest.raises(ValueError):
            database_name(name)


def test_minimum_spec_has_no_outside_relations_or_virtual_columns():
    spec=specification()
    assert spec['source_database'] == 'test_invoice_pg_xl'
    assert set(spec['tables'])=={'state','customer','invoice','product','invoice_row'}
    assert sum(len(t['columns']) for t in spec['tables'].values())==21
    physical={t['physical'] for t in spec['tables'].values()}
    for table in spec['tables'].values():
        fields={c['name'] for c in table['columns']}
        for c in table['constraints']:
            assert set(c['columns'])<=fields
            if c['type']=='f':
                assert c['related_table'] in physical
    assert spec['tables']['invoice_row']['physical']=='invc_invoice_row'


def test_sqlalchemy_prefix_precedes_containment_and_wildcards_are_literal():
    engine=create_engine('sqlite://')
    metadata=MetaData()
    people=Table('people',metadata,Column('id',Integer,primary_key=True),Column('name',String))
    metadata.create_all(engine)
    try:
        with engine.begin() as connection:
            connection.execute(people.insert(),[{'id':1,'name':'Archer Baker'},
                {'id':2,'name':'Baker'}, {'id':3,'name':'100%_literal'}])
        service=SQLAlchemySelect(engine).register('people',people,identifier='id',caption='name')
        assert [r['id'] for r in service.select(dbtable='people',_querystring='b')['rows']]==[2]
        assert [r['id'] for r in service.select(dbtable='people',_querystring='cher')['rows']]==[1]
        assert [r['id'] for r in service.select(dbtable='people',_querystring='%_')['rows']]==[3]
        assert not service.select(dbtable='people',_querystring='b',ignoreCase=False)['rows']
    finally:
        engine.dispose()


def test_sqlalchemy_state_name_preserves_customers_without_state():
    from sqlalchemy import select, ForeignKey
    engine = create_engine('sqlite://')
    metadata = MetaData()
    states = Table('states', metadata, Column('code', String, primary_key=True),
                   Column('name', String))
    customers = Table('customers', metadata, Column('id', Integer, primary_key=True),
        Column('name', String), Column('state', String, ForeignKey('states.code')))
    metadata.create_all(engine)
    try:
        with engine.begin() as connection:
            connection.execute(states.insert(), [{'code':'TAS','name':'Tasmania'}])
            connection.execute(customers.insert(), [
                {'id':1,'name':'Alpha','state':'TAS'}, {'id':2,'name':'Beta','state':None}])
        selection = select(customers, states.c.name.label('state_name')).select_from(
            customers.outerjoin(states, customers.c.state == states.c.code)).subquery()
        provider = SQLAlchemySelect(engine).register('customers', selection,
            identifier='id', caption='name', columns=('state_name',))
        assert provider.select(dbtable='customers', _querystring='',
            hiddenColumns='state_name')['rows'] == [
                {'id':1,'name':'Alpha','state_name':'Tasmania'},
                {'id':2,'name':'Beta','state_name':None}]
        assert provider.select(dbtable='customers', _id=2,
            hiddenColumns='state_name')['rows'][0]['state_name'] is None
    finally:
        engine.dispose()


def test_django_registered_relation_annotation_and_null_state():
    # Isolate Django settings from the HTTP adapter suite.
    import subprocess
    import sys
    result = subprocess.run([sys.executable, '-c', """
from django.conf import settings
settings.configure(DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}, INSTALLED_APPS=[])
import django
django.setup()
from django.db import models, connection
from django.db.models import F
from django.test.utils import CaptureQueriesContext
from gramlot_py_server.db.django import DjangoSelect
class State(models.Model):
    code = models.CharField(max_length=5, primary_key=True)
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'selector_test'
class Customer(models.Model):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(State, null=True, on_delete=models.DO_NOTHING)
    class Meta:
        app_label = 'selector_test'
with connection.schema_editor() as editor:
    editor.create_model(State)
    editor.create_model(Customer)
State.objects.create(code='TAS', name='Tasmania')
Customer.objects.create(id=1, name='Alpha', state_id='TAS')
Customer.objects.create(id=2, name='Beta', state_id=None)
provider = DjangoSelect().register('customers', Customer, identifier='id', caption='name',
    columns=('state_name',), filters=('state_name',), annotations={'state_name':F('state__name')})
with CaptureQueriesContext(connection) as queries:
    rows = provider.select(dbtable='customers', _querystring='', hiddenColumns='state_name')['rows']
assert len(queries) == 1
assert rows == [{'id':1,'name':'Alpha','state_name':'Tasmania'}, {'id':2,'name':'Beta','state_name':None}]
assert provider.select(dbtable='customers', _id=2, hiddenColumns='state_name')['rows'] == [rows[1]]
assert provider.select(dbtable='customers', _querystring='', state_name='Tasmania')['rows'] == [{'id':1,'name':'Alpha'}]
for kwargs in ({'hiddenColumns':'state__name'}, {'order_by':'state__name'}, {'state__name':'Tasmania'}):
    try:
        provider.select(dbtable='customers', _querystring='', **kwargs)
    except ValueError:
        pass
    else:
        raise AssertionError('Unregistered relation exposed')
for annotations in ({'name':F('state__name')}, {'state__name':F('state__name')}):
    try:
        DjangoSelect().register('invalid', Customer, identifier='id', caption='name', annotations=annotations)
    except ValueError:
        pass
    else:
        raise AssertionError('Invalid annotation alias accepted')
"""], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_local_candidate_excludes_application_launcher_and_model():
    from importlib.resources import files
    assert not (files('gramlot_py_server') / 'gallery' / 'application').is_dir()
