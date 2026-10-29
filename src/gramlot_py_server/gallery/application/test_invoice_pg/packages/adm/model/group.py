"""Read-only model of adm.adm_group; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('group', name_long='Group', name_plural='!!Groups', caption_field='description', pkey='code', sqlname='adm_group', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('_row_count', dtype='L', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='A', notnull=True, name_long='!!Code', size=':15')
        tbl.column('description', dtype='T', notnull=False, name_long='!!Description')
        tbl.column('custom_menu', dtype='T', notnull=False, name_long='!!Custom menu')
        tbl.column('rootpage', dtype='T', notnull=False, name_long='!![en]Root Page')
        tbl.column('require_2fa', dtype='B', notnull=False, name_long='Require 2fa', name_short='2FA')
        tbl.column('no2fa_alternative_group', dtype='A', notnull=False, group='_', name_long='Without 2FA', size=':15').relation('adm.group.code', foreign_key=True, constraint_name='fk_b63ef0c6', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=True, initially_deferred=True, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='adm_group___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_group___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_group___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_group_no2fa_alternative_group_idx', columns='no2fa_alternative_group', unique=False, method='btree')
