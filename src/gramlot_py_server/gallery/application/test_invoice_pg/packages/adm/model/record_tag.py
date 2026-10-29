"""Read-only model of adm.adm_record_tag; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('record_tag', name_long='!!Table tag', name_plural='!!Table tags', pkey='id', sqlname='adm_record_tag', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('tablename', dtype='T', notnull=False, name_long='!!Table name')
        tbl.column('tag', dtype='T', notnull=False, name_long='!!Tag')
        tbl.column('description', dtype='T', notnull=False, name_long='!!Description')
        indexes = tbl.indexes()
        indexes.index(name='adm_record_tag___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_record_tag___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_record_tag___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
