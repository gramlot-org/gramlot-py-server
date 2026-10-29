"""Read-only model of adm.adm_tblinfo_item; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('tblinfo_item', name_long='!!Tblinfo item', name_plural='!!Tblinfo items', caption_field='description', pkey='info_key', sqlname='adm_tblinfo_item', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('info_key', dtype='A', notnull=True, name_long='!!Info key', size=':50')
        tbl.column('code', dtype='A', notnull=False, name_long='!!Code', size=':50')
        tbl.column('description', dtype='A', notnull=False, name_long='!!Description', size=':50')
        tbl.column('item_type', dtype='A', notnull=False, name_long='!!Type', size=':5')
        tbl.column('data', dtype='T', notnull=False, name_long='!!Data')
        tbl.column('tblid', dtype='A', notnull=False, size=':50').relation('adm.tblinfo.tblid', foreign_key=True, constraint_name='fk_bb1fc4eb', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='adm_tblinfo_item___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_tblinfo_item___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_tblinfo_item___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_tblinfo_item_tblid_idx', columns='tblid', unique=False, method='btree')
