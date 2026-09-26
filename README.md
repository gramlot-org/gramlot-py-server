# Gramlot Uvicorn

Origin: `gramlot-minimal@87bcd90`.

| Profile | Page | Runtime |
| --- | --- | --- |
| Python / Uvicorn | Python `Page` | Generic ASGI adapter served by Uvicorn |

For Python, install Gramlot and `python -m pip install ".[uvicorn]"` from this
checkout, define a directory of Python pages, and use `create_asgi_application(pages)` from `gramlot_uvicorn` as
an ASGI application. Run it with Uvicorn. The Hello World example supplies a
ready-to-run launcher:

```sh
python -m gramlot_example_app.server.uvicorn
```

[Architecture](docs/005-architecture.md) · [Usage](docs/010-usage.md) ·
[Verification](docs/020-verification.md).
