# Contributing to gramlot-kajenn

Use `develop` for new work. Install current Gramlot core, gramlot-minimal and
this checkout with test and documentation dependencies, refreshing first-party
dependencies during setup. Do not commit first-party lockfiles or pins.

Before committing, run `python scripts/check.py` and `git diff --check`.
Build distributions with `python -m build` and check them with
`python -m twine check --strict dist/*`. Mypy is advisory.

Native tests cover the real Kajenn server. The old PoC host, CLI and examples
are historical and require an older Gramlot API. Do not present them as native
examples or add clean-core compatibility layers for them.

Keep code and maintained documentation in English. Preserve Softwell copyright
and Apache 2.0 notices; do not add assistant authorship trailers. No automatic
package publication or deployment is authorized.
