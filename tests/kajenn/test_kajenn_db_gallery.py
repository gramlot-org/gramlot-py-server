"""The optional gallery database survives subsequent launches without reseeding."""
import runpy
import sqlite3
from pathlib import Path

import pytest

pytest.importorskip('kajenn_db.asqueel')
pytest.importorskip('gramlot_examples.trials.kajenn_db.model')
RUNNER = Path(__file__).resolve().parents[2] / 'scripts' / 'serve_kajenn_db_gallery.py'


def test_gallery_seeds_once_and_preserves_committed_records(tmp_path):
    prepare = runpy.run_path(str(RUNNER))['prepare_database']
    database = tmp_path / 'demo' / 'customers.sqlite'
    prepare(database)
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT id, name, email FROM customer ORDER BY id').fetchall() == [
            ('1', 'Mario Rossi', 'mario@example.com'),
            ('2', 'Anna Bianchi', 'anna@example.com'),
        ]
        db.execute("UPDATE customer SET name='Saved before restart' WHERE id='1'")
        db.execute("DELETE FROM customer WHERE id='2'")
    prepare(database)
    with sqlite3.connect(database) as db:
        assert db.execute('SELECT id, name FROM customer').fetchall() == [('1', 'Saved before restart')]
        assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
