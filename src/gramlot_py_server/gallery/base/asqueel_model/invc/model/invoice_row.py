"""Asqueel physical subset; no virtuals or implicit row filters."""

class Table:
    def config_db(self, pkg):
        tbl = pkg.table('invoice_row', pkey='id', sqlname='invc_invoice_row')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('invoice_id', dtype='C', notnull=False, size='22').relation('invc.invoice.id', foreign_key=True, onDelete_sql="NO ACTION", onUpdate_sql="CASCADE")
        tbl.column('product_id', dtype='C', notnull=False, size='22').relation('invc.product.id', foreign_key=True, onDelete_sql="NO ACTION", onUpdate_sql="CASCADE")
        tbl.column('quantity', dtype='I', notnull=False)
        tbl.column('unit_price', dtype='N', notnull=False, size='14,2')
        tbl.column('tot_price', dtype='N', notnull=False, size='14,2')
