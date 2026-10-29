"""Read-only model of adm.adm_served_page; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('served_page', name_long='!!Served page', name_plural='!!Served pages', pkey='page_id', sqlname='adm_served_page')
        tbl.column('page_id', dtype='C', notnull=True, name_long='!!Page id', size='22')
        tbl.column('pagename', dtype='T', notnull=False, name_long='!!Page name')
        tbl.column('connection_id', dtype='C', notnull=False, group='_', size='22').relation('adm.connection.id', foreign_key=True, constraint_name='fk_044e5728', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('start_ts', dtype='DH', notnull=False, name_long='!!Start ts')
        tbl.column('end_ts', dtype='DH', notnull=False, name_long='!!End ts')
        tbl.column('end_reason', dtype='A', notnull=False, name_long='!!End Reason', size=':12')
        indexes = tbl.indexes()
        indexes.index(name='adm_served_page_connection_id_idx', columns='connection_id', unique=False, method='btree')
