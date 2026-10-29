"""Read-only model of invc.invc_price_year_note; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('price_year_note', name_long='!!Price Year Note', name_plural='!!Price Year Notes', pkey='id', sqlname='invc_price_year_note', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('product_id', dtype='C', notnull=False, group='_', name_long='!!Product', size='22').relation('invc.product.id', foreign_key=True, constraint_name='fk_invc_price_year_note_product_id', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('year', dtype='L', notnull=False, name_long='!!Year')
        tbl.column('note_text', dtype='T', notnull=False, name_long='!!Note Text')
        tbl.column('importance', dtype='I', notnull=False, name_long='!!Importance')
        indexes = tbl.indexes()
        indexes.index(name='idx_ccf60652', columns='product_id,year', unique=False, method='btree')
        indexes.index(name='invc_price_year_note___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='invc_price_year_note___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='invc_price_year_note___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='invc_price_year_note_product_id_idx', columns='product_id', unique=False, method='btree')
