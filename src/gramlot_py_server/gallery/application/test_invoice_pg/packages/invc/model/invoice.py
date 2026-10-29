"""Read-only model of invc.invc_invoice; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('invoice', name_long='!!Invoice', name_plural='!!Invoice', caption_field='inv_number', pkey='id', sqlname='invc_invoice', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('inv_number', dtype='C', notnull=False, name_long='!!Invoice number', name_short='Inv N', size='10')
        tbl.column('customer_id', dtype='C', notnull=False, group='_', name_long='!!Customer', size='22').relation('invc.customer.id', foreign_key=True, constraint_name='fk_935fad9a', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('date', dtype='D', notnull=False, name_long='!!Date')
        tbl.column('total', dtype='N', notnull=False, name_long='!!Total', size='14,2')
        tbl.column('vat_total', dtype='N', notnull=False, name_long='!!VAT total', size='14,2')
        tbl.column('gross_total', dtype='N', notnull=False, name_long='!!Gross total', size='14,2')
        tbl.column('invoice_time', dtype='H', notnull=False, name_long='!!Invoice Time')
        constraints = tbl.constraints()
        constraints.constraint('cst_74a8dffe', constraint_type='UNIQUE', columns='inv_number')
        indexes = tbl.indexes()
        indexes.index(name='idx_014e7dfa', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_161a123a', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_3e295060', columns='customer_id', unique=False, method='btree')
        indexes.index(name='idx_d060b79b', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='invc_invoice_inv_number_idx', columns='inv_number', unique=True, method='btree')
