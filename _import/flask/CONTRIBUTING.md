# Contributing to gramlot-flask

Run `uv sync --extra dev --extra docs`, then `git config core.hooksPath hooks`.
Use `develop` for new development and keep changes focused on SPECIFICATION.md.

Before a commit or push, run `python scripts/check.py` and inspect
`git diff --check`. Run `python -m mypy src/` as a non-blocking advisory check.
Validate distribution changes with `python -m build` and
`python -m twine check dist/*`.

Add real host and application behavior tests with the first implementation;
do not substitute mocks for available integration infrastructure. Keep installed-wheel and plain-host isolation checks alongside the demo tests.
Document public behavior and runtime dependencies in the same change.

Keep code, documentation and commit messages in English. Use focused conventional
commit messages and preserve Softwell copyright; do not add assistant authorship
trailers. Contributions are licensed under Apache 2.0.

Native 0.1.0 checks and Git hooks use the active Python environment. Install the
release core wheel and this adapter with its dev/docs extras there first; refresh
first-party dependencies during setup/update. Do not use a frozen PoC environment
or commit dependency lockfiles that pin first-party packages. Missing native core
imports fail collection rather than skipping the release tests.
