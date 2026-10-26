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
  gallery, every example it links, the `Logic` of c03 and the absence of environment quick-start routes.
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


Local database-selector development verification, 2026-10-18: connected core and
Python server sources, SQLAlchemy 2.1.5 with SQLite. Server suite: 117 passed,
including registered projection/filter boundaries and the environment catalog.
The five gallery fixtures now activate the same inputs/layout collections as
run_gallery. Live Python gallery checks cover typed keys, key resolution, dependent
filters, dedicated methods, invalid drafts, free text and sole-candidate selection.
GP-025 documents the unreleased increment; core GC-070 §1425 records combined
qualification. Browser/SQL tests do not claim support for other database engines.


Development verification, 2026-10-20 — Gallery staging now creates parent directories for filesystem routes and stages index_aux.js re-exporting the ordinary gallery Logic. The Python gallery/staging and core index checks pass (34 focused tests), and live Chromium/WebKit checks pass under Uvicorn for nested directories, own index pages and retained tabs.


<a id="gp-910-015"></a>

## 015 · Numbered gallery paths — 2026-10-21

Block ID: **GP-910-015**.

Owner explicitly authorizes connected catalogue and staging changes: “Sì, adegua anche le integrazioni”. Gallery catalogues require the physical family `folder`; each executable route is staged at its nested `url`, with its companions. Catalogue keys remain lesson identities. Hosted carousel links include the mount path; offline links include the route depth. Numbered path segments, including `00-index`, are supported by the static exporter without accepting traversal or empty segments. Markdown directory descriptions are supplied by the examples navigation and rendered by the gallery. No core loader change, route alias, release or deployment is included.

Verification: nine gallery catalogue/staging tests pass, including mounted paths. Both documentation builds pass. Live Uvicorn gallery checks confirm numbered navigation, executable and Markdown indexes, nested lesson URLs and retained Python source display.


Intermediate release qualification — 2026-10-21. Owner authorizes tree, pages, gallery and guide only, including the necessary connected integrations. All 126 tests pass. Chromium passes all 84 common lessons under /py and the root gallery/Logic check on Uvicorn, Django, Flask, FastAPI and Kajenn. Both documentation views build without warnings. Database selectors and Genropy experiments are excluded. Package publication is pending at this checkpoint.


Clean-install verification follow-up — 2026-10-21. The wheel installation check now obtains the e01 route from the installed examples catalogue instead of the retired short URL. A fresh Uvicorn virtual environment, generated project and mounted gallery pass Chromium against the published core and examples packages. The same script is exercised for all five frameworks by CI.


Publication receipt — 2026-10-21. Release v0.2.12 passed all required repository and tag checks and is published on PyPI. The five framework matrices, clean wheel installations, generated projects and gallery browser checks pass. Publication workflow: https://github.com/gramlot-org/gramlot-py-server/actions/runs/39575513271 . Hosted gallery promotion has its own deployment receipt.


Coordinated 0.3.17 qualification — 2026-10-26. Owner explicitly requested aligned
publication of the servers with core and examples. All 154 adapter tests pass
against the prepared 0.3.17 candidate; both documentation views build. Gallery
asset tests use the transparent branding path supplied by the core. Remote Edit
remains disabled by default; the Kajenn HEAD Content-Length debt is unchanged.
Registry publication is pending.
