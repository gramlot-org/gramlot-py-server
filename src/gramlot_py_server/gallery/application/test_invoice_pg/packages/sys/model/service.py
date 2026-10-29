"""Read-only model of sys.sys_service; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('service', name_long='!!Service', name_plural='!!Services', caption_field='service_identifier', pkey='service_identifier', sqlname='sys_service', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('service_identifier', dtype='A', notnull=True, name_long='!!Identifier', size=':60')
        tbl.column('service_type', dtype='A', notnull=False, name_long='!!Service type', size=':30')
        tbl.column('service_name', dtype='A', notnull=False, name_long='!!Service name', size=':30')
        tbl.column('implementation', dtype='T', notnull=False, name_long='!!Implementation')
        tbl.column('parameters', dtype='T', notnull=False, name_long='!!Parameters')
        tbl.column('daemon', dtype='B', notnull=False, name_long='!!Daemon')
        tbl.column('disabled', dtype='B', notnull=False, name_long='!!Disabled')
        indexes = tbl.indexes()
        indexes.index(name='idx_13f3f882', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_3ba8c783', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_3c51a08f', columns='__ins_ts', unique=False, method='btree')
