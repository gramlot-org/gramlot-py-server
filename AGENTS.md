# Gramlot Uvicorn integration repository instructions

Read `../gramlot/docs/00-constitution.md`, `../gramlot/docs/01-overview.md`,
`../gramlot/ports/README.md`, and `../gramlot/docs/005-documentation-policy.md`
before changing this repository. The Gramlot constitution is authoritative.

- Keep code and maintained documentation in English.
- This repository owns the framework-neutral ASGI adapter for Python/Uvicorn. It does not own
  Gramlot Source, Data Bags, Host, or the browser runtime.
- Never ship a substitute runtime. Fail if an accepted integration is unavailable.
- Only `application_data` crosses the JSON boundary through a typed Bag codec.
- Pair `docs` and `docs_llm` guides and preserve GS document/block IDs.
- Do not publish, release, deploy, push, or change visibility without authorization.

Origin: `gramlot-minimal@87bcd90`.
