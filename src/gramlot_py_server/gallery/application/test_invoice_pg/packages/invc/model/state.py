"""Read-only model of invc.invc_state; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('state', name_long='!!State', name_plural='!!States', caption_field='code', lookup=True, pkey='code', sqlname='invc_state', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='A', notnull=True, name_long='!!Code', size=':5')
        tbl.column('name', dtype='A', notnull=False, name_long='!!Name', size=':100')
        tbl.column('region_code', dtype='A', notnull=False, name_long='!!Region', size=':5').relation('invc.region.code', foreign_key=True, constraint_name='fk_5ca36a72', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='idx_0c31e35f', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_4e4d89bb', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_639974a6', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='invc_state_region_code_idx', columns='region_code', unique=False, method='btree')
