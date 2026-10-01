# Contributing

## Setup

```sh
python -m venv .venv
.venv/bin/pip install "gramlot>=0.2.0" -e ".[uvicorn,test]"
.venv/bin/pip install -r requirements-docs.txt   # documentation only
git config core.hooksPath hooks
```

## Checks before a commit

```sh
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_docs.py   # when documentation changes
```

## Documentation

- Published guides: `docs/105-…` to `docs/140-…`, paired in `docs_llm/`,
  written for a user of the adapter. Internal notes and verification records:
  `docs/internal/` and `docs_llm/internal/`.
- The README quick start is `tests/pages/hello.py`; `tests/test_examples.py`
  fails when the README block and the file differ.

## Commits and branches

- New work on `develop`; `main` holds verified, owner-accepted work.
- Messages: `<type>: <subject>`, present tense, English. Types: `feat`, `fix`,
  `docs`, `refactor`, `test`, `chore`.
- Use `git switch`, never `git checkout`. Never force-push a pushed branch:
  fixes land as new commits.
- No AI, LLM or assistant references in commits, pull requests, code, comments
  or documents; no assistant `Co-Authored-By` trailers; no `Generated with …`
  lines. `hooks/commit-msg` rejects the usual forms.

## Releases

Only with owner authorization. The package is not published on PyPI yet.
