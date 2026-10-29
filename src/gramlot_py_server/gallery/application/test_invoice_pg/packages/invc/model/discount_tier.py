"""Read-only model of invc.invc_discount_tier; physical fields from PostgreSQL."""


class Table:
    def config_db(self, pkg):
        tbl = pkg.table('discount_tier', name_long='!!Discount Tier', name_plural='!!Discount Tiers', pkey='id', sqlname='invc_discount_tier', logicalDeletionField='__del_ts', lastTS='__mod_ts')
        tbl.column('id', dtype='C', notnull=True, size='22')
        tbl.column('__ins_ts', dtype='DH', notnull=False)
        tbl.column('__del_ts', dtype='DH', notnull=False)
        tbl.column('__mod_ts', dtype='DH', notnull=False)
        tbl.column('__ins_user', dtype='T', notnull=False)
        tbl.column('customer_type_code', dtype='A', notnull=False, name_long='!!Customer Type', size=':5').relation('invc.customer_type.code', foreign_key=True, constraint_name='fk_invc_discount_tier_customer_type_code', onDelete_sql='NO ACTION', onUpdate_sql='CASCADE', deferrable=False, initially_deferred=False, indexed=False)
        tbl.column('min_amount', dtype='N', notnull=False, name_long='!!Min Amount')
        tbl.column('max_amount', dtype='N', notnull=False, name_long='!!Max Amount')
        tbl.column('discount_rate', dtype='N', notnull=False, name_long='!!Discount Rate', size='5,2')
        tbl.column('description', dtype='T', notnull=False, name_long='!!Description')
        indexes = tbl.indexes()
        indexes.index(name='invc_discount_tier___del_ts_idx', columns='__del_ts', unique=False, method='btree')
        indexes.index(name='invc_discount_tier___ins_ts_idx', columns='__ins_ts', unique=False, method='btree')
        indexes.index(name='invc_discount_tier___mod_ts_idx', columns='__mod_ts', unique=False, method='btree')
        indexes.index(name='invc_discount_tier_customer_type_code_idx', columns='customer_type_code', unique=False, method='btree')
