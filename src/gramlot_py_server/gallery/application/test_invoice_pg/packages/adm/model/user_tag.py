"""Read-only model of adm.adm_user_tag; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('user_tag', name_long='!!User tag', name_plural='!!User tags', pkey='id', sqlname='adm_user_tag', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('group_code', dtype='A', notnull=False, name_long='!!Group', size=':15').relation('adm.group.code', foreign_key=True, constraint_name='fk_a48a6e31', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('user_id', dtype='C', notnull=False, group='_', name_long='!!User', size='22').relation('adm.user.id', foreign_key=True, constraint_name='fk_9bca5ef6', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('tag_id', dtype='C', notnull=False, group='_', name_long='!!Tag', size='22').relation('adm.htag.id', foreign_key=True, constraint_name='fk_3dbb5ecb', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='adm_user_tag___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_user_tag___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_user_tag___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_user_tag_group_code_idx', columns='group_code', unique=False, method='btree')
        indexes.index(name='adm_user_tag_tag_id_idx', columns='tag_id', unique=False, method='btree')
        indexes.index(name='adm_user_tag_user_id_idx', columns='user_id', unique=False, method='btree')
