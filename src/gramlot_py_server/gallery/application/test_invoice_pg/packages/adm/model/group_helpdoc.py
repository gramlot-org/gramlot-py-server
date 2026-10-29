"""Read-only model of adm.adm_group_helpdoc; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('group_helpdoc', name_long='!![en]Help document for group', name_plural='!![en]Help documents for group', caption_field='', pkey='id', sqlname='adm_group_helpdoc', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('_row_count', dtype='L', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('group_code', dtype='A', notnull=False, group='_', name_long='Group', size=':15').relation('adm.group.code', foreign_key=True, constraint_name='fk_561191a7', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('helpdoc_id', dtype='C', notnull=False, group='_', name_long='Help document', size='22').relation('adm.helpdoc.id', foreign_key=True, constraint_name='fk_84a74f80', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='adm_group_helpdoc___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_group_helpdoc___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_group_helpdoc___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_group_helpdoc_group_code_idx', columns='group_code', unique=False, method='btree')
        indexes.index(name='adm_group_helpdoc_helpdoc_id_idx', columns='helpdoc_id', unique=False, method='btree')
