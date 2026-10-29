"""Read-only model of invc.invc_staff_role; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('staff_role', name_long='!!Staff Role', name_plural='!!Staff Roles', caption_field='description', lookup=True, pkey='code', sqlname='invc_staff_role', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='A', notnull=True, name_long='!!Code', size=':5')
        tbl.column('description', dtype='T', notnull=False, name_long='!!Description')
        indexes = tbl.indexes()
        indexes.index(name='invc_staff_role___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='invc_staff_role___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='invc_staff_role___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
