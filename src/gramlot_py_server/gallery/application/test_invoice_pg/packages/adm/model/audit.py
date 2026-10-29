"""Read-only model of adm.adm_audit; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('audit', name_long='!!Audit', name_plural='!!Audit', pkey='id', sqlname='adm_audit', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('tablename', dtype='T', notnull=False, name_long='!!Table name')
        tbl.column('event', dtype='C', notnull=False, name_long='!!Change type', size='1')
        tbl.column('username', dtype='T', notnull=False, name_long='!!User')
        tbl.column('record_pkey', dtype='T', notnull=False, name_long='!!Record Pkey')
        tbl.column('version', dtype='L', notnull=False, name_long='!!Version')
        tbl.column('data', dtype='T', notnull=False, name_long='!!Data')
        tbl.column('transaction_id', dtype='T', notnull=False, name_long='!!Transaction id')
        indexes = tbl.indexes()
        indexes.index(name='adm_audit___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_audit___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_audit___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
