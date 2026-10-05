# 910 · Verification

Document ID: **GP-910**.

Derived from a guide of the archived gramlot-uvicorn repository.

[Paired view](../../docs/internal/910-verification.md).

<a id="gp-910-005"></a>

## 005 · Automated checks

Block ID: **GP-910-005**.

The tests live in `tests/<framework>/`, one folder per adapter. Each folder holds
the adapter tests, with the gallery served under `/py`, and
`test_<framework>_project.py`, which creates the project with
`gramlot <framework> new` and serves it. `tests/uvicorn/test_uvicorn_tutorial.py`
serves `examples/`. `tests/test_readme.py`, `tests/test_cli.py` and
`tests/test_gallery.py` need no framework. Each folder runs with its own extra
only:

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
paired guides and builds both documentation views. Two more required jobs use
Playwright Chromium:

- `browser`: `scripts/verify_browser.mjs` serves a pages folder with each
  adapter under `/py` and the strict profile (the 301 of `/py`, an image of the
  `assets` map, the core theme, a Python page that takes its `Logic` from its
  page module); `scripts/verify_gallery_browser.mjs` starts
  `gramlot <environment> gallery` with and without `--mount /py` and opens the
  gallery, every example it links, the `Logic` of c03 and `<environment>-01`.
- `install`, one run per environment: `scripts/verify_install.py` installs the
  built wheel in a clean virtual environment, runs `gramlot <environment> new`,
  `pip install -r requirements.txt`, the printed start command and
  `gramlot <environment> gallery --mount /py`, and opens each page with
  `scripts/verify_url_browser.mjs`.

```sh
node scripts/verify_browser.mjs "$(command -v python)" "$PLAYWRIGHT_ENTRY" chromium webkit
node scripts/verify_gallery_browser.mjs "$(command -v python)" "$PLAYWRIGHT_ENTRY" chromium webkit
python -m build --wheel -o dist .
python scripts/verify_install.py django dist/gramlot_py_server-*.whl "$PLAYWRIGHT_ENTRY" chromium
```

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

Local verification, 2026-10-04, for 0.2.2 with `gramlot` 0.2.5,
`gramlot-examples` 0.2.5, `kajenn` 0.1.0, Django 6.1.1, Flask 3.1.3, FastAPI
0.142.2 and Uvicorn 0.54.0:

- the full suite passes, 69 tests, on Python 3.12.9 and 3.11.11;
- Playwright 1.63.0 with Chromium 153.0.8010.12 and WebKit 26.6:
  `verify_browser.mjs` 20/20 and `verify_gallery_browser.mjs` 20/20 (five
  environments, with and without `/py`, 34 examples under `/py`);
- `verify_install.py` for the five environments from the built wheel, with
  `--port 8123` because port 5000 is taken by AirPlay Receiver on macOS; Flask
  also without `--port`, with its printed command on port 8000.

The CI run 37184570774 of the branch `feat/gramlot-command` (2026-10-04) passed
the jobs `browser`, `install` (five environments), `repository`,
`documentation`, `core-main` and `published-core` on 3.12, and failed
`published-core` on 3.11: the theme `README.md` was `application/octet-stream`
there. Commit `155aa63` fixed it with `THEME_MEDIA_TYPES`.

Local verification, 2026-10-05, for 0.2.3 with `gramlot` 0.2.6,
`gramlot-examples` 0.2.5, `kajenn` 0.1.1, Django 6.1.1, Flask 3.1.3, FastAPI
0.142.2 and Uvicorn 0.54.0:

- the full suite passes, 74 tests, on Python 3.12.9 and 3.11.11; `ruff check`
  and `mypy src` pass;
- Playwright 1.63.0 with Chromium and WebKit: `verify_browser.mjs` 20/20 and
  `verify_gallery_browser.mjs` 20/20;
- `verify_install.py` for the five environments from the built wheel, with
  `--port 8123`, in Chromium.
