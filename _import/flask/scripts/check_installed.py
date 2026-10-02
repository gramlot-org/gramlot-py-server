"""Verify an installed wheel, executed outside the repository."""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import sys

from flask import Flask
from gramlot_flask import mount_gramlot

with TemporaryDirectory() as directory:
    root = Path(directory)
    (root / "pages").mkdir()
    (root / "pages/hello.py").write_text("from gramlot.page import WebPage\n"
                                       "class Page(WebPage):\n"
                                       "    def main(self, root): root.h1('Installed Flask page')\n")
    app = Flask(__name__)
    pages = mount_gramlot(app, root)
    client = app.test_client()
    assert client.get('/gramlot/hello/').status_code == 200
    assert b'Installed Flask page' in client.get('/gramlot/hello/recipe').data
    assert client.get(pages.runtime.entry_url).status_code == 200
    if '--demo' not in sys.argv:
        assert importlib.util.find_spec('sqlalchemy') is None
        assert importlib.util.find_spec('flask_login') is None
        print('Installed plain host passed without SQLAlchemy or Microblog dependencies.')
    else:
        from gramlot_flask.demo import create_demo, close_demo
        demo = create_demo(root / 'demo')
        try:
            client = demo.test_client()
            assert client.get('/auth/login').status_code == 200
            with client.session_transaction() as session:
                session['_user_id'] = '1'
                session['_fresh'] = True
            assert client.get('/').status_code == 200
            assert client.get('/gramlot/community/').status_code == 200
            assert b'Microblog community' in client.get('/gramlot/community/recipe').data
            runtime = demo.extensions['gramlot']['/gramlot'].runtime
            assert client.get(runtime.entry_url).status_code == 200
            print('Installed Microblog/Gramlot demo passed.')
        finally:
            close_demo(demo)
