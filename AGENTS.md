# gramlot-genro-asgi

Read README.md and SPECIFICATION.md before working. This is a pre-alpha
experimental Genro ASGI host with optional legacy GnrApp lifecycle integration.

- Keep code and maintained documentation in English.
- Use main for the baseline and develop for new development.
- Preserve copyright and Apache 2.0 notices.
- Keep secrets, virtualenvs, temp files and local worktrees out of Git.
- Use Python-first Gramlot declarations for applications; expose framework gaps
  instead of bypassing them with application-local DOM, events or fetch calls.
- Keep Genro ASGI hosting in this consumer repository or its host integration. Do not introduce a Genro ASGI dependency into the Gramlot core. Review the existing genro-asgi[gui] integration before designing application hosting.
- Run scripts/check.py before commits/pushes; add behavior tests with implementation.
- Ruff and test failures block delivery; mypy is advisory.
- Do not add assistant co-author trailers to commit messages.
- Keep documentation aligned with implemented behavior; no speculative API claims.
- Do not introduce automatic package publication or deployment without authorization.


## Current implementation direction — 2026-09-16

Prioritize Genro ASGI + legacy GenroPy; SQLAlchemy is deferred. Read the paired
GA-005 contract. Use the experimental sibling PoC experimentally; never claim that the
clean core already provides a runtime. Keep public/consolidated work on main and
new work on develop. Documentation uses classic sphinx_rtd_theme and paired
GA document/block IDs. Record actual compatibility and test skips.
