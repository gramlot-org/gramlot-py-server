"""Verify native models and the common selector contract on real read-only copies."""
import argparse
import json
from .copy_dataset import BACKENDS, specification, database_name, READ_ONLY
from .service import configure_django, create_database


def verify(backend):
    if backend == 'django':
        configure_django()
    provider = create_database(backend)
    spec = specification()
    counts = {}
    for name, table in spec['tables'].items():
        fields = [c['name'] for c in table['columns']]
        if backend == 'asqueel':
            with provider.database.session() as session:
                model = session.table('invc.'+name)
                assert set(model.model.columns) == set(fields)
                assert not model.query(columns=','.join('$'+f for f in fields),where='1=0').fetch()
                counts[name] = model.query().count()
        elif backend == 'sqlalchemy':
            from sqlalchemy import select, func
            from .sqlalchemy_model import metadata
            model = metadata.tables['invc.'+table['physical']]
            assert set(model.c.keys()) == set(fields)
            with provider.engine.connect() as connection:
                assert not connection.execute(select(model).where(False)).all()
                counts[name] = connection.execute(select(func.count()).select_from(model)).scalar_one()
        else:
            from . import django_model
            model = getattr(django_model, {'state':'State','customer':'Customer','invoice':'Invoice',
                'product':'Product','invoice_row':'InvoiceRow'}[name])
            assert {f.column for f in model._meta.fields} == set(fields)
            # Query every mapped column without storing/logging record values.
            queryset = model.objects.values_list(*(f.attname for f in model._meta.fields))
            assert len(list(queryset[:1])) == 1
            counts[name] = model.objects.count()
        assert counts[name] > 0
    cases = 0
    for query in ('b','Archer','a','%','_',"'",'zz-no-match-908172'):
        result = provider.select(dbtable='customers',_querystring=query,hiddenColumns='suburb,state')
        assert len(result['rows']) <= 10
        assert all(query.casefold() in r['account_name'].casefold() for r in result['rows'])
        assert all(set(r)=={'id','account_name','suburb','state'} for r in result['rows'])
        cases += 1
    first = provider.select(dbtable='customers',_querystring='')['rows'][0]
    assert provider.select(dbtable='customers',_id=first['id'])['rows'][0] == first
    cases += 1
    for params in ({'hiddenColumns':'access_token'},{'order_by':'bank_account'},{'unknown_filter':'x'},
                   {'limit':0},{'ignoreCase':'yes'}):
        try:
            provider.select(dbtable='customers',_querystring='',**params)
        except (ValueError,TypeError):
            cases += 1
        else:
            raise AssertionError('Unsupported selector input accepted')
    try:
        provider.select(dbtable='customers',_id=1)
    except TypeError:
        cases += 1
    else:
        raise AssertionError('Coerced text primary key')
    # Compare every selector row with an independent physical LEFT JOIN.
    import psycopg
    from psycopg.rows import dict_row
    with psycopg.connect(dbname=database_name(backend), options=READ_ONLY,
                         row_factory=dict_row) as connection:
        expected = connection.execute(
            'SELECT c.id, c.account_name, c.suburb, c.state, s.name AS state_name '
            'FROM invc.invc_customer c LEFT JOIN invc.invc_state s ON s.code=c.state '
            'ORDER BY c.account_name, c.id').fetchall()
    state_field = '_state_name' if backend == 'asqueel' else 'state_name'
    auxiliary = '@state.name' if backend == 'asqueel' else 'state_name'
    if backend == 'asqueel':
        for row in expected:
            row['_state_name'] = row.pop('state_name')
        with provider.database.session() as session:
            assert session.table('invc.customer').column('state_name') is None
    result = provider.select(dbtable='customers', _querystring='',
        hiddenColumns='suburb,state', auxColumns=auxiliary, limit=len(expected)+1)
    assert result['columns'] == ['account_name', state_field]
    actual = result['rows']
    assert actual == expected
    sample = next(row for row in expected if row[state_field] is not None)
    assert provider.select(dbtable='customers', _id=sample['id'],
        hiddenColumns='suburb,state', auxColumns=auxiliary)['rows'] == [sample]
    try:
        provider.select(dbtable='customers', _querystring='', hiddenColumns='state__name')
    except ValueError:
        pass
    else:
        raise AssertionError('Unregistered relation path accepted')
    cases += 3
    return {'backend':backend,'native_model_rows':counts,'selector_cases':cases,
            'state_name_rows':len(actual),
            'customers_without_state':sum(row['state'] is None for row in expected),
            'status':'passed'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend',choices=BACKENDS,required=True)
    args=parser.parse_args()
    print(json.dumps(verify(args.backend),indent=2))


if __name__=='__main__':
    main()
