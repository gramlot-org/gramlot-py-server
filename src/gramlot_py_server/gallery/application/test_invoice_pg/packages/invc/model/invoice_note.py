"""Read-only model of invc.invc_invoice_note; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('invoice_note', name_long='!!Invoice Note', name_plural='!!Invoice Notes', pkey='id', sqlname='invc_invoice_note', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('invoice_id', dtype='C', notnull=False, group='_', name_long='!!Invoice', size='22').relation('invc.invoice.id', foreign_key=True, constraint_name='fk_invc_invoice_note_invoice_id', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('note_type', dtype='A', notnull=False, name_long='!!Note Type', size=':20')
        tbl.column('note_text', dtype='T', notnull=False, name_long='!!Note Text')
        tbl.column('priority', dtype='I', notnull=False, name_long='!!Priority')
        indexes = tbl.indexes()
        indexes.index(name='invc_invoice_note___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='invc_invoice_note___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='invc_invoice_note___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='invc_invoice_note_invoice_id_idx', columns='invoice_id', unique=False, method='btree')
