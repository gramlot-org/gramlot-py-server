"""Read-only model of adm.adm_user_config; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('user_config', name_long='!!User config', name_plural='!!User config', pkey='ruleid', sqlname='adm_user_config', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('ruleid', dtype='A', notnull=True, size=':80')
        tbl.column('user_group', dtype='A', notnull=False, name_long='!!Group', size=':15').relation('adm.group.code', foreign_key=True, constraint_name='fk_2b0f3704', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('username', dtype='A', notnull=False, group='_', name_long='!!User', size=':32')
        tbl.column('pkgid', dtype='A', notnull=False, name_long='!!Pkg', size=':50').relation('adm.pkginfo.pkgid', foreign_key=True, constraint_name='fk_a8760ee5', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('tblid', dtype='A', notnull=False, name_long='!!Tbl', size=':50').relation('adm.tblinfo.tblid', foreign_key=True, constraint_name='fk_aa9e6d22', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('data', dtype='T', notnull=False, name_long='!!Data')
        indexes = tbl.indexes()
        indexes.index(name='adm_user_config___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_user_config___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_user_config___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_user_config_pkgid_idx', columns='pkgid', unique=False, method='btree')
        indexes.index(name='adm_user_config_tblid_idx', columns='tblid', unique=False, method='btree')
        indexes.index(name='adm_user_config_user_group_idx', columns='user_group', unique=False, method='btree')
        indexes.index(name='adm_user_config_username_idx', columns='username', unique=False, method='btree')
