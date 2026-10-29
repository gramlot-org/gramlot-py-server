"""Read-only model of invc.invc_postcode; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('postcode', name_long='Postcode', name_plural='Postcodes', caption_field='postcode', lookup=False, pkey='id', sqlname='invc_postcode', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('postcode', dtype='A', notnull=False, name_long='postcode', size=':10')
        tbl.column('suburb', dtype='A', notnull=False, name_long='suburb', size=':100')
        tbl.column('state', dtype='A', notnull=False, name_long='state', size=':5').relation('invc.state.code', foreign_key=True, constraint_name='fk_71b94554', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('lat', dtype='T', notnull=False, name_long='lat')
        tbl.column('lon', dtype='T', notnull=False, name_long='lon')
        indexes = tbl.indexes()
        indexes.index(name='idx_1790b53e', columns='postcode', unique=False, method='btree')
        indexes.index(name='idx_2a63d502', columns='state', unique=False, method='btree')
        indexes.index(name='idx_39a44207', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='idx_c949b04d', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_fdceb829', columns='__del_ts', unique=False, method='btree')
