"""Read-only model of sys.sys_calendar; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('calendar', name_long='!![en]Calendar', name_plural='!![en]Calendar Days', caption_field='date', pkey='date', sqlname='sys_calendar')
        tbl.column('date', dtype='D', notnull=True, name_long='!![en]Date')
        constraints = tbl.constraints()
        constraints.constraint('un_sys_sys_calendar_date', constraint_type='UNIQUE', columns='date')
