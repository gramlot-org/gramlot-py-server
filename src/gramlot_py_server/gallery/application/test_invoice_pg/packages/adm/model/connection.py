"""Read-only model of adm.adm_connection; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('connection', name_long='!!Connection', name_plural='!!Connections', pkey='id', sqlname='adm_connection')
        tbl.column('id', dtype='C', notnull=True, name_long='!!Connection id', size='22')
        tbl.column('userid', dtype='C', notnull=False, name_long='!!Userid', size='22')
        tbl.column('username', dtype='A', notnull=False, name_long='!!Username', size=':32')
        tbl.column('ip', dtype='A', notnull=False, name_long='!!Ip address', size=':255')
        tbl.column('start_ts', dtype='DH', notnull=False, name_long='!!Start TS')
        tbl.column('end_ts', dtype='DH', notnull=False, name_long='!!End TS')
        tbl.column('end_reason', dtype='A', notnull=False, name_long='!!End reason', size=':12')
        tbl.column('user_agent', dtype='T', notnull=False, name_long='!!User agent')
        indexes = tbl.indexes()
        indexes.index(name='adm_connection_userid_idx', columns='userid', unique=False, method='btree')
