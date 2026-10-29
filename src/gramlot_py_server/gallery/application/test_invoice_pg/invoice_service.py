"""Read-only selector provider over the complete local test_invoice_pg model."""
import atexit
from asqueel import AsqueelDb
from gramlot_py_server.db.asqueel import AsqueelSelect
from .configure import DatabaseConfiguration

shared = AsqueelDb(DatabaseConfiguration)
with shared.session() as session:
    if session.execute('SHOW transaction_read_only').fetchone()[0] != 'on':
        raise RuntimeError('The invoice example requires PostgreSQL read-only connections')

database = AsqueelSelect(shared).register(
    'customers', 'invc.customer', identifier='id', caption='display_name',
    search=('account_name',),
    columns=('account_name', 'suburb', 'state', 'state_name', 'region_name',
             'payment_description', 'n_invoices', 'customer_score'),
    filters=('state',), order_by=('display_name', 'id'),
)
atexit.register(shared.close)
