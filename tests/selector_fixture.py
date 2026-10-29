"""Disposable database shared by selector contract tests."""
from asqueel import AsqueelDb, SqlDatabaseConfig
from gramlot_py_server.db.asqueel import AsqueelSelect


def create_database(path):
    recipe = SqlDatabaseConfig()
    root = recipe.source.db("selectors", implementation="sqlite")
    root.connection("main", database=str(path))
    table = root.packages().package("demo", sqlschema="main", sqlprefix=False).table("customer", pkey="id")
    for name, dtype in (("id", "L"), ("name", "T"), ("city", "T"), ("active", "L"), ("secret", "T")):
        table.column(name, dtype=dtype)
    table.formulaColumn("display", sql_formula="$name || ' (' || COALESCE($city,'') || ')'", dtype="T")
    shared = AsqueelDb(recipe)
    with shared.session() as session:
        session.execute("CREATE TABLE customer (id INTEGER PRIMARY KEY, name TEXT NOT NULL, city TEXT, active INTEGER NOT NULL, secret TEXT)").close()
        session.table("demo.customer").sql_insert([
            {"id": 0, "name": "Ada Rossi", "city": "Torino", "active": 1},
            {"id": 3, "name": "Elena Bianchi", "city": "Trento", "active": 1},
            {"id": 2, "name": "Grazia Conti", "city": "Milano", "active": 1},
            {"id": 6, "name": "Luca Ferrari", "city": "Bologna", "active": 1},
            {"id": 4, "name": "Mario Rossi", "city": "Roma", "active": 1},
            {"id": 5, "name": "Mario Rossi", "city": "Firenze", "active": 1},
            {"id": 9, "name": "Bruno Archiviato", "city": "Roma", "active": 0},
        ])
        session.commit()
    return shared


def selection_provider(shared):
    return AsqueelSelect(shared).register("customers", "demo.customer",
        identifier="id", caption="name", columns=("city",), filters=("city",),
        where="$active = :enabled", sqlparams={"enabled": 1})
