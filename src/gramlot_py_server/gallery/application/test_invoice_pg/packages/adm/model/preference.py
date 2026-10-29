"""Read-only model of adm.adm_preference; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('preference', name_long='!!Preference', name_plural='!!Preference', pkey='code', sqlname='adm_preference', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='C', notnull=True, name_long='!!Code', size='12')
        tbl.column('data', dtype='T', notnull=False, name_long='!!Data')
        indexes = tbl.indexes()
        indexes.index(name='adm_preference___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_preference___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_preference___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
