"""Read-only model of adm.adm_shortcut; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('shortcut', name_long='!!Shortcut', name_plural='!!Shortcuts', caption_field='phrase', lookup=True, pkey='keycode', sqlname='adm_shortcut', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('_row_count', dtype='L', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('keycode', dtype='A', notnull=True, name_long='!!Key', size=':10')
        tbl.column('phrase', dtype='T', notnull=False, name_long='!!Phrase')
        tbl.column('groupcode', dtype='A', notnull=False, name_long='!!Group', size=':20')
        indexes = tbl.indexes()
        indexes.index(name='adm_shortcut___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_shortcut___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_shortcut___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
