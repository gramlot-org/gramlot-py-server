"""Read-only model of sys.sys_upgrade; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('upgrade', name_long='!!Upgrade ', name_plural='!!Upgrades', caption_field='codekey', pkey='codekey', sqlname='sys_upgrade', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('codekey', dtype='A', notnull=True, name_long='Identifier', size=':306')
        tbl.column('pkg', dtype='A', notnull=False, name_long='Package', size=':50')
        tbl.column('filename', dtype='A', notnull=False, name_long='!!Filename', size=':255')
        tbl.column('error', dtype='T', notnull=False, name_long='!!Upgrade error', name_short='!!Error')
        indexes = tbl.indexes()
        indexes.index(name='idx_19de0f67', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_9018f031', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_998e916d', columns='__ins_ts', unique=False, method='btree')
