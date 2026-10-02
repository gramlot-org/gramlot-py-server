# gramlot-fastapi

Read README.md and SPECIFICATION.md before working. This repository provides an
experimental FastAPI adapter for Gramlot.

## Code and repository practices

- Keep code and maintained documentation in English.
- Use main as the consolidated public baseline and develop for new development.
- Preserve copyright and Apache 2.0 notices.
- Keep secrets, virtualenvs, temporary files and local worktrees out of Git.
- Use Python-first Gramlot declarations for applications; expose framework gaps
  instead of bypassing them with application-local DOM, events or fetch calls.
- Keep FastAPI hosting separate from database adaptation. SQLAlchemy and Genropy
  (GnrApp) are independent optional profiles; plain hosting requires neither.
  Preserve host-independent facilities in Gramlot rather than duplicating them here.
- Run scripts/check.py before commits and pushes. Add behavior tests with
  implementation changes. Ruff and test failures block delivery; mypy is advisory.
- Do not add assistant co-author trailers to commit messages.
- Keep documentation aligned with implemented behavior; no speculative API claims.
- Do not introduce automatic package publication or deployment without authorization.

## Documentation

Follow [the documentation policy](docs/015-documentation.md) and its
[concise counterpart](docs_llm/015-documentation.md).

- Use three-digit guide filename prefixes initially spaced by five (005, 010,
  015); insert in gaps without renumbering established identities.
- Mirror paths and folders between docs and docs_llm, updating both views together.
- Use the GF repository namespace for document IDs and level-two block IDs.
  Both views share logical IDs and explicit lowercase HTML anchors.
- Keep IDs repository-wide across folders. Preserve IDs and anchors when moving
  or reordering content; never reuse retired IDs. Update links after moves.
- Exempt entry points, configuration, requirements, assets and historical exports
  from guide numbering.
- Record mirror and migration gaps in the documentation policy. Add missing
  mirrors on substantial revision. New architecture and product-contract guides
  require both views. Preserve status, constraints, limitations and open questions.
- Keep navigation and references current, and run the documentation checks.
- Public documentation defaults to main. New work stays on develop until
  verified and accepted; this does not authorize releases or deployment.

## Documentation appearance

Use Sphinx with sphinx_rtd_theme: blue header, dark sidebar, light content and
standard theme typography. Preserve the Gramlot logo and accurate experimental
status notices. This applies to documentation; application UI is separate.


## Accepted native 0.1.0 release — 2026-09-24

The owner accepted the bounded clean-core native profile and authorized GitHub
archive distribution. This supersedes earlier PoC-only direction for this profile.
Use the native exports and documented Hello World launchers. Legacy Page/recipe/RPC
modules, CLIs and database demos remain historical and are not clean-core aliases.
`scripts/check.py` runs Ruff, the native protocol suite and documentation checks;
PoC-only suites require their own compatible environment and do not define the
native release gate. Preserve those tests; do not skip failures in the native suite.
CI builds the current core from main with its declared floating dependencies.
No PyPI/npm publication or application deployment is authorized.
