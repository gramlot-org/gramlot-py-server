"""Read-only model of adm.adm_tblinfo; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('tblinfo', name_long='!!Table Info', name_plural='!!Table info', pkey='tblid', sqlname='adm_tblinfo', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('tblid', dtype='A', notnull=True, name_long='!!Table', size=':50')
        tbl.column('pkgid', dtype='A', notnull=False, name_long='!!Package', size=':50')
        tbl.column('description', dtype='A', notnull=False, name_long='!!Description', size=':50')
        indexes = tbl.indexes()
        indexes.index(name='adm_tblinfo___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_tblinfo___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_tblinfo___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_tblinfo_pkgid_idx', columns='pkgid', unique=False, method='btree')
