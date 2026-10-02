# 910 · Verification

Document ID: **GP-910**.

Derived from GS-020 (gramlot-uvicorn).

[Paired view](../../docs/internal/910-verification.md).

<a id="gp-910-005"></a>

## 005 · Automated checks

Block ID: **GP-910-005**.

The tests live in `tests/<framework>/`, one folder per adapter. Each folder holds
the adapter tests and `test_<framework>_examples.py`, which serves the files of
`examples/<framework>/` and `examples/pages`. Each folder runs with its own
extra only:

```sh
python -m pip install -e ".[flask,test]"
python -m pytest -q tests/flask
```

With every extra installed, `python -m pytest -q` runs the whole suite.

The workflow `.github/workflows/tests.yml` runs each framework with its own extra
on Python 3.11 and 3.12 against the core released on PyPI (required job,
coverage uploaded to Codecov with one flag per framework from the 3.12 run).
An informational job runs every adapter against the `main` branch of
`gramlot-org/gramlot` installed in editable mode. Another job validates the
paired guides and builds both documentation views.

`python scripts/check_docs.py` validates the paired guides and their
identities, then builds `docs` and `docs_llm` with Sphinx and `-W`.

<a id="gp-910-010"></a>

## 010 · Verification record

Block ID: **GP-910-010**.

Local verification, 2026-10-02, on Python 3.12 in a clean virtual environment
with every extra installed: the full suite passes, 30 tests, with `gramlot`
0.2.1, `kajenn` 0.1.0, Django 6.1.1, Flask 3.1.3, FastAPI 0.142.2 and Uvicorn
0.54.0. The same day each example, started from its folder with the server
named in its docstring on a chosen port, answered 200 on `/hello`
(`/pages/hello` for Kajenn). The FastAPI example was started with
`uvicorn app:app`. No browser was run for this package.
