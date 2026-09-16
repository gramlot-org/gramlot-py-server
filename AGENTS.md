# gramlot-flask repository instructions

Read README.md and SPECIFICATION.md before changing this repository. Read the
Gramlot constitution, overview and port protocol in the sibling `../gramlot`
repository; the constitution is authoritative.

- Keep code and maintained technical documentation in English.
- Use `develop` for new work; consolidate verified, owner-accepted work into `main`.
- Keep Flask dependencies and request integration here, never in Gramlot core.
- Plain hosting must not require a database; SQLAlchemy remains an independent
  database adapter. Do not implement a second SQLAlchemy adapter here.
- Write applications in Python using Gramlot Source, Data Bags, bindings,
  controllers, resolvers and shared components. Expose framework gaps rather than
  using application-local DOM construction, event wiring, input scraping or fetch.
- Do not infer Live Object Tree semantics. Review PoC evidence through bounded
  ports; do not bulk-copy it or claim accepted contracts from experimental code.
- Pair `docs` and `docs_llm` guides; use three-digit filenames spaced by five,
  namespace GFL, shared stable document/block IDs and explicit lowercase anchors.
- Use the classic `sphinx_rtd_theme`, the Gramlot logo and accurate status notices.
- Run `scripts/check.py` before commits/pushes. Ruff, documentation and actual
  test failures block delivery; mypy is advisory. Add behavior tests with runtime
  implementation; preserve the existing Flask/Microblog behavior coverage. Keep bundled upstream
  source unchanged, retain its MIT notice, and record revision updates.
- Preserve Apache 2.0 and copyright notices. Keep secrets and environments out of
  Git. Do not add assistant co-author trailers.
- Do not publish packages, releases or applications without owner authorization.
