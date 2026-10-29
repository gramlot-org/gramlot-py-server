"""Read-only model of sys.sys_dataretention; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('dataretention', rowcaption='$table_fullname', caption_field='task_fullname', name_long='!!Data Retention Policy', name_plural='!!Data Retention Policies', pkey='id', sqlname='sys_dataretention', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('table_fullname', dtype='T', notnull=False, name_long='!!Table')
        tbl.column('filter_column', dtype='T', notnull=False, name_long='!!Filter Column')
        tbl.column('retention_period', dtype='L', notnull=False, name_long='!!Retention (days)')
        constraints = tbl.constraints()
        constraints.constraint('cst_2b6b9436', constraint_type='UNIQUE', columns='table_fullname')
        indexes = tbl.indexes()
        indexes.index(name='idx_84c2b441', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_918bcf82', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_c5f19321', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='sys_dataretention_table_fullname_idx', columns='table_fullname', unique=True, method='btree')
