"""Read-only model of adm.adm_week; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('week', name_long='!![en]Week', name_plural='!![en]Week', caption_field='week', pkey='start_date', sqlname='adm_week')
        tbl.column('start_date', dtype='D', notnull=True, name_long='!![en]Start Date')
