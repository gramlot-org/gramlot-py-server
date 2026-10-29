"""Read-only model of adm.adm_ckstyle; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('ckstyle', name_long='Ckeditor style', name_plural='!!Ckeditor styles', caption_field='name', lookup=True, pkey='id', sqlname='adm_ckstyle', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('name', dtype='T', notnull=False, name_long='!!Name')
        tbl.column('element', dtype='T', notnull=False, name_long='!!Dom element', name_short='Element')
        tbl.column('styles', dtype='T', notnull=False, name_long='!!Styles')
        tbl.column('attributes', dtype='T', notnull=False, name_long='!!Attributes')
        tbl.column('stylegroup', dtype='T', notnull=False, name_long='!!Group')
        indexes = tbl.indexes()
        indexes.index(name='adm_ckstyle___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_ckstyle___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_ckstyle___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
