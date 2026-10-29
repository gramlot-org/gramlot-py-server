"""Read-only model of adm.adm_xgroup; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('xgroup', name_long='!!Deployment group', name_plural='!!Deployment groups', caption_field='description', lookup=True, pkey='code', sqlname='adm_xgroup', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('__syscode', dtype='A', notnull=False, size=':20')
        tbl.column('code', dtype='A', notnull=True, name_long='!!Code', size=':10')
        tbl.column('description', dtype='T', notnull=False, name_long='!!Description')
        constraints = tbl.constraints()
        constraints.constraint('cst_24d1c269', constraint_type='UNIQUE', columns='__syscode')
        indexes = tbl.indexes()
        indexes.index(name='adm_xgroup___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_xgroup___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_xgroup___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_xgroup___syscode_idx', columns='__syscode', unique=True, method='btree')
