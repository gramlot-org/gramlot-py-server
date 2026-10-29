"""Read-only verification of the complete model and customer query surface."""
import json
from pathlib import Path
from asqueel import AsqueelDb
from .configure import DatabaseConfiguration

ROOT = Path(__file__).resolve().parent


def verify():
    catalog = json.loads((ROOT / 'catalog.json').read_text())
    inventory = json.loads((ROOT / 'model_inventory.json').read_text())
    report = {'database': 'test_invoice_pg', 'tables': [], 'customer_fields': [], 'errors': []}
    db = AsqueelDb(DatabaseConfiguration)
    try:
        assert len(db.model.tables) == len(inventory) == len(catalog['tables'])
        with db.session() as session:
            report['transaction_read_only'] = session.execute('SHOW transaction_read_only').fetchone()[0]
            report['default_transaction_read_only'] = session.execute('SHOW default_transaction_read_only').fetchone()[0]
            assert report['transaction_read_only'] == report['default_transaction_read_only'] == 'on'
            for spec in inventory:
                table = session.table(spec['model'])
                schema, name = spec['table'].split('.')
                expected = {c['name'] for c in catalog['columns'] if c['schema'] == schema and c['table'] == name}
                assert set(table.model.columns) == expected, spec['model']
                query = table.query(columns=','.join('$' + n for n in sorted(expected)), where='1=0', limit=1)
                assert query.fetch() == []
                report['tables'].append({'name': spec['model'], 'columns': len(expected), 'query': 'passed'})
            customer = session.table('invc.customer')
            report['customer_physical_columns'] = len(customer.model.columns)
            report['customer_virtual_columns'] = len(customer.model.virtual_columns)
        # Separate sessions keep a failed SELECT from aborting later field checks.
        for field in (*customer.model.columns, *customer.model.virtual_columns):
            try:
                with db.session() as session:
                    rows = session.table('invc.customer').query(columns='$id,$' + field,
                        order_by='$id', limit=1).fetch()
                    report['customer_fields'].append({'name':field, 'status':'passed', 'rows_checked':len(rows)})
            except Exception as error:
                report['errors'].append({'field':field,'type':type(error).__name__,'message':str(error)})
        with db.session() as session:
            customer = session.table('invc.customer')
            fields = (*customer.model.columns, *customer.model.virtual_columns)
            rows = customer.query(columns=','.join('$' + f + ' AS ' + f for f in fields),
                                  order_by='$id', limit=1).fetch()
            assert len(rows) == 1 and set(rows[0].keys()) == set(fields)
            report['customer_combined_projection'] = {'status': 'passed', 'fields': len(fields)}
            report['eligible_customers'] = customer.query().count()
        from gramlot_py_server.db.asqueel import AsqueelSelect
        provider = AsqueelSelect(db).register(
            'customers', 'invc.customer', identifier='id', caption='display_name',
            search=('account_name',), columns=('account_name', 'state_name', 'n_invoices'),
            order_by=('display_name', 'id'))
        result = provider.select(dbtable='customers', _querystring='b',
                                 hiddenColumns='account_name,state_name,n_invoices', limit=10)
        assert result['rows'] and all('b' in row['account_name'].lower() for row in result['rows'])
        first = result['rows'][0]
        lookup = provider.select(dbtable='customers', _id=first['id'])
        assert lookup['rows'][0]['display_name'] == first['display_name']
        try:
            provider.select(dbtable='customers', _querystring='', hiddenColumns='access_token')
        except ValueError:
            pass
        else:
            raise AssertionError('Unexposed customer fields must be rejected')
        report['provider'] = {'search': 'passed', 'identity_lookup': 'passed',
                              'unexposed_field_rejection': 'passed'}
    finally:
        db.close()
    print(json.dumps({k:v for k,v in report.items() if k not in ('tables','customer_fields','errors')},ensure_ascii=False))
    print('Tables checked:', len(report['tables']), 'customer fields passed:',len(report['customer_fields']))
    for error in report['errors']:
        print(error['field'],error['type'],error['message'][:350])
    if report['errors']:
        raise SystemExit(1)


if __name__ == '__main__':
    verify()
