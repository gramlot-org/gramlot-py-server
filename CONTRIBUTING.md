# Contributing

## Setup

```sh
python -m venv .venv
.venv/bin/pip install "gramlot>=0.2.12" -e ".[uvicorn,django,flask,fastapi,kajenn,gallery,test]"
.venv/bin/pip install ruff mypy      # lint and type checks, configured in pyproject.toml
.venv/bin/pip install -e ".[docs]"   # documentation only
git config core.hooksPath hooks
```

To test against the core `main` branch, place a `gramlot` checkout beside this
repository, build its runtime (`npm --prefix js install && npm --prefix js run build`)
and install it in editable mode: `.venv/bin/pip install -e ../gramlot`.

## Checks before a commit

```sh
.venv/bin/python -m pytest -q                  # every adapter and the README
.venv/bin/python -m pytest -q tests/django     # one adapter
.venv/bin/ruff check .
.venv/bin/mypy src
.venv/bin/python scripts/check_docs.py         # when documentation changes
```

CI installs each adapter with its own extra only and runs `tests/<framework>`;
a test that needs another framework fails there. CI does not run `ruff` and
`mypy`: run them before a commit.

Browser checks, with Node.js 22 and Playwright (`PLAYWRIGHT_ENTRY` is the path of
`playwright/index.mjs`); CI runs them in Chromium (GP-910):

```sh
node scripts/verify_browser.mjs .venv/bin/python "$PLAYWRIGHT_ENTRY" chromium webkit
node scripts/verify_gallery_browser.mjs .venv/bin/python "$PLAYWRIGHT_ENTRY" chromium webkit
.venv/bin/python -m build --wheel -o dist .
.venv/bin/python scripts/verify_install.py django dist/gramlot_py_server-*.whl "$PLAYWRIGHT_ENTRY"
```

`verify_install.py` runs the start command that `gramlot new` prints; add
`--port PORT` when that port is in use on your machine.

## Documentation

- Published guides, paired in `docs_llm/`, namespace GP: `docs/005-…` to
  `docs/020-…` common, `docs/105-…` to `docs/120-…` Uvicorn, `docs/205-…`
  Django, `docs/305-…` Flask, `docs/405-…` FastAPI, `docs/505-…` Kajenn.
  Internal notes: `docs/internal/` and `docs_llm/internal/`.
- The README quick start is the templates of `gramlot <framework> new` in
  `src/gramlot_py_server/templates/`; `tests/test_readme.py` fails when the
  README blocks and the templates differ. `examples/` holds the pages of the
  Uvicorn tutorial (GP-105).

## Commits and branches

- New work on `develop`; `main` holds verified, owner-accepted work.
- Messages: `<type>: <subject>`, present tense, English. Types: `feat`, `fix`,
  `docs`, `refactor`, `test`, `build`, `ci`, `chore`.
- Use `git switch`, never `git checkout`. Never force-push a pushed branch:
  fixes land as new commits.
- No AI, LLM or assistant references in commits, pull requests, code, comments
  or documents; no assistant `Co-Authored-By` trailers; no `Generated with …`
  lines. `hooks/commit-msg` rejects the usual forms.

## Releases

Only with owner authorization. A release is the tag `vX.Y.Z` on `main`, with
`version` in `pyproject.toml` equal to it and `.github/release-notes/vX.Y.Z.md`
present; the workflow `Publish release` (`.github/workflows/publish.yml`), run
by hand on the tag, tests, builds, creates the GitHub release and uploads to
PyPI with trusted publishing.
