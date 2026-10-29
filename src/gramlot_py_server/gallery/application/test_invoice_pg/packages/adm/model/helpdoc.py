"""Read-only model of adm.adm_helpdoc; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('helpdoc', name_long='!![en]Help document', name_plural='!![en]Help documents', caption_field='title', lookup=True, pkey='id', sqlname='adm_helpdoc', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('title', dtype='A', notnull=False, name_long='Title', size=':25')
        tbl.column('url', dtype='T', notnull=False, name_long='Url')
        tbl.column('description', dtype='T', notnull=False, name_long='Description')
        indexes = tbl.indexes()
        indexes.index(name='adm_helpdoc___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_helpdoc___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_helpdoc___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
