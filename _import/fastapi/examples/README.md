# Examples

## Plain FastAPI inspector

Run `gramlot-fastapi serve examples/plain` from this checkout and open
http://127.0.0.1:8000/page/inspector/. This Python-authored page demonstrates
Data bindings and Source inspection without a database. See the
[inspector guide](../docs/025-inspector.md).

## Genropy

`gramlot_fastapi._examples/genropy` contains packaged Python-authored Gramlot pages for an initialized Genropy
`GnrApp`. Start them from an environment that provides the legacy application:

```python
from gnr.app.gnrapp import GnrApp
from gramlot_fastapi.genropy import create_genropy_application

app = create_genropy_application(
    "src/gramlot_fastapi/_examples/genropy",
    genropy_application=GnrApp("my_instance"),
)
```

The pages expect the sample `invc` model described in their README. Plain
FastAPI hosting does not initialize Genropy and does not expose these pages.

## SQLAlchemy / SQLite

Install `.[sqlalchemy]`, then run `python examples/sqlalchemy/serve.py`.
Open http://127.0.0.1:8000/page/index/. The demo creates three synthetic customers
in a temporary database, opens it read-only through the core adapter and closes
the handler on server shutdown. See [the SQLAlchemy guide](../docs/035-sqlalchemy.md).
