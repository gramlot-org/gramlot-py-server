"""Read-only model of adm.adm_backup; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('backup', name_long='!!Backup', name_plural='!!Backups', rowcaption='$name', pkey='id', sqlname='adm_backup', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('name', dtype='T', notnull=False, name_long='!!Name')
        tbl.column('start_ts', dtype='DH', notnull=False, name_long='!!Backup start ts')
        tbl.column('end_ts', dtype='DH', notnull=False, name_long='!!Backup end ts')
        tbl.column('file_url', dtype='T', notnull=False, name_long='!!Download')
        indexes = tbl.indexes()
        indexes.index(name='adm_backup___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_backup___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_backup___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
