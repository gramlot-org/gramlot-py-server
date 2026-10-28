"""Real Kajenn database handlers, reached through Page and PageStore."""
import asyncio
import sqlite3
import threading
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
import pytest
from genro_tytx import from_tytx, to_tytx
from kajenn import AsgiServer
from kajenn.config.templates import DefaultConfiguration
from gramlot_py_server.kajenn import Application
from page_store_checks import channel, open_page, rpc


@pytest.fixture(params=['asqueel', 'sqlalchemy', 'django'])
def database(request, tmp_path):
    backend = request.param
    module = pytest.importorskip(f'kajenn_db.{backend}')
    path = tmp_path / 'customers.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE customer (id INTEGER PRIMARY KEY, name TEXT)')
        db.execute("INSERT INTO customer VALUES (1, 'Ada')")
    if backend == 'asqueel':
        from asqueel import SqlDatabaseConfig
        source = SqlDatabaseConfig()
        model = source.source.db('customers', implementation='sqlite')
        model.connection('main', database=str(path))
        table = model.packages().package('app', sqlschema='main', sqlprefix=False).table('customer', pkey='id')
        table.column('id', dtype='L')
        table.column('name')
        handler, params = module.AsqueelDbHandler, {'source': source}
        statement = 'db.execute(sql)'
        async_statement = 'await db.execute(sql)'
        async_read = '(await result.fetchone())[0]'
    elif backend == 'sqlalchemy':
        handler, params = module.SqlAlchemyDbHandler, {'url': f'sqlite:///{path}'}
        statement = "db.execute(__import__('sqlalchemy').text(sql))"
        async_statement = "await db.execute(__import__('sqlalchemy').text(sql))"
        async_read = 'result.fetchone()[0]'
    else:
        import django
        from django.conf import settings
        from django.db import connections
        if not settings.configured:
            settings.configure(DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': str(path)}}, INSTALLED_APPS=[])
            django.setup()
        alias = 'gramlot_' + uuid4().hex
        config = dict(connections.databases['default'])
        config.update(ENGINE='django.db.backends.sqlite3', NAME=str(path))
        connections.databases[alias] = config
        handler, params = module.DjangoDbHandler, {'alias': alias}
        statement = 'db.cursor()\n    result.execute(sql)'
        async_statement, async_read = 'None', 'None'
    return backend, handler, params, path, statement, async_statement, async_read


@asynccontextmanager
async def site(tmp_path, database):
    backend, handler_class, params, path, statement, async_statement, async_read = database
    source = f'''import asyncio
from gramlot import Page as BasePage, PageStore as BaseStore, endpoint

def query(db, sql):
    result = {statement}
    return result

class Page(BasePage):
    def main(self, root): root.h1('Database customer')
    @endpoint
    def read(self, database=None):
        db = self.db(database)
        assert db is self.db(database)
        return query(db, 'SELECT name FROM customer WHERE id=1').fetchone()[0]
    @endpoint
    def write(self, fail=False):
        db = self.db()
        {"db.set_autocommit(False)" if backend == "django" else ""}
        query(db, "UPDATE customer SET name='Grace' WHERE id=1")
        if fail: raise ValueError('rollback requested')
        db.commit()
        return 'saved'
    @endpoint
    async def read_async(self, wait=False):
        db = self.async_db()
        sql = 'SELECT name FROM customer WHERE id=1'
        result = {async_statement}
        value = {async_read}
        if wait: await asyncio.sleep(60)
        return value

class PageStore(BaseStore):
    def main(self, root):
        root.dataController(func='load', subscribe_load=True)
        root.dataController(func='changed', key='^request.pkey')
    def changed(self, node, key):
        if key: self.load(node)
    def load(self, node, fail=False):
        self.data.set_item('customer.status', 'loading')
        db = self.db()
        value = {"db.table('app.customer').query(where='$id=:pkey', pkey=1).fetchRecord()['name']" if backend == 'asqueel' else "query(db, 'SELECT name FROM customer WHERE id=1').fetchone()[0]"}
        if fail:
            {"db.set_autocommit(False)" if backend == "django" else ""}
            query(db, "UPDATE customer SET name='Uncommitted' WHERE id=1")
            raise ValueError('controller failure')
        self.data.set_item('customer.name', value)
        self.data.set_item('customer.status', 'loaded')
'''
    (tmp_path / 'index.py').write_text(source)
    class Configuration(DefaultConfiguration):
        def applications_section(self, cfg):
            databases = cfg.databases(handler_class=handler_class)
            databases.database(code='default', **params)
            databases.database(code='named', **params)
            cfg.applications().application(code='pages', mount='', app_class=Application,
                                          pages=tmp_path, websocket=True).request(body='raw')
    server = AsgiServer(config=Configuration)
    app = server.applications['pages']
    handler = server.databases['default']
    taken, released = [], []
    original_take, original_release = handler.take, handler.release
    def take(name, call):
        obj = original_take(name, call)
        taken.append((obj, threading.get_ident(), call.request_id))
        return obj
    def release(call):
        released.extend((obj, threading.get_ident(), call.request_id) for obj in call.databases.values())
        return original_release(call)
    handler.take, handler.release = take, release
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server), base_url='http://test') as client:
            page_id, cookie = await open_page(client)
            yield server, app, client, page_id, cookie, taken, released
    finally:
        app.on_shutdown()
        for db_handler in server.db_handlers.values():
            await db_handler.close()
        server.pool.shutdown(wait=True)


@pytest.mark.asyncio
async def test_http_and_socket_share_backend_with_call_lifetime(tmp_path, database):
    async with site(tmp_path, database) as (server, app, client, page_id, cookie, taken, released):
        async def http(name, **params):
            response = await client.post('/gramlot/rpc', content=to_tytx(dict(rpc('http', name, **params), pageId=page_id)),
                                         headers={'content-type': 'application/json'})
            return from_tytx(response.text)
        assert (await http('read'))['value'] == 'Ada'
        assert (await http('read', database='named'))['value'] == 'Ada'
        assert (await http('write', fail=True))['error']['code'] == 'application_error'
        assert (await http('read'))['value'] == 'Ada'
        assert taken == released  # Sync access and release happen on the same native worker.
        assert all(thread != threading.get_ident() for _, thread, _ in taken)
        async with channel(server, cookie, page_id) as (_, send, receive):
            await send(dict(op='subscribe', binderId='customer', path='customer'))
            await receive()
            await send(dict(op='publish', id='load', topic='load', payload={}))
            assert from_tytx((await receive())['text'])['value'] == 'ok'
            changes = [from_tytx((await receive())['text']) for _ in range(3)]
            assert [(m['path'], m['value']) for m in changes] == [('status','loading'), ('name','Ada'), ('status','loaded')]
            await send(rpc('barrier', 'read'))
            assert from_tytx((await receive())['text'])['value'] == 'Ada'
            assert taken == released
            await send(dict(op='subscribe', binderId='request', path='request'))
            await receive()
            await send(dict(op='change', binderId='request', path='pkey', evt='ins', value=1, attr={}))
            while True:
                change = from_tytx((await receive())['text'])
                if change.get('path') == 'status' and change.get('value') == 'loaded': break
            await send(rpc('after-binder', 'read'))
            assert from_tytx((await receive())['text'])['value'] == 'Ada'
            assert taken == released
            await send(dict(op='publish', id='fail', topic='load', payload={'fail': True}))
            assert from_tytx((await receive())['text'])['value'] == 'ok'
            await receive()  # loading; subscriber failure is logged, not an RPC reply.
            await send(rpc('after-failure', 'read'))
            assert from_tytx((await receive())['text'])['value'] == 'Ada'
            await send(rpc('save', 'write'))
            assert from_tytx((await receive())['text'])['value'] == 'saved'
        assert taken == released
        assert server.requests.in_flight == 0
        with sqlite3.connect(database[3]) as db:
            assert db.execute('SELECT name FROM customer').fetchone()[0] == 'Grace'


@pytest.mark.asyncio
async def test_async_access_and_cancellation_release(tmp_path, database):
    async with site(tmp_path, database) as (server, app, client, page_id, cookie, taken, released):
        async with channel(server, cookie, page_id) as (_, send, receive):
            await send(rpc('async', 'read_async'))
            response = from_tytx((await receive())['text'])
            if database[0] == 'django':
                assert response['error']['code'] == 'application_error'
                assert [obj for obj, _, _ in taken] == [obj for obj, _, _ in released]
                assert taken[0][0].connection is None
                return
            assert response['value'] == 'Ada'
            assert [obj for obj, _, _ in taken] == [obj for obj, _, _ in released]
            await send(rpc('pending', 'read_async', wait=True))
            for _ in range(200):
                if len(taken) == 2: break
                await asyncio.sleep(.005)
            assert len(taken) == 2
            await send({'op': 'cancel', 'id': 'pending'})
            await send(rpc('barrier', 'read'))
            assert from_tytx((await receive())['text'])['id'] == 'barrier'
        assert [obj for obj, _, _ in taken] == [obj for obj, _, _ in released]
        assert server.requests.in_flight == 0


@pytest.mark.asyncio
async def test_http_close_waits_for_active_sync_controller(tmp_path, database):
    async with site(tmp_path, database) as (server, app, client, page_id, cookie, taken, released):
        handler = server.databases['default']
        take = handler.take
        entered, finish = threading.Event(), threading.Event()
        def slow_take(name, call):
            obj = take(name, call)
            entered.set()
            if not finish.wait(5): raise TimeoutError('test did not release the worker')
            return obj
        handler.take = slow_take
        async with channel(server, cookie, page_id) as (_, send, receive):
            await send(dict(op='publish', id='load', topic='load', payload={}))
            assert from_tytx((await receive())['text'])['value'] == 'ok'
            for _ in range(200):
                if entered.is_set(): break
                await asyncio.sleep(.005)
            assert entered.is_set()
            close = asyncio.create_task(client.post('/gramlot/close',
                content=to_tytx({'pageId':page_id}), headers={'content-type':'application/json'}))
            try:
                await asyncio.sleep(.02)
                assert not close.done()
            finally:
                finish.set()
            assert (await close).status_code == 200
        assert taken == released
        assert server.requests.in_flight == 0


@pytest.mark.asyncio
async def test_repeated_cancellation_drains_sync_database_worker(tmp_path, database):
    async with site(tmp_path, database) as (server, app, client, page_id, cookie, taken, released):
        handler = server.databases['default']
        take = handler.take
        entered, finish = threading.Event(), threading.Event()
        def slow_take(name, call):
            obj = take(name, call)
            entered.set()
            if not finish.wait(5): raise TimeoutError('test did not release the worker')
            return obj
        handler.take = slow_take
        task = asyncio.create_task(app._store_channel._call(
            to_tytx(dict(rpc('read', 'read'), pageId=page_id)),
            owner=client.cookies['gramlot_owner'], identity=None))
        for _ in range(200):
            if entered.is_set(): break
            await asyncio.sleep(.005)
        assert entered.is_set()
        task.cancel()
        await asyncio.sleep(.01)
        task.cancel()
        close = asyncio.create_task(client.post('/gramlot/close', content=to_tytx({'pageId':page_id}),
                                               headers={'content-type':'application/json'}))
        try:
            await asyncio.sleep(.02)
            assert not task.done() and not close.done()
        finally:
            finish.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert (await close).status_code == 200
        assert taken == released
        assert server.requests.in_flight == 0
