"""Read-only model of invc.invc_customer_type; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('customer_type', name_long='!!Customer type', name_plural='!!Customer types', caption_field='description', lookup=True, pkey='code', sqlname='invc_customer_type', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='A', notnull=True, name_long='!!Code', size=':5')
        tbl.column('description', dtype='T', notnull=False, name_long='Description')
        indexes = tbl.indexes()
        indexes.index(name='idx_275ac7d6', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_2b87e383', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_ea061055', columns='__mod_ts', unique=False, method='btree')
