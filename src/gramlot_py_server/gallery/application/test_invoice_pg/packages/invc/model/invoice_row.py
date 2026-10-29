"""Read-only model of invc.invc_invoice_row; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('invoice_row', name_long='!!Invoice row', name_plural='!!Invoice rows', pkey='id', sqlname='invc_invoice_row', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('_row_count', dtype='L', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('invoice_id', dtype='C', notnull=False, group='_', name_long='!!Invoice', size='22').relation('invc.invoice.id', foreign_key=True, constraint_name='fk_invc_invoice_row_invoice_id', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('product_id', dtype='C', notnull=False, group='_', name_long='!!Product', size='22').relation('invc.product.id', foreign_key=True, constraint_name='fk_1095e1e9', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('quantity', dtype='I', notnull=False, name_long='!![it]Quantity', name_short='Q.')
        tbl.column('unit_price', dtype='N', notnull=False, name_long='!!Unit price', name_short='U.Pr.', size='14,2')
        tbl.column('tot_price', dtype='N', notnull=False, name_long='!!Total price', name_short='T.Pr.', size='14,2')
        tbl.column('vat', dtype='N', notnull=False, name_long='VAT', name_short='VAT', size='14,2')
        tbl.column('vat_rate', dtype='N', notnull=False, name_long='!![it]Vat rate', size='5,2')
        indexes = tbl.indexes()
        indexes.index(name='idx_22824d3d', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_6d66801d', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_ca1e7d2b', columns='product_id', unique=False, method='btree')
        indexes.index(name='idx_ccd8c114', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_e7667e79', columns='invoice_id', unique=False, method='btree')
