"""Read-only model of sys.sys_batch_log; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('batch_log', name_long='!!Batch log', name_plural='!!Batch logs', caption_field='log_caption', pkey='id', sqlname='sys_batch_log', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('batch_title', dtype='T', notnull=False, name_long='!!Batch title')
        tbl.column('page_id', dtype='C', notnull=False, group='_', name_long='!!Page', size='22')
        tbl.column('start_ts', dtype='DH', notnull=False, name_long='!!Start ts')
        tbl.column('end_ts', dtype='DH', notnull=False, name_long='!!End ts')
        tbl.column('notes', dtype='T', notnull=False, name_long='!!Notes')
        tbl.column('logbag', dtype='T', notnull=False, name_long='!!Log')
        tbl.column('tbl', dtype='T', notnull=False, name_long='!!Table')
        indexes = tbl.indexes()
        indexes.index(name='idx_6890a669', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_895449d7', columns='page_id', unique=False, method='btree')
        indexes.index(name='idx_9f24ebba', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_d40639a3', columns='__ins_ts', unique=False, method='btree')
