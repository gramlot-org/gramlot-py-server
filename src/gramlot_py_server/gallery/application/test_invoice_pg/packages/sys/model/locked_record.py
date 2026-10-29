"""Read-only model of sys.sys_locked_record; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('locked_record', pkey='id', sqlname='sys_locked_record')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('lock_ts', dtype='DH', notnull=False)
        tbl.column('lock_table', dtype='A', notnull=False, size=':64')
        tbl.column('lock_pkey', dtype='A', notnull=False, size=':64')
        tbl.column('page_id', dtype='C', notnull=False, size='22')
        tbl.column('connection_id', dtype='C', notnull=False, size='22')
        tbl.column('username', dtype='A', notnull=False, size=':32')
        indexes = tbl.indexes()
        indexes.index(name='sys_locked_record_lock_table_lock_pkey_idx', columns='lock_table,lock_pkey', unique=True, method='btree')
