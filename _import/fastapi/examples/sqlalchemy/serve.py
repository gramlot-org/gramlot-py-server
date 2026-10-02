# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Run a disposable, read-only SQLite demo: python examples/sqlalchemy/serve.py."""
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory

from gramlot.contrib.sqlalchemy import SqliteDbHandler, TableConfig
import uvicorn

from gramlot_fastapi import GramlotApplication


def main():
    with TemporaryDirectory(prefix='gramlot-sqlalchemy-') as directory:
        database = Path(directory) / 'demo.sqlite'
        with sqlite3.connect(database) as connection:
            connection.execute('CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL)')
            connection.executemany('INSERT INTO customers VALUES (?, ?)', [
                (1, 'Alice Rossi'), (2, 'Bruno Bianchi'), (3, 'Carla Verdi'),
            ])
        connection.close()
        handler = SqliteDbHandler(database, {
            'customers': TableConfig('customers', 'id', 'name'),
        })

        @asynccontextmanager
        async def lifespan(app):
            try:
                yield
            finally:
                handler.close()

        app = GramlotApplication(Path(__file__).parent, db_handler=handler, lifespan=lifespan)
        uvicorn.run(app, host='127.0.0.1', port=8000)


if __name__ == '__main__':
    main()
