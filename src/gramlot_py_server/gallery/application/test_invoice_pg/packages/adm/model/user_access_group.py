"""Read-only model of adm.adm_user_access_group; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('user_access_group', name_long='!!User access', name_plural='!!User access', pkey='id', sqlname='adm_user_access_group', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('user_id', dtype='C', notnull=False, group='_', name_long='!!User', size='22').relation('adm.user.id', foreign_key=True, constraint_name='fk_39298e61', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('access_group_code', dtype='A', notnull=False, group='_', name_long='!!Access group', size=':10').relation('adm.access_group.code', foreign_key=True, constraint_name='fk_aa45f43b', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='adm_user_access_group___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_user_access_group___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_user_access_group___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_user_access_group_access_group_code_idx', columns='access_group_code', unique=False, method='btree')
        indexes.index(name='adm_user_access_group_user_id_idx', columns='user_id', unique=False, method='btree')
