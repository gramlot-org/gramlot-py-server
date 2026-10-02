# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Real SQLite requests through the optional database proxy."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import threading
import subprocess
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
from gramlot.contrib.sqlalchemy import SqliteDbHandler, TableConfig
from gramlot.transport import from_tytx, to_tytx, TYTX_MEDIA_TYPE
import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import OperationalError

from gramlot_fastapi import GramlotApplication, mount_gramlot


@pytest.fixture
def handler(tmp_path):
    path = tmp_path / 'data.sqlite'
    with sqlite3.connect(path) as connection:
        connection.execute('CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL)')
        connection.executemany('INSERT INTO customers VALUES (?, ?)', [
            (0, 'Alice'), (1, 'Bruno'), (2, 'Carla'),
        ])
    connection.close()
    handler = SqliteDbHandler(path, {'customers': TableConfig('customers', 'id', 'name')})
    yield handler
    handler.close()


EXAMPLE = Path(__file__).resolve().parents[1] / 'examples' / 'sqlalchemy'


def query(client, **params):
    return client.post('/page/index/rpc/data/dbhandler.dbselect',
                       content=to_tytx(params, 'json'),
                       headers={'content-type': TYTX_MEDIA_TYPE})


@pytest.mark.parametrize('mounted', [False, True])
def test_recipe_lookup_search_and_exposure(handler, mounted):
    if mounted:
        app = FastAPI()
        mount_gramlot(app, EXAMPLE, db_handler=handler)
    else:
        app = GramlotApplication(EXAMPLE, db_handler=handler)
    with TestClient(app) as client:
        assert client.get('/page/index/').status_code == 200
        recipe = client.get('/page/index/recipe')
        assert recipe.status_code == 200
        assert 'dbhandler.dbselect' in recipe.text
        result = from_tytx(query(client, dbtable='customers', _id=0).text, 'json')
        assert result['result']['rows'] == [{'id': 0, 'caption': 'Alice'}]
        result = from_tytx(query(client, dbtable='customers', _querystring='AR').text, 'json')
        assert result['result']['rows'] == [{'id': 2, 'caption': 'Carla'}]
        assert result['result']['metadata']['match'] == 'contains'
        assert query(client, dbtable='not_exposed').status_code == 500
        assert client.post('/page/index/rpc/data/dbhandler.close',
                           content='{}', headers={'content-type': TYTX_MEDIA_TYPE}).status_code == 404


def test_connections_released_after_success_failure_and_concurrent_requests(handler):
    checked_out, returned, threads = [], [], []

    @event.listens_for(handler.engine, 'checkout')
    def checkout(connection, record, proxy):
        checked_out.append(id(connection))
        threads.append(threading.get_ident())

    @event.listens_for(handler.engine, 'checkin')
    def checkin(connection, record):
        returned.append(id(connection))

    with TestClient(GramlotApplication(EXAMPLE, db_handler=handler)) as client:
        with ThreadPoolExecutor(max_workers=4) as pool:
            responses = list(pool.map(
                lambda key: query(client, dbtable='customers', _id=key), [0, 1, 2] * 4,
            ))
        assert all(response.status_code == 200 for response in responses)
        assert len(checked_out) == len(returned) == 12
        assert threading.get_ident() not in threads
        # A failure after connection acquisition must release the connection too.
        with event_failure(handler):
            assert query(client, dbtable='customers').status_code == 500
        assert len(checked_out) == len(returned) == 13
        assert query(client, dbtable='customers').status_code == 200

    # Handler ownership stays with the caller, even after host shutdown.
    assert handler.dbselect('customers', _id=1)['rows'][0]['caption'] == 'Bruno'
    with handler.engine.connect() as connection:
        with pytest.raises(OperationalError, match='readonly'):
            connection.execute(text("UPDATE customers SET name='changed'"))


@contextmanager
def event_failure(handler):
    def fail(*args):
        raise RuntimeError('deliberate query failure')
    event.listen(handler.engine, 'before_cursor_execute', fail)
    try:
        yield
    finally:
        event.remove(handler.engine, 'before_cursor_execute', fail)


def test_missing_and_invalid_handler_fail_clearly():
    with pytest.raises(TypeError, match='DbHandler'):
        GramlotApplication(EXAMPLE, db_handler=object())
    with TestClient(GramlotApplication(EXAMPLE)) as client:
        response = query(client, dbtable='customers')
        assert response.status_code == 500
        assert 'requires a configured db_handler' in response.text


def test_plain_import_keeps_database_dependencies_optional():
    subprocess.run([sys.executable, '-c', '''
import sys
import gramlot_fastapi
assert 'sqlalchemy' not in sys.modules
assert 'gnr' not in sys.modules
'''], check=True)
