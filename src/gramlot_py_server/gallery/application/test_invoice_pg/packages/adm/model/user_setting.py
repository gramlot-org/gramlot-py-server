"""Read-only model of adm.adm_user_setting; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('user_setting', name_long='User setting', name_plural='User setting', caption_field='', pkey='identifier', sqlname='adm_user_setting', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('user_id', dtype='C', notnull=True, group='_', name_long='User', size='22').relation('adm.user.id', foreign_key=True, constraint_name='fk_761d34fe', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('setting_code', dtype='A', notnull=True, name_long='Setting code', size=':20')
        tbl.column('setting_data', dtype='T', notnull=False, name_long='Setting data')
        tbl.column('identifier', dtype='A', notnull=True, name_long='Setting identifier', size=':42')
        indexes = tbl.indexes()
        indexes.index(name='adm_user_setting___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_user_setting___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_user_setting___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_user_setting_user_id_idx', columns='user_id', unique=False, method='btree')
