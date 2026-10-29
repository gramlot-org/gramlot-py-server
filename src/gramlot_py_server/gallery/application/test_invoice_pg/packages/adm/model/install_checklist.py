"""Read-only model of adm.adm_install_checklist; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('install_checklist', name_long='!!Install checklist', name_plural='!!Install checklist', caption_field='description', pkey='__syscode', sqlname='adm_install_checklist', logicalDeletionField='__del_ts')
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('__syscode', dtype='A', notnull=True, name_long='!![en]Internal code', size=':20')
        tbl.column('name', dtype='T', notnull=False, name_long='!!Name')
        tbl.column('description', dtype='T', notnull=False, name_long='!!Description')
        tbl.column('pkg', dtype='A', notnull=False, name_long='!!Package', size=':20')
        tbl.column('checked', dtype='B', notnull=False, name_long='!!Checked')
        tbl.column('check_ts', dtype='DH', notnull=False, name_long='!!Check ts')
        tbl.column('check_user', dtype='A', notnull=False, name_long='!!Check user', size=':30')
        tbl.column('annotations', dtype='T', notnull=False, name_long='!!Annotations')
        tbl.column('doc_url', dtype='T', notnull=False, name_long='!!Documentation url', name_short='!!Url')
        constraints = tbl.constraints()
        constraints.constraint('un_adm_adm_install_checklist___syscode', constraint_type='UNIQUE', columns='__syscode')
        indexes = tbl.indexes()
        indexes.index(name='adm_install_checklist___del_ts_idx', columns='__del_ts', unique=False, method='btree')
