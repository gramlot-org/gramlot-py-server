"""Read-only model of sys.sys_dbchange; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('dbchange', name_long='!!Dbchange', name_plural='!!Db change', pkey='ref', sqlname='sys_dbchange')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('ref', dtype='L', notnull=True, name_long='!!Reference', sql_pg_default="nextval('sys.sys_dbchange_ref_seq'::regclass)")
        tbl.column('tbl', dtype='A', notnull=False, name_long='!!Table', size=':80')
        tbl.column('record_pkey', dtype='T', notnull=False, name_long='!!Record pkey')
        tbl.column('evt', dtype='C', notnull=False, name_long='Evt', name_short='!!Evt', size='1')
        tbl.column('record', dtype='T', notnull=False, name_long='!!Record')
        tbl.column('dbstore', dtype='A', notnull=False, name_long='!!Dbstore', size=':60')
        indexes = tbl.indexes()
        indexes.index(name='idx_2a8c56bd', columns='__ins_ts', unique=False, method='btree')
