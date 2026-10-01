# gramlot-uvicorn repository instructions

Read `../gramlot/docs/00-constitution.md`, `../gramlot/docs/01-overview.md`,
`../gramlot/ports/README.md` and `../gramlot/docs/005-documentation-policy.md`
before changing this repository. The Gramlot constitution is authoritative.

- This repository owns the framework-neutral ASGI adapter for Python/Uvicorn.
  It does not own Gramlot Source, Data Bags, Host or the browser runtime.
- Depend on the released core only: `gramlot>=0.2.0` from PyPI. The `core-main`
  CI job, which installs the core from `main`, is the only exception.
- Never ship a substitute runtime. Fail if an accepted integration is unavailable.
- Only `application_data` crosses the JSON boundary through a typed Bag codec.
- Serve companions with the `FileHost.url` rule only: `.css` and `_aux.js`
  files whose real path is below the pages folder.
- Keep code, comments and maintained documentation in English.
- Pair `docs` and `docs_llm` guides; namespace **GS**; shared document IDs,
  block IDs and lowercase anchors. Run `python scripts/check_docs.py` after
  changing documentation.
- Before a commit: `python -m pytest -q`.
- Use `develop` for new work; `main` holds verified, owner-accepted work.
- Git: `git switch`, never `git checkout`; never force-push a pushed branch;
  commit messages `<type>: <subject>` in English.
- **No AI, LLM or assistant references anywhere**: not in commits, pull
  requests, code, comments or documents. Never add `Co-Authored-By` trailers
  for assistants or `Generated with …` lines. This is a contractual
  obligation. `hooks/commit-msg` blocks the usual forms.
- Do not publish, release, tag, deploy or change visibility without owner
  authorization.

Origin: `gramlot-minimal@87bcd90`.
