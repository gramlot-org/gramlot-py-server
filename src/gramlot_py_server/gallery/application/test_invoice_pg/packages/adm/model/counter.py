"""Read-only model of adm.adm_counter; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('counter', name_long='!!Counter', pkey='codekey', sqlname='adm_counter', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('codekey', dtype='A', notnull=True, name_long='!!Codekey', size=':80')
        tbl.column('code', dtype='A', notnull=False, name_long='!!Code', size=':12')
        tbl.column('pkg', dtype='A', notnull=False, name_long='!!Package', size=':12')
        tbl.column('tbl', dtype='A', notnull=False, name_long='!!Table', size=':30')
        tbl.column('fld', dtype='A', notnull=False, name_long='!!Counter Field', size=':30')
        tbl.column('period', dtype='A', notnull=False, name_long='!!Period', size=':10')
        tbl.column('counter', dtype='L', notnull=False, name_long='!!Counter')
        tbl.column('last_used', dtype='D', notnull=False, name_long='!!Last used')
        tbl.column('holes', dtype='T', notnull=False, name_long='!!Holes')
        tbl.column('errors', dtype='T', notnull=False, name_long='!!Errors')
        indexes = tbl.indexes()
        indexes.index(name='adm_counter___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_counter___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_counter___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_counter_period_idx', columns='period', unique=False, method='btree')
