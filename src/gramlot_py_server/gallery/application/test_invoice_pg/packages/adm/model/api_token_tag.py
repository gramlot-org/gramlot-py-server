"""Read-only model of adm.adm_api_token_tag; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('api_token_tag', name_long='!!API Token Tag', name_plural='!!API Token Tags', pkey='id', sqlname='adm_api_token_tag', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('api_token_id', dtype='C', notnull=False, group='_', name_long='!!API Token', size='22').relation('adm.api_token.id', foreign_key=True, constraint_name='fk_b5526050', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('tag_id', dtype='C', notnull=False, group='_', name_long='!!Tag', size='22').relation('adm.htag.id', foreign_key=True, constraint_name='fk_bf9cf492', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='adm_api_token_tag___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_api_token_tag___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_api_token_tag___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_api_token_tag_api_token_id_idx', columns='api_token_id', unique=False, method='btree')
        indexes.index(name='adm_api_token_tag_tag_id_idx', columns='tag_id', unique=False, method='btree')
