"""Asqueel physical subset; no virtuals or implicit row filters."""

class Table:
    def config_db(self, pkg):
        tbl = pkg.table('invoice', pkey='id', sqlname='invc_invoice')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('inv_number', dtype='C', notnull=False, size='10', unique=True)
        tbl.column('customer_id', dtype='C', notnull=False, size='22').relation('invc.customer.id', foreign_key=True, onDelete_sql="NO ACTION", onUpdate_sql="CASCADE")
        tbl.column('date', dtype='D', notnull=False)
        tbl.column('total', dtype='N', notnull=False, size='14,2')
