# gramlot-django

Read README.md and SPECIFICATION.md before working. This repository contains
the native Django Host adapter and a preserved PoC archive. Read
docs/090-native-html.md for the current installable scope.

- Keep code and maintained documentation in English.
- Use main for the baseline and develop for new development.
- Preserve copyright and Apache 2.0 notices.
- Keep secrets, virtualenvs, temp files and local worktrees out of Git.
- Use Python-first Gramlot declarations for applications; expose framework gaps
  instead of bypassing them with application-local DOM, events or fetch calls.
- Maintain the native adapter under gramlot_django and use standard Django project conventions.
- Keep server-independent page services and browser runtime in Gramlot; verify core compatibility.
- Native development uses the current Gramlot core without first-party pins;
  the old gramlot-poc adapter and tests are historical.
- Run scripts/check.py before commits/pushes; add behavior tests with implementation.
- Ruff and test failures block delivery; mypy is advisory.
- Do not add assistant co-author trailers to commit messages.
- Keep documentation aligned with implemented behavior; no speculative API claims.
- Do not introduce automatic package publication or deployment without authorization.

## Architecture and paired documentation

- Read the Gramlot product constitution and overview in the sibling `gramlot`
  repository before architecture changes; use `gramlot-poc` for experimental evidence.
- Keep server adaptation separate from database/ORM adaptation, including Django's two roles.
- Treat the native adapter as local development until acceptance; the old
  downloadable preview is historical, not a native compatibility claim.
- Follow docs/055-documentation.md: update paired docs/<path> and docs_llm/<path> together,
  preserving decisions, constraints, status and open questions. New architecture and
  product-contract documents require both views. Existing unpaired guides are tracked
  by that policy; do not claim complete mirror coverage.

- Number maintained guides in steps of five; mirror paths and stable GD document/block
  IDs between docs and docs_llm. Preserve IDs across moves; follow docs/055-documentation.md.


## Shared documentation theme — owner directive, 2026-09-16

All Gramlot documentation sites use the classic Read the Docs theme shown by
Genro Bag: blue header, dark sidebar, light content and default theme typography.
Use sphinx_rtd_theme for Sphinx (readthedocs for MkDocs). Preserve the Gramlot
logo and accurate status notices. This supersedes prior Furo/Material choices;
see ../gramlot/docs/005-documentation-policy.md and constitution section 9.
This rule also applies to future documentation sites; application UI is separate.
