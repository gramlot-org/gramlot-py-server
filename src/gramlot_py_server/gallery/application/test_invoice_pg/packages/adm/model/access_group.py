"""Read-only model of adm.adm_access_group; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('access_group', name_long='!!Access group', name_plural='!!Access group', caption_field='code', pkey='code', sqlname='adm_access_group', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='A', notnull=True, name_long='!!Code', size=':10')
        tbl.column('description', dtype='A', notnull=False, name_long='!!Description', size=':30')
        tbl.column('allowed_ip', dtype='T', notnull=False, name_long='!!Allowed ip')
        indexes = tbl.indexes()
        indexes.index(name='adm_access_group___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_access_group___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_access_group___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
