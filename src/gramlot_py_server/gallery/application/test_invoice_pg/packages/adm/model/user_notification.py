"""Read-only model of adm.adm_user_notification; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('user_notification', name_long='User notification', name_plural='!!User notifications', pkey='id', sqlname='adm_user_notification', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('user_id', dtype='C', notnull=False, group='_', name_long='!!User', size='22').relation('adm.user.id', foreign_key=True, constraint_name='fk_057f0c3a', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('notification_id', dtype='C', notnull=False, group='_', name_long='!!Notification', size='22').relation('adm.notification.id', foreign_key=True, constraint_name='fk_e27a4888', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('confirmed', dtype='B', notnull=False, name_long='!!Confirmed')
        tbl.column('notification', dtype='T', notnull=False, name_long='Custom Notification')
        indexes = tbl.indexes()
        indexes.index(name='adm_user_notification___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_user_notification___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_user_notification___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_user_notification_notification_id_idx', columns='notification_id', unique=False, method='btree')
        indexes.index(name='adm_user_notification_user_id_idx', columns='user_id', unique=False, method='btree')
