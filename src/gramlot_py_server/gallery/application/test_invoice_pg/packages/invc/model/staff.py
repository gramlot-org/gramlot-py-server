"""Read-only model of invc.invc_staff; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('staff', name_long='!!Staff', name_plural='!!Staff Members', caption_field='full_name', pkey='id', sqlname='invc_staff', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('first_name', dtype='T', notnull=False, name_long='!!First Name')
        tbl.column('last_name', dtype='T', notnull=False, name_long='!!Last Name')
        tbl.column('email', dtype='T', notnull=False, name_long='!!Email')
        tbl.column('hire_date', dtype='D', notnull=False, name_long='!!Hire Date')
        tbl.column('state', dtype='A', notnull=False, name_long='!!State', size=':5').relation('invc.state.code', foreign_key=True, constraint_name='fk_invc_staff_state', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('role_code', dtype='A', notnull=False, name_long='!!Role', size=':5').relation('invc.staff_role.code', foreign_key=True, constraint_name='fk_invc_staff_role_code', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('user_id', dtype='C', notnull=False, name_long='!!User', size='22').relation('adm.user.id', foreign_key=True, constraint_name='fk_invc_staff_user_id', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=True, initially_deferred=True, indexed=False)
        indexes = tbl.indexes()
        indexes.index(name='invc_staff___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='invc_staff___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='invc_staff___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='invc_staff_role_code_idx', columns='role_code', unique=False, method='btree')
        indexes.index(name='invc_staff_state_idx', columns='state', unique=False, method='btree')
        indexes.index(name='invc_staff_user_id_idx', columns='user_id', unique=False, method='btree')
