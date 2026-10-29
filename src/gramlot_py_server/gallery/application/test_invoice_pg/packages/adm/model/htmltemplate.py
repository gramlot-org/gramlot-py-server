"""Read-only model of adm.adm_htmltemplate; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('htmltemplate', name_long='!!Letterhead', name_plural='!!Letterheads', rowcaption='name', pkey='id', sqlname='adm_htmltemplate', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('name', dtype='T', notnull=False, name_long='!!Name')
        tbl.column('username', dtype='T', notnull=False, name_long='!!Username')
        tbl.column('version', dtype='T', notnull=False, name_long='!!Version')
        tbl.column('type_code', dtype='A', notnull=False, name_long='Type', size=':15').relation('adm.letterhead_type.code', foreign_key=True, constraint_name='fk_2d4817ba', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('data', dtype='T', notnull=False, name_long='!!Data')
        tbl.column('center_height', dtype='I', notnull=False, name_long='!!Center height')
        tbl.column('center_width', dtype='I', notnull=False, name_long='!!Center width')
        tbl.column('based_on', dtype='C', notnull=False, group='_', name_long='!!Based on', size='22').relation('adm.htmltemplate.id', foreign_key=True, constraint_name='fk_b1c0a379', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=True, initially_deferred=True, indexed=False)
        tbl.column('next_letterhead_id', dtype='C', notnull=False, group='_', name_long='!!Next letterhead', size='22').relation('adm.htmltemplate.id', foreign_key=True, constraint_name='fk_08bece9d', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=True, initially_deferred=True, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='adm_htmltemplate___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='adm_htmltemplate___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='adm_htmltemplate___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='adm_htmltemplate_based_on_idx', columns='based_on', unique=False, method='btree')
        indexes.index(name='adm_htmltemplate_next_letterhead_id_idx', columns='next_letterhead_id', unique=False, method='btree')
        indexes.index(name='adm_htmltemplate_type_code_idx', columns='type_code', unique=False, method='btree')
