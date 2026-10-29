"""Read-only model of sys.sys_external_token; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('external_token', name_long='!!External Token', name_plural='!!External Tokens', pkey='id', sqlname='sys_external_token')
        tbl.column('id', dtype='C', notnull=True, name_long='!!id', size='22')
        tbl.column('datetime', dtype='DHZ', notnull=False, name_long='!!Date and Time')
        tbl.column('expiry', dtype='DHZ', notnull=False, name_long='!!Expiry')
        tbl.column('allowed_user', dtype='A', notnull=False, name_long='!!Destination user', size=':32')
        tbl.column('connection_id', dtype='C', notnull=False, name_long='!!Connection Id', size='22')
        tbl.column('max_usages', dtype='I', notnull=False, name_long='!!Max uses')
        tbl.column('allowed_host', dtype='T', notnull=False, name_long='!!Allowed host')
        tbl.column('page_path', dtype='T', notnull=False, name_long='!!Page path')
        tbl.column('method', dtype='T', notnull=False, name_long='!!Method')
        tbl.column('assigned_user_id', dtype='C', notnull=False, group='_', name_long='Assigned user id', size='22')
        tbl.column('parameters', dtype='T', notnull=False, name_long='!!Parameters')
        tbl.column('exec_user', dtype='A', notnull=False, name_long='!!Execute as user', size=':32')
        tbl.column('userobject_id', dtype='C', notnull=False, group='_', name_long='Userobject', size='22').relation('adm.userobject.id', foreign_key=True, constraint_name='fk_f04925af', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='idx_329046fc', columns='userobject_id', unique=False, method='btree')
        indexes.index(name='idx_8f4c9728', columns='exec_user', unique=False, method='btree')
        indexes.index(name='idx_9e52e956', columns='connection_id', unique=False, method='btree')
        indexes.index(name='idx_aa9eae51', columns='assigned_user_id', unique=False, method='btree')
