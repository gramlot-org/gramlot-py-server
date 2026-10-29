"""Read-only model of invc.invc_product; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('product', name_long='!!Product', name_plural='!!Prodocts', caption_field='description', pkey='id', sqlname='invc_product', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='A', notnull=False, name_long='!!Code', size=':10')
        tbl.column('description', dtype='A', notnull=False, name_long='!!Description', size=':80')
        tbl.column('presentation_txt', dtype='T', notnull=False, name_long='!!Presentation')
        tbl.column('vat_type_code', dtype='A', notnull=False, group='_', name_long='!![it]VAT type', size=':5').relation('invc.vat_type.code', foreign_key=True, constraint_name='fk_26395a34', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('product_type_id', dtype='C', notnull=False, group='_', name_long='!!Product type', name_short='Type', size='22').relation('invc.product_type.id', foreign_key=True, constraint_name='fk_0b464fa7', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('unit_price', dtype='N', notnull=False, name_long='!!Price', name_short='Price', size='14,2')
        tbl.column('image_url', dtype='T', notnull=False, name_long='!!Image url', name_short='Img')
        tbl.column('details', dtype='T', notnull=False)
        indexes = tbl.indexes()
        indexes.index(name='idx_1affaea7', columns='vat_type_code', unique=False, method='btree')
        indexes.index(name='idx_3cc938a0', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_c34ef379', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_ce84e35e', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_f76fa660', columns='product_type_id', unique=False, method='btree')
