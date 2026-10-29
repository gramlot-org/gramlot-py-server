"""Asqueel physical subset; no virtuals or implicit row filters."""

class Table:
    def config_db(self, pkg):
        tbl = pkg.table('state', pkey='code', sqlname='invc_state')
        tbl.column('code', dtype='A', notnull=True, size='5')
        tbl.column('name', name_long='State', dtype='A', notnull=False, size='100')
