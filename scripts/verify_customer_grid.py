"""Verify the resident customer Grid endpoint against the read-only Base database."""
import importlib.util
from importlib.resources import files

from gramlot_py_server.gallery.base.service import create_database


def main():
    path = files('gramlot_examples') / 'base/pages/82-grid-database/01-customers.py'
    spec = importlib.util.spec_from_file_location('customer_grid', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    service = create_database('asqueel')
    page = module.Page()
    page.database = service
    try:
        with service.database.session() as session:
            assert session.execute('SHOW transaction_read_only').fetchone()[0] == 'on'
            expected = session.execute('SELECT id, account_name, suburb, state FROM invc.invc_customer ORDER BY account_name, id').fetchall()
        for limit in module.ROW_LIMITS:
            result = page.load_customers(str(limit))
            rows = result.get_item('rows')
            actual = [tuple(node.attr[field] for field in ('id', 'account_name', 'suburb', 'state')) for node in rows.nodes]
            assert actual == [tuple(row) for row in expected[:limit]]
            assert len(rows) == result.get_item('count') == min(limit, len(expected))
            assert result.get_item('requested') == limit
            assert 0 <= result.get_item('query_ms') <= result.get_item('server_ms')
            print(dict(requested=limit, table='invc.invc_customer', rows=len(rows),
                       query_ms=round(result.get_item('query_ms'), 2),
                       server_ms=round(result.get_item('server_ms'), 2)))
        for invalid in ('0', '101', '100001', '1000;DROP TABLE customer', 1000, None):
            try:
                page.load_customers(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError('Undeclared record limit accepted')
    finally:
        service.database.close()


if __name__ == '__main__':
    main()
