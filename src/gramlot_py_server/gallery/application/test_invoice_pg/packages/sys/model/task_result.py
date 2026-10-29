"""Read-only model of sys.sys_task_result; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('task_result', name_long='!!Task log', pkey='id', sqlname='sys_task_result', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('task_id', dtype='C', notnull=False, name_long='!!Task ID', size='22').relation('sys.task.id', foreign_key=True, constraint_name='fk_b4dc7c4a', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('result', dtype='T', notnull=False, name_long='!!result')
        tbl.column('result_time', dtype='DH', notnull=False, name_long='!!Result Time')
        tbl.column('start_time', dtype='DH', notnull=False, name_long='!!Start Time')
        tbl.column('end_time', dtype='DH', notnull=False, name_long='!!Start Time')
        tbl.column('is_error', dtype='B', notnull=False, name_long='!!Is Error')
        indexes = tbl.indexes()
        indexes.index(name='idx_00d91910', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='idx_2e7d70b4', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='idx_a6d5db55', columns='task_id', unique=False, method='btree')
        indexes.index(name='idx_e93415ae', columns='__ins_ts', unique=False, method='btree')
