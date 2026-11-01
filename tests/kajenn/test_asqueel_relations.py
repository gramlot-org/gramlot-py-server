from asqueel import AsqueelDb, SqlDatabaseConfig
from genro_tytx import to_tytx
import pytest

from gramlot.tree_store import TreeStoreResolver
from gramlot_py_server.asqueel_relations import AsqueelRelations, _display_caption, relation_tree
from contextvars import ContextVar

_current_request = ContextVar("relation_test_request")


def model_config():
    config = SqlDatabaseConfig()
    db = config.source.db('demo', implementation='sqlite')
    package = db.packages().package('app', sqlschema='main', sqlprefix=False)
    customer = package.table('customer', pkey='id', name_long='!!Customer')
    customer.column('id', 'L')
    customer.column('name', 'T', name_long='!!Name')
    customer.colgroup('contact', name_long='!!Contact').column('email', dtype='T', name_long='!!Email')
    customer.formulaColumn('upper_email', sql_formula='upper($email)', dtype='T', name_long='!!Upper email')
    invoice = package.table('invoice', pkey='id', name_long='!!Invoice')
    invoice.column('id', 'L')
    invoice.colgroup('links', name_long='Links').column('customer_id', dtype='L').relation('app.customer.id', relation_name='invoices')
    return config


class Page(AsqueelRelations):
    relation_roots = ('app.customer',)
    def async_db(self, name):
        return _current_request.get().async_db(name)


def test_relation_tree_authors_the_inspector_action():
    import json
    from importlib.resources import files
    from gramlot import GramlotBuilder
    grammar = json.loads(files('gramlot').joinpath('collections/tree.json').read_text())
    builder = GramlotBuilder(collections=[grammar])
    pane = relation_tree(builder.root, datapath='model', table='app.customer')
    nodes = pane.value.get_nodes()
    assert any(node.node_tag == 'label' for node in nodes)
    trees = [node for node in nodes if node.node_tag == 'tree']
    assert len(trees) == 1
    assert trees[0].get_attr('favorites') == '^.favorites'
    assert not any(node.node_tag == 'details' for node in nodes)
    wire = builder.to_tytx()
    assert 'rowActions' in wire
    assert 'treeInspect' in wire
    assert 'treeFavoriteActionState' in wire
    assert 'rowAction' in wire


def test_provisional_caption_filter_removes_only_the_leading_marker():
    assert _display_caption('!!Name') == 'Name'
    assert _display_caption('!![it]Quantity') == 'Quantity'
    assert _display_caption('Hello!!') == 'Hello!!'


def test_group_name_collision_is_rejected():
    config = SqlDatabaseConfig()
    table = config.source.db('demo', implementation='sqlite').packages().package(
        'app', sqlschema='main', sqlprefix=False).table('customer', pkey='id')
    table.column('id', 'L')
    table.colgroup('id', name_long='Identifiers').column('code', dtype='T')
    db = AsqueelDb(config)
    class Request:
        def async_db(self, name): return db
    token = _current_request.set(Request())
    try:
        with pytest.raises(ValueError, match='Field and group names collide'):
            Page().relation_tree('app.customer')
    finally:
        _current_request.reset(token)
        db.close()


def test_asqueel_levels_are_lazy_and_restricted():
    db = AsqueelDb(model_config())
    class Request:
        def async_db(self, name):
            assert name is None
            return db
    token = _current_request.set(Request())
    try:
        page = Page()
        root = page.relation_tree('app.customer')
        assert root.get_node('name').resolver is None
        assert root.get_node('name').attr['caption'] == 'Name'
        assert root.get_node('name').attr['name_long'] == '!!Name'
        assert root.get_node('name').attr['root_table_caption'] == 'Customer'
        assert root.get_node('contact').attr['caption'] == 'Contact'
        assert root.get_node('contact.email').attr['group'] == 'contact.001'
        assert root.get_node('contact.email').attr['caption'] == 'Email'
        assert root.get_node('contact.email').attr['fieldpath'] == 'email'
        assert root.get_node('contact.email').attr['badge'] == 'T'
        assert root.get_node('upper_email').attr['column_kind'] == 'formula'
        assert root.get_node('upper_email').attr['dtype'] == 'T'
        assert root.get_node('upper_email').attr['caption'] == 'Upper email'
        assert isinstance(root.get_node('@invoices').resolver, TreeStoreResolver)
        assert root.get_node('@invoices').attr.get('loop') is None
        assert root.get_node('@invoices').attr['caption'] == 'Invoice'
        assert root.get_node('@invoices').attr['dtype'] == 'RM'
        assert root.get_node('@invoices').attr['badge'] == 'RM'
        assert root.get_node('@invoices').attr['badge_color'] == '#246ed4'
        assert root.get_node('@invoices').attr['relation_direction'] == 'descending'
        assert '::RSLV:' in to_tytx(root)
        child = page.relation_tree('app.customer', path='@invoices', label='@invoices', attributes={})
        assert child.get_node('customer_id') is not None
        assert isinstance(child.get_node('links.@customer_id').resolver, TreeStoreResolver)
        assert child.get_node('links.@customer_id').attr['loop'] is True
        assert child.get_node('links.@customer_id').attr['dtype'] == 'RO'
        assert child.get_node('links.@customer_id').attr['badge'] == 'RO'
        assert child.get_node('links.@customer_id').attr['badge_color'] == '#218544'
        assert child.get_node('links.@customer_id').attr['relation_direction'] == 'ascending'
        assert child.get_node('links.@customer_id').attr['fieldpath'] == '@invoices.@customer_id'
        deeper = page.relation_tree('app.customer', path='@invoices.links.@customer_id')
        assert deeper.get_node('@invoices').attr['loop'] is True
        long_path = '.'.join(['@invoices', 'links', '@customer_id'] * 17)
        deep = page.relation_tree('app.customer', path=long_path)
        assert deep.get_node('@invoices').attr['loop'] is True
        with pytest.raises(ValueError, match='not exposed'):
            page.relation_tree('app.invoice')
        with pytest.raises(ValueError, match='Invalid relation path'):
            page.relation_tree('app.customer', path='name')
        with pytest.raises(ValueError, match='Invalid relation path'):
            page.relation_tree('app.customer', path='@invoices.@customer_id')
        with pytest.raises(ValueError, match='Invalid relation path'):
            page.relation_tree('app.customer', path='@invoices.other.@customer_id')
        with pytest.raises(ValueError, match='Unknown relation path'):
            page.relation_tree('app.customer', path='@missing')
    finally:
        _current_request.reset(token)
        db.close()

@pytest.mark.asyncio
async def test_kajenn_rpc_uses_request_database(tmp_path):
    import asyncio
    import re
    import httpx
    from genro_tytx import from_tytx
    from kajenn import AsgiServer
    from kajenn.config import AsgiConfigBuilder
    from kajenn_db.asqueel import AsqueelDbHandler
    from gramlot_py_server.kajenn import Application

    config = model_config()
    (tmp_path / 'index.py').write_text('''\
from gramlot import Page as BasePage
from gramlot_py_server.asqueel_relations import AsqueelRelations
class Page(AsqueelRelations, BasePage):
    relation_roots = ('app.customer',)
    def main(self, root): root.div('Tree')
''')
    class Site(AsgiConfigBuilder):
        default_config = False
        def main(self, root):
            cfg = root.configuration()
            cfg.databases(handler_class=AsqueelDbHandler).database(code='default', source=config)
            cfg.applications().application(code='pages', mount='', app_class=Application,
                                           pages=tmp_path).request(body='raw')

    server = AsgiServer(config=Site)
    queue, events = asyncio.Queue(), []
    async def send(message): events.append(message)
    task = asyncio.create_task(server({'type': 'lifespan'}, queue.get, send))
    await queue.put({'type': 'lifespan.startup'})
    while not events: await asyncio.sleep(0)
    assert events[0]['type'] == 'lifespan.startup.complete'
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=server), base_url='http://test') as client:
            page = await client.get('/')
            assert page.status_code == 200
            page_id = re.search(r'"pageId":"([^"]+)"', page.text).group(1)
            async def call(path):
                payload = {'id': 'a', 'pageId': page_id, 'contentType': 'data', 'name': 'relation_tree',
                           'params': {'table': 'app.customer', 'path': path, 'label': None, 'attributes': {}}}
                response = await client.post('/gramlot/rpc', content=to_tytx(payload),
                                             headers={'content-type': 'application/json'})
                assert response.status_code == 200
                return from_tytx(response.text)
            root = await call('')
            assert root.get('error') is None, root
            assert root['value'].get_node('@invoices').resolver is not None
            child = await call('@invoices')
            assert child.get('error') is None, child
            assert child['value'].get_node('customer_id') is not None
            assert child['value'].get_node('links.@customer_id').resolver is not None
            nested = await call('@invoices.links.@customer_id')
            assert nested.get('error') is None, nested
            assert nested['value'].get_node('contact.email') is not None
    finally:
        await queue.put({'type': 'lifespan.shutdown'})
        await task
