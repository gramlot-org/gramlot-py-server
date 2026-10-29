"""Read-only model of sys.sys_external_token_use; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('external_token_use', name_long='!!External token usage', name_plural='!!External token usages', pkey='id', sqlname='sys_external_token_use')
        tbl.column('id', dtype='C', notnull=True, name_long='!!id', size='22')
        tbl.column('external_token_id', dtype='C', notnull=False, name_long='!!External token id', size='22').relation('sys.external_token.id', foreign_key=True, constraint_name='fk_6901ec1c', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('datetime', dtype='DH', notnull=False, name_long='!!Date and Time')
        tbl.column('host', dtype='T', notnull=False, name_long='!!Host')
        indexes = tbl.indexes()
        indexes.index(name='idx_d88959d4', columns='external_token_id', unique=False, method='btree')
