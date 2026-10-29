"""Asqueel physical subset; relation projections require no alias columns."""

class Table:
    def config_db(self, pkg):
        tbl = pkg.table('customer', pkey='id', sqlname='invc_customer')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('account_name', name_long='Customer', dtype='T', notnull=False)
        tbl.column('suburb', dtype='T', notnull=False)
        tbl.column('state', dtype='A', notnull=False, size='5').relation('invc.state.code', foreign_key=True, onDelete_sql="NO ACTION", onUpdate_sql="CASCADE")
