"""Django ORM work must not run on the async event-loop thread."""
import asyncio
import pytest
from gramlot_py_server.django import _DjangoFileServer


@pytest.mark.asyncio
async def test_sync_invocation_leaves_event_loop_and_keeps_async_results():
    server = object.__new__(_DjangoFileServer)
    def synchronous():
        with pytest.raises(RuntimeError):
            asyncio.get_running_loop()
        return 17
    async def asynchronous():
        assert asyncio.get_running_loop()
        return 23
    assert await server._invoke(synchronous) == 17
    assert await server._invoke(asynchronous) == 23
    assert await server._invoke(lambda: asynchronous()) == 23


def test_django_rpc_runs_sync_database_work_without_disabling_async_safety(tmp_path):
    import subprocess
    import sys
    import textwrap

    (tmp_path / 'index.py').write_text(textwrap.dedent('''
        from django.db import connection
        from gramlot import Page as BasePage, endpoint

        class Page(BasePage):
            def main(self, root):
                root.div(str(self.answer()))

            @endpoint
            def answer(self):
                with connection.cursor() as cursor:
                    cursor.execute('SELECT 42')
                    return cursor.fetchone()[0]
    '''))
    check = '''
import json, re, sys
from django.conf import settings
settings.configure(SECRET_KEY='test', DATABASES={'default':{
    'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}},
    ALLOWED_HOSTS=['testserver'], INSTALLED_APPS=[], MIDDLEWARE=[])
import django
django.setup()
from gramlot_py_server.django import Pages, _URLconf
from django.test import Client
pages=Pages(sys.argv[1])
settings.ROOT_URLCONF=_URLconf(pages.urlpatterns)
try:
    client=Client()
    document=client.get('/')
    assert document.status_code == 200
    page_id=re.search(r'"pageId":"([^\"]+)"',document.content.decode()).group(1)
    for kind,name in [('source','main'),('data','answer')]:
        response=client.post('/gramlot/rpc',json.dumps(dict(id='test',pageId=page_id,
            contentType=kind,name=name,params={})),content_type='application/json')
        assert response.status_code == 200
        result=response.json()
        assert 'error' not in result,result
        if kind == 'data': assert result['value'] == 42
        else: assert '42' in result['value']
finally:
    pages.shutdown()
'''
    result = subprocess.run([sys.executable, '-c', check, str(tmp_path)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
