"""Read-only model of sys.sys_externalcall_log; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('externalcall_log', name_long='External call log', name_plural='External call log', caption_field='methodname', pkey='id', sqlname='sys_externalcall_log', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('endpoint', dtype='T', notnull=False, name_long='Endpoint')
        tbl.column('methodname', dtype='T', notnull=False, name_long='Method')
        tbl.column('parameters', dtype='T', notnull=False, name_long='Parameters')
        tbl.column('error', dtype='T', notnull=False, name_long='Error')
        tbl.column('result', dtype='T', notnull=False, name_long='Result')
        indexes = tbl.indexes()
        indexes.index(name='idx_06ce1242', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_158565be', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_6ca9a00a', columns='__ins_ts', unique=False, method='btree')
