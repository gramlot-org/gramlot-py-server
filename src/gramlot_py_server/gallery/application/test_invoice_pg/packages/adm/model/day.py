"""Read-only model of adm.adm_day; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('day', name_long='!!Days', name_plural='!!Days', caption_field='date', pkey='date', sqlname='adm_day')
        tbl.column('date', dtype='D', notnull=True, name_long='!!Date')
        tbl.column('weekday', dtype='L', notnull=False, name_long='!!Weekday')
        tbl.column('is_holyday', dtype='B', notnull=False, name_long='!!Is holyday')
