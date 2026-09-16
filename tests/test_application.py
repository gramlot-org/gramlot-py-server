import re

from flask import Flask
import pytest
from gramlot.transport import TYTX_FORMAT, TYTX_MEDIA_TYPE, from_tytx, to_tytx
from gramlot_flask import mount_gramlot
from gramlot_flask.demo import create_demo, close_demo


def rpc(client, path, params):
    return client.post(path, data=to_tytx(params, TYTX_FORMAT), content_type=TYTX_MEDIA_TYPE)


def decode(response):
    return from_tytx(response.get_data(as_text=True), transport=TYTX_FORMAT)


@pytest.fixture
def plain(tmp_path):
    (tmp_path / 'pages').mkdir()
    (tmp_path / 'pages/hello.py').write_text('''from flask import current_app
from gramlot.page import WebPage, endpoint
class Page(WebPage):
    def main(self, root):
        root.h1(current_app.config['LABEL'])
    @endpoint
    def greet(self, name: str):
        return current_app.config['LABEL'] + ': ' + name
    @endpoint
    def fail(self):
        raise RuntimeError('private-server-detail')
''')
    app = Flask(__name__)
    app.config.update(TESTING=True, LABEL='First app')
    pages = mount_gramlot(app, tmp_path)
    return app, pages, tmp_path


def test_plain_delivery_context_and_fresh_apps(plain):
    app, pages, directory = plain
    other = Flask('other')
    other.config['LABEL'] = 'Second app'
    mount_gramlot(other, directory)
    client = app.test_client()
    assert client.get('/gramlot/hello/').status_code == 200
    assert b'First app' in client.get('/gramlot/hello/recipe').data
    assert b'Second app' in other.test_client().get('/gramlot/hello/recipe').data
    assert b'First app' in client.get('/gramlot/hello/recipe').data
    response = rpc(client, '/gramlot/hello/rpc/data/greet', {'name': 'Alice'})
    assert decode(response) == {'ok': True, 'result': 'First app: Alice'}
    assert response.headers['Cache-Control'] == 'no-store'
    assert client.get(pages.runtime.entry_url).status_code == 200
    assert 'immutable' in client.get(pages.runtime.entry_url).headers['Cache-Control']
    assert client.get('/gramlot/recipe').status_code == 200


@pytest.mark.parametrize('path,status', [
    ('/gramlot/missing/', 404), ('/gramlot/missing/recipe', 404),
    ('/gramlot/_runtime/../../pyproject.toml', 404),
])
def test_unknown_routes(plain, path, status):
    assert plain[0].test_client().get(path).status_code == status


@pytest.mark.parametrize('role,method,params,status', [
    ('source', 'greet', {'name': 'a'}, 409),
    ('bad', 'greet', {}, 404), ('data', 'missing', {}, 404),
    ('data', 'greet', {}, 422), ('data', 'greet', {'name': 123}, 422),
    ('data', 'greet', {'name': 'a', 'extra': True}, 422),
    ('data', 'fail', {}, 500),
])
def test_dispatch_errors(plain, role, method, params, status):
    response = rpc(plain[0].test_client(), f'/gramlot/hello/rpc/{role}/{method}', params)
    assert response.status_code == status
    assert decode(response)['ok'] is False
    assert b'private-server-detail' not in response.data


def test_request_validation_and_asset_escape(plain, tmp_path):
    app, pages, _ = plain
    client = app.test_client()
    path = '/gramlot/hello/rpc/data/greet'
    assert client.post(path, data='{}', content_type='text/plain').status_code == 415
    assert client.post(path, data='invalid', content_type=TYTX_MEDIA_TYPE).status_code == 400
    assert rpc(client, path, ['a']).status_code == 400
    mount = pages.runtime.asset_mounts()[0]
    assert client.get(mount.url_prefix + '../manifest.json').status_code == 404
    assert client.get(mount.url_prefix + 'does-not-exist.js').status_code == 404


@pytest.fixture
def demo(tmp_path):
    app = create_demo(tmp_path)
    app.config['TESTING'] = True
    yield app
    close_demo(app)


def login(client):
    page = client.get('/auth/login')
    token = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', page.text).group(1)
    response = client.post('/auth/login', data={
        'username': 'demo', 'password': 'gramlot-demo', 'csrf_token': token,
    })
    assert response.status_code == 302


def test_demo_authentication_all_surfaces(demo):
    client = demo.test_client()
    assert client.get('/gramlot/community/').status_code == 302
    assert client.get('/gramlot/community/recipe').status_code == 401
    assert rpc(client, '/gramlot/community/rpc/source/main', {}).status_code == 401
    assert rpc(client, '/gramlot/community/rpc/data/dbhandler.dbselect', {}).status_code == 401
    login(client)
    assert client.get('/').status_code == 200
    assert 'href="/gramlot/community/"' in client.get('/').text
    assert client.get('/gramlot/community/').status_code == 200
    assert rpc(client, '/gramlot/community/rpc/source/main', {}).status_code == 200
    client.get('/auth/logout')
    assert rpc(client, '/gramlot/community/rpc/source/member', {'user_id': 1}).status_code == 401


def test_selector_and_profile_share_real_microblog_data(demo):
    from app import db
    from app.models import User, Post
    import sqlalchemy as sa
    client = demo.test_client()
    login(client)
    response = rpc(client, '/gramlot/community/rpc/data/dbhandler.dbselect',
                   {'dbtable': 'users', '_querystring': 'ali'})
    assert response.status_code == 200
    rows = decode(response)['result']['rows']
    assert rows[0]['caption'] == 'alice'
    user_id = rows[0]['id']
    with demo.app_context():
        user = db.session.get(User, user_id)
        db.session.add(Post(author=user, body='A new post from the original Microblog models'))
        db.session.commit()
        assert db.session.scalar(sa.select(sa.func.count()).select_from(User)) == 6
    response = rpc(client, '/gramlot/community/rpc/source/member', {'user_id': str(user_id)})
    assert response.status_code == 200
    assert b'A new post from the original Microblog models' in response.data
    assert b'flask' in response.data.lower()
    assert b'password_hash' not in response.data
    assert b'alice@example.test' not in response.data
    assert client.get('/user/alice').status_code == 200
    assert client.get('/messages').status_code == 200
    assert client.get('/export_posts').status_code == 503


def test_seed_is_idempotent_and_databases_are_independent(tmp_path):
    first = create_demo(tmp_path / 'first')
    from app import db
    from app.models import User
    import sqlalchemy as sa
    with first.app_context():
        user = db.session.scalar(sa.select(User).where(User.username == 'alice'))
        user.about_me = 'Preserve this edit'
        db.session.commit()
    close_demo(first)
    again = create_demo(tmp_path / 'first')
    other = create_demo(tmp_path / 'second')
    try:
        with again.app_context():
            assert db.session.scalar(sa.select(User).where(User.username == 'alice')).about_me == 'Preserve this edit'
            assert db.session.scalar(sa.select(sa.func.count()).select_from(User)) == 6
        with other.app_context():
            assert db.session.scalar(sa.select(User).where(User.username == 'alice')).about_me != 'Preserve this edit'
    finally:
        close_demo(again)
        close_demo(other)


def test_cli_default_starts_demo_and_closes_resources(tmp_path, monkeypatch):
    from click.testing import CliRunner
    from gramlot_flask.cli import main
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path))
    monkeypatch.setattr('click.get_app_dir', lambda name: str(tmp_path))
    calls = []
    monkeypatch.setattr(Flask, 'run', lambda self, **kw: calls.append((self, kw)))
    result = CliRunner().invoke(main)
    assert result.exit_code == 0, result.output
    assert 'demo / gramlot-demo' in result.output
    assert calls[0][1] == {'host': '127.0.0.1', 'port': 8073, 'debug': False, 'use_reloader': False}
    assert (tmp_path / 'microblog/microblog.sqlite').exists()
    result = CliRunner().invoke(main, ['demo', '--data-dir', str(tmp_path / 'custom'), '--port', '8075'])
    assert result.exit_code == 0, result.output
    assert calls[-1][1]['port'] == 8075
