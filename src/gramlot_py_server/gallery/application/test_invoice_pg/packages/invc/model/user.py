"""Read-only model of invc.invc_user; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('user', pkey='id', sqlname='invc_user', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('username', dtype='T', notnull=False)
        constraints = tbl.constraints()
        constraints.constraint('cst_7e146b81', constraint_type='UNIQUE', columns='username')
        indexes = tbl.indexes()
        indexes.index(name='idx_558666f0', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_810588fd', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_9e304810', columns='__mod_ts', unique=False, method='btree')
