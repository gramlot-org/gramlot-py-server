"""Asqueel-only trial: SELECT on invoice tables, writes confined to cache schema."""
from pathlib import Path
from asqueel import AsqueelDb, SqlDatabaseConfig

ROLE = 'gramlot_cached_trial'
DATABASE = 'gramlot_base_asqueel'


def create_database(*, catalog_only=False):
    class Configuration(SqlDatabaseConfig):
        def main(self, root):
            db = root.db(DATABASE, implementation='postgres',
                         conninfo=f"dbname={DATABASE} options='-c role={ROLE} -c statement_timeout=120000'")
            db.options().cachedFetch()
            if not catalog_only:
                db.packages().package('invc', path=str(Path(__file__).parent/'asqueel_model/invc'),
                                      sqlschema='invc', sqlprefix=False)
    return AsqueelDb(Configuration)
