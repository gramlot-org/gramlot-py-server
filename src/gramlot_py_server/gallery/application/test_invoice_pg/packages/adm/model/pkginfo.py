"""Read-only model of adm.adm_pkginfo; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('pkginfo', name_long='!!Package info', name_plural='!!Package info', caption_field='pkgid', pkey='pkgid', sqlname='adm_pkginfo', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('pkgid', dtype='A', notnull=True, name_long='!!Package', size=':50')
        tbl.column('prj', dtype='A', notnull=False, name_long='!!Project', size=':50')
        indexes = tbl.indexes()
        indexes.index(name='adm_pkginfo___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_pkginfo___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_pkginfo___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
