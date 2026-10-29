"""Read-only model of adm.adm_language; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('language', name_long='Language', name_plural='!!Languages', lookup=True, caption_field='name', pkey='code', sqlname='adm_language', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('_row_count', dtype='L', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('__syscode', dtype='A', notnull=False, size=':20')
        tbl.column('code', dtype='A', notnull=True, name_long='!!Code', size=':2')
        tbl.column('name', dtype='T', notnull=False, name_long='!!Name')
        constraints = tbl.constraints()
        constraints.constraint('cst_adff5efb', constraint_type='UNIQUE', columns='__syscode')
        indexes = tbl.indexes()
        indexes.index(name='adm_language___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_language___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_language___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_language___syscode_idx', columns='__syscode', unique=True, method='btree')
