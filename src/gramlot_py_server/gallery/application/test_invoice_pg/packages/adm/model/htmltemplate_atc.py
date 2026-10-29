"""Read-only model of adm.adm_htmltemplate_atc; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('htmltemplate_atc', caption_field='description', rowcaption='$description', name_long='!!Letterhead  Attachment', name_plural='!!Letterhead Attachments', pkey='id', sqlname='adm_htmltemplate_atc', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, group='_', name_long='Id', size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('_row_count', dtype='L', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('filepath', dtype='T', notnull=False, name_long='!![en]Filepath')
        tbl.column('filepath_hash', dtype='T', notnull=False, name_long='MD5 hash')
        tbl.column('filepath_original_name', dtype='T', notnull=False, name_long='!![en]Original name')
        tbl.column('external_url', dtype='T', notnull=False, name_long='!![en]External url')
        tbl.column('description', dtype='T', notnull=False, name_long='!![en]Description')
        tbl.column('mimetype', dtype='T', notnull=False, name_long='!![en]Mimetype')
        tbl.column('text_content', dtype='T', notnull=False, name_long='!![en]Content')
        tbl.column('info', dtype='T', notnull=False, name_long='!![en]Additional info')
        tbl.column('is_foreign_document', dtype='B', notnull=False, name_long='!![en][Is foreign document]', name_short='!![en]Ext')
        tbl.column('maintable_id', dtype='C', notnull=False, group='*', name_long='htmltemplate', size='22').relation('adm.htmltemplate.id', foreign_key=True, constraint_name='fk_c88e0a68', onDelete_sql='CASCADE', onUpdate_sql='CASCADE', deferrable=True, initially_deferred=True, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='adm_htmltemplate_atc___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_htmltemplate_atc___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_htmltemplate_atc___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_htmltemplate_atc_maintable_id_idx', columns='maintable_id', unique=False, method='btree')
