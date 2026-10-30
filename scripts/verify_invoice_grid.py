"""Check the invoice Grid against real read-only SQL, including related products."""
import importlib.util
from importlib.resources import files

from gramlot_py_server.gallery.base.service import create_database


def main():
    path = files('gramlot_examples') / 'base/pages/82-grid-database/02-invoice_rows.py'
    spec = importlib.util.spec_from_file_location('invoice_grid', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    service = create_database('asqueel')
    page = module.Page()
    page.database = service
    fields = ('id', 'customer_name', 'state', 'invoice_number', 'invoice_date', 'product_code', 'description',
              'quantity', 'unit_price', 'tot_price')
    try:
        with service.database.session() as session:
            assert session.execute('SHOW transaction_read_only').fetchone()[0] == 'on'
            available = session.execute('SELECT count(*) FROM invc.invc_invoice_row').fetchone()[0]
            expected = session.execute('''SELECT r.id, c.account_name, c.state, i.inv_number, i.date, p.code, p.description,
                r.quantity, r.unit_price, r.tot_price FROM invc.invc_invoice_row r
                LEFT JOIN invc.invc_invoice i ON i.id=r.invoice_id
                LEFT JOIN invc.invc_customer c ON c.id=i.customer_id
                LEFT JOIN invc.invc_product p ON p.id=r.product_id
                ORDER BY r.id LIMIT 100000''').fetchall()
        for limit in module.ROW_LIMITS:
            result = page.load_trial_rows(str(limit))
            rows = list(result.records)
            actual = [tuple(row[field] for field in fields) for row in rows]
            assert actual == [tuple(row) for row in expected[:limit]]
            assert len(rows) == min(limit, available)
            assert result.requested == limit
            assert result.query_ms >= 0
            print(dict(requested=limit, available=available, loaded=len(rows),
                       query_ms=round(result.query_ms, 2)), flush=True)
        for invalid in ('0', '101', '100001', '1000;DROP TABLE invoice_row', 1000, None):
            try:
                page.load_trial_rows(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError('Undeclared record limit accepted')
    finally:
        service.database.close()


if __name__ == '__main__':
    main()
