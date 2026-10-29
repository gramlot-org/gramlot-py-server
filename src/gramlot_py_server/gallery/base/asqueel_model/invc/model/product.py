"""Asqueel physical subset; no virtuals or implicit row filters."""

class Table:
    def config_db(self, pkg):
        tbl = pkg.table('product', pkey='id', sqlname='invc_product')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('code', dtype='A', notnull=False, size='10')
        tbl.column('description', dtype='A', notnull=False, size='80')
        tbl.column('unit_price', dtype='N', notnull=False, size='14,2')
