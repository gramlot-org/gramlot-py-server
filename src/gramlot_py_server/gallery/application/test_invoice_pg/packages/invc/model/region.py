"""Read-only model of invc.invc_region; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('region', name_long='!!Region', name_plural='!!Regions', pkey='code', sqlname='invc_region', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='A', notnull=True, name_long='!!Code', size=':5')
        tbl.column('name', dtype='A', notnull=False, name_long='!!Name', size=':50')
        indexes = tbl.indexes()
        indexes.index(name='invc_region___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='invc_region___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='invc_region___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
