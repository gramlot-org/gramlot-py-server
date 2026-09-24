# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""The packaged demo has its own Django configuration and persistent database."""
import os
import subprocess
import sys


def test_polls_database_voting_and_restart(tmp_path):
    script = '''
import django
django.setup()
from django.core.management import call_command
from django.test import Client
from django.utils import timezone
from datetime import timedelta
from gramlot.transport import to_tytx
from gramlot_django.demo.models import Choice, Question
from gramlot_django.demo.seed import seed
call_command('migrate', verbosity=0)
call_command('makemigrations', 'gramlot_polls', check=True, dry_run=True, verbosity=0)
seed()
assert Question.objects.count() == 1
assert Choice.objects.count() == 3
client = Client(enforce_csrf_checks=True)
assert client.get('/polls/').status_code == 200
assert client.get('/polls/spa/polls/').status_code == 200
choice = Choice.objects.first()
url = '/polls/spa/polls/rpc/data/vote'
body = to_tytx({'choice_id': choice.pk}, 'json')
assert client.post(url, body, content_type='application/vnd.tytx+json').status_code == 403
headers = {'HTTP_X_CSRFTOKEN': client.cookies['csrftoken'].value}
assert client.post('/polls/spa/polls/rpc/source/main', to_tytx({}, 'json'),
                   content_type='application/vnd.tytx+json', **headers).status_code == 200
assert client.post(url, body, content_type='application/vnd.tytx+json', **headers).status_code == 200
choice.refresh_from_db()
assert choice.votes == 1
assert client.get(f'/polls/{choice.question_id}/').status_code == 200
assert client.post(f'/polls/{choice.question_id}/vote/', {'choice': choice.pk}).status_code == 403
assert client.post(f'/polls/{choice.question_id}/vote/', {'choice': choice.pk}, **headers).status_code == 302
assert client.post(f'/polls/{choice.question_id}/vote/', {'choice': 999999}, **headers).status_code == 400
assert b'A dashboard: 2' in client.get(f'/polls/{choice.question_id}/results/').content
seed()
choice.refresh_from_db()
assert choice.votes == 2 and Choice.objects.count() == 3
question = choice.question
question.pub_date = timezone.now() + timedelta(days=1)
question.save()
assert client.post(url, body, content_type='application/vnd.tytx+json', **headers).status_code != 200
choice.refresh_from_db()
assert choice.votes == 2
assert client.get(f'/polls/{question.pk}/').status_code == 404
'''
    env = {**os.environ, 'DJANGO_SETTINGS_MODULE': 'gramlot_django.demo.settings',
           'GRAMLOT_POLLS_DATA_DIR': str(tmp_path)}
    result = subprocess.run([sys.executable, '-c', script], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_cli_rejects_invalid_port_before_creating_data(tmp_path):
    directory = tmp_path / 'unused'
    result = subprocess.run([sys.executable, '-m', 'gramlot_django.cli', 'demo',
                             '--port', '70000', '--data-dir', str(directory)],
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert not directory.exists()


def test_bakery_restore_preserves_existing_database(tmp_path):
    import sqlite3
    import zipfile
    from gramlot_django.cli import restore_bakery
    archive = tmp_path / 'bakery.zip'
    with zipfile.ZipFile(archive, 'w') as output:
        output.writestr('bakerydemo.sql', 'CREATE TABLE votes(n INTEGER); INSERT INTO votes VALUES(1);')
    database = tmp_path / 'bakery.sqlite3'
    restore_bakery(archive, database)
    with sqlite3.connect(database) as connection:
        connection.execute('UPDATE votes SET n=2')
    restore_bakery(archive, database)
    with sqlite3.connect(database) as connection:
        assert connection.execute('SELECT n FROM votes').fetchone() == (2,)


def test_bakery_restore_failure_does_not_leave_database(tmp_path):
    import sqlite3
    import zipfile
    import pytest
    from gramlot_django.cli import restore_bakery
    archive = tmp_path / 'broken.zip'
    with zipfile.ZipFile(archive, 'w') as output:
        output.writestr('bakerydemo.sql', 'THIS IS NOT SQL')
    database = tmp_path / 'bakery.sqlite3'
    with pytest.raises(sqlite3.Error):
        restore_bakery(archive, database)
    assert not database.exists()
    assert not list(tmp_path.glob('bakery-*.sqlite3'))
