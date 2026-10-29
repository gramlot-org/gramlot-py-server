"""Existing PostgreSQL database: all connections are read-only, with no schema setup."""
from pathlib import Path
from asqueel import SqlDatabaseConfig

ROOT = Path(__file__).resolve().parent
CONNINFO = "dbname=test_invoice_pg options='-c default_transaction_read_only=on -c statement_timeout=15000'"


class DatabaseConfiguration(SqlDatabaseConfig):
    def main(self, root):
        db = root.db("test_invoice_pg", implementation="postgres", conninfo=CONNINFO)
        packages = db.packages()
        for schema in ("adm", "invc", "sys"):
            packages.package(schema, path=str(ROOT / "packages" / schema), sqlschema=schema, sqlprefix=False)
