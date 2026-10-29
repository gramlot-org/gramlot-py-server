"""Read-only model of adm.adm_menu_page; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('menu_page', name_long='!!Menu Page', name_plural='!!Menu Pages', rowcaption='$label', caption_field='label', pkey='id', sqlname='adm_menu_page', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('label', dtype='T', notnull=False, name_long='!!Label')
        tbl.column('filepath', dtype='T', notnull=False, name_long='!!Filepath')
        tbl.column('tbl', dtype='T', notnull=False, name_long='!!Table')
        tbl.column('pkg', dtype='T', notnull=False, name_long='!!Package')
        tbl.column('metadata', dtype='T', notnull=False, name_long='!!Metadata')
        indexes = tbl.indexes()
        indexes.index(name='adm_menu_page___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_menu_page___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_menu_page___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
