"""Read-only model of sys.sys_shorturl; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('shorturl', name_long='Shorturl', name_plural='Shorturl', caption_field='shorturl', pkey='codekey', sqlname='sys_shorturl', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('codekey', dtype='A', notnull=True, name_long='Codekey', size=':100')
        tbl.column('service_identifier', dtype='A', notnull=False, group='_', name_long='Service', size=':60').relation('sys.service.service_identifier', foreign_key=True, constraint_name='fk_a2c5363c', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('longurl', dtype='T', notnull=False, name_long='Long url')
        tbl.column('shorturl', dtype='T', notnull=False, name_long='Short url', name_short='Short')
        tbl.column('domain', dtype='T', notnull=False, name_long='Domain')
        tbl.column('key', dtype='T', notnull=False, name_long='Key')
        tbl.column('expiration', dtype='D', notnull=False, name_long='Expiration')
        tbl.column('traking', dtype='T', notnull=False, name_long='Traking')
        indexes = tbl.indexes()
        indexes.index(name='idx_06aea233', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_249a3201', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_60569029', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_fae70f7f', columns='service_identifier', unique=False, method='btree')
