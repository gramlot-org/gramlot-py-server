"""Read-only model of sys.sys_shared_object; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('shared_object', name_long='!!Shared Object', name_plural='Shared objects', pkey='id', sqlname='sys_shared_object', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('data', dtype='T', notnull=False, name_long='!!Data')
        tbl.column('backup', dtype='T', notnull=False, name_long='!!Backup')
        tbl.column('description', dtype='A', notnull=False, name_long='Code', size=':50')
        tbl.column('linked_table', dtype='T', notnull=False, name_long='!!Table')
        indexes = tbl.indexes()
        indexes.index(name='idx_0ce8c864', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_7b3d133a', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_98162fd3', columns='description', unique=False, method='btree')
        indexes.index(name='idx_c59720c2', columns='__mod_ts', unique=False, method='btree')
