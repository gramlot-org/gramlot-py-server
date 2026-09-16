# Contributing to gramlot-flask

Run `uv sync --extra dev --extra docs`, then `git config core.hooksPath hooks`.
Use `develop` for new development and keep changes focused on SPECIFICATION.md.

Before a commit or push, run `uv run python scripts/check.py` and inspect
`git diff --check`. Run `uv run mypy src/` as a non-blocking advisory check.
Validate distribution changes with `uv run python -m build` and
`uv run python -m twine check dist/*`.

Add real host and application behavior tests with the first implementation;
do not substitute mocks for available integration infrastructure. The initial
scaffold has no application behavior and no claimed application test coverage.
Document public behavior and runtime dependencies in the same change.

Keep code, documentation and commit messages in English. Use focused conventional
commit messages and preserve Softwell copyright; do not add assistant authorship
trailers. Contributions are licensed under Apache 2.0.
