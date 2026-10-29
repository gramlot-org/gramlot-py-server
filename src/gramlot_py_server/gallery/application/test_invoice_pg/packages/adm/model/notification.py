"""Read-only model of adm.adm_notification; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('notification', name_long='!!Notification', name_plural='!!Notifications', caption_field='title', pkey='id', sqlname='adm_notification', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('title', dtype='T', notnull=False, name_long='!!Title')
        tbl.column('template', dtype='T', notnull=False, name_long='!!Template')
        tbl.column('confirm_label', dtype='T', notnull=False, name_long='!!Confirm label')
        tbl.column('tag_rule', dtype='T', notnull=False, name_long='!!Tag rule')
        tbl.column('group_code', dtype='T', notnull=False, name_long='!!Group code')
        tbl.column('all_users', dtype='B', notnull=False, name_long='!!For all users')
        tbl.column('letterhead_id', dtype='C', notnull=False, group='_', name_long='!!Letterhead', size='22').relation('adm.htmltemplate.id', foreign_key=True, constraint_name='fk_9797a9c3', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('linked_query', dtype='T', notnull=False, name_long='!![en]Linked query')
        tbl.column('dynamic_list', dtype='B', notnull=False, name_long='!!Dynamic list', name_short='!!Dynamic', sql_pg_default='true')
        tbl.column('start_date', dtype='D', notnull=False, name_long='!!Start date')
        tbl.column('end_date', dtype='D', notnull=False, name_long='!!End date')
        tbl.column('confirm_button_label', dtype='T', notnull=False)
        tbl.column('cancel_button_label', dtype='T', notnull=False)
        indexes = tbl.indexes()
        indexes.index(name='adm_notification___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_notification___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_notification___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_notification_letterhead_id_idx', columns='letterhead_id', unique=False, method='btree')
