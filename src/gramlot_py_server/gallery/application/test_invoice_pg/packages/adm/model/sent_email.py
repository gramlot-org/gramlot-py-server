"""Read-only model of adm.adm_sent_email; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('sent_email', name_long='Sent email', name_plural='!!Sent email', caption_field='batch_key', pkey='id', sqlname='adm_sent_email', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('code', dtype='T', notnull=False, name_long='!!Code')
        tbl.column('tbl', dtype='T', notnull=False, name_long='!!Table')
        tbl.column('mail_address', dtype='T', notnull=False, name_long='!!Email address')
        tbl.column('sent_ts', dtype='DH', notnull=False, name_long='!!Sent ts')
        tbl.column('record_id', dtype='T', notnull=False, name_long='Record id')
        indexes = tbl.indexes()
        indexes.index(name='adm_sent_email___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_sent_email___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_sent_email___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
