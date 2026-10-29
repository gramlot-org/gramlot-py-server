"""Read-only model of invc.invc_vat_type; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('vat_type', name_long='!!VAT type', name_plural='!!VAT types', caption_field='description', lookup=True, pkey='code', sqlname='invc_vat_type', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='A', notnull=True, name_long='!!Code', size=':5')
        tbl.column('description', dtype='T', notnull=False, name_long='Description')
        tbl.column('vat_rate', dtype='N', notnull=False, name_long='!!VAT rate', size='5,2')
        indexes = tbl.indexes()
        indexes.index(name='idx_3e4ac1a8', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_6ebe1f64', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_c12f0ce1', columns='__del_ts', unique=False, method='btree')
