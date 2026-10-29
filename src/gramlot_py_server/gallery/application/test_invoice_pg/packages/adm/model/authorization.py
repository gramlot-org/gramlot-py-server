"""Read-only model of adm.adm_authorization; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('authorization', name_long='!!Authorization', name_plural='!!Authorizations', pkey='code', sqlname='adm_authorization', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='A', notnull=True, name_long='!!Code', size=':8')
        tbl.column('user_id', dtype='C', notnull=False, name_long='!!User id', size='22').relation('adm.user.id', foreign_key=True, constraint_name='fk_0fd9920f', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('use_ts', dtype='DH', notnull=False, name_long='!!Used datetime')
        tbl.column('used_by', dtype='T', notnull=False, name_long='!!Used by')
        tbl.column('note', dtype='T', notnull=False, name_long='!!Note')
        tbl.column('usage_scope', dtype='T', notnull=False, name_long='!!Use Scope')
        tbl.column('remaining_usages', dtype='L', notnull=False, name_long='!!Remaining usages')
        tbl.column('expiry_date', dtype='D', notnull=False, name_long='!!Expire Date')
        indexes = tbl.indexes()
        indexes.index(name='adm_authorization___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_authorization___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_authorization___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_authorization_user_id_idx', columns='user_id', unique=False, method='btree')
