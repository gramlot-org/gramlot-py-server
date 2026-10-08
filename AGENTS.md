# gramlot-py-server repository instructions

Read `../gramlot/docs/00-constitution.md`, `../gramlot/docs/01-overview.md`,
`../gramlot/ports/README.md` and `../gramlot/docs/005-documentation-policy.md`
before changing this repository. The Gramlot constitution is authoritative.

The repository publishes one PyPI package, `gramlot-py-server`, with one adapter
module per framework in `src/gramlot_py_server/`: `uvicorn.py`, `django.py`,
`flask.py`, `fastapi.py` and `kajenn.py`. Each module imports only its own
framework, which arrives with the extra of the same name.

## Rules common to every adapter

- The repository owns HTTP routing, payload parsing, response mapping and
  request identity for each framework. It does not own Gramlot Source, Data
  Bags, `GramlotServer` or the browser runtime.
- Depend on the released core only: `gramlot>=0.2.12` from PyPI. The `core-main`
  CI job, which installs the core from `main`, is the only exception. Never
  copy the core into this repository.
- Every adapter keeps the same contract: the core `GramlotFileServer` with root-relative
  URLs, the mount path passed to `open_page` and carried by the request path
  (404 outside it, 301 from `/py` to `/py/`), the companions rule (`GET` and
  `HEAD` of `.css` and `.js` files whose real path is below the pages folder),
  `<path>/index.html` opening the page `<path>` and `/index.html` the index,
  the core themes at `/themes/…`, the `assets` option, the owner cookie `gramlot_owner`, the 4096-byte request
  limit and the `content_security_policy` option with `{nonce}`. A change to one adapter's
  contract is made in all five, with its tests. The server protocol GC-230 of
  the core prevails: `tests/<framework>/test_<framework>_conformance.py` runs
  the core `check_protocol` on each adapter started with its `serve`.
- Never ship a substitute runtime. Fail if an accepted integration is unavailable.
- No database adapters in this release; they come in the next cycle under
  `gramlot_py_server/db/<engine>.py`.
- Keep code, comments and maintained documentation in English.
- Pair `docs` and `docs_llm` guides; namespace **GP**; shared Document and
  Block IDs and lowercase anchors; three-digit filenames spaced by five.
  Published guides: `005`–`020` common, `105`–`120` Uvicorn, `205` Django,
  `305` Flask, `405` FastAPI, `505` Kajenn. Internal notes `905` and `910` live
  in `docs/internal/` and `docs_llm/internal/`, out of the published build.
  Document IDs are never reused: new guides take new numbers. A guide derived
  from an archived adapter carries the line "Derived from <ID> (<repository>)";
  the archived namespaces GD, GFL, GF and GA are frozen. A guide derived from
  gramlot-uvicorn carries "Derived from a guide of the archived gramlot-uvicorn
  repository." without an ID: the namespace GS belongs to the serverless guides
  of gramlot-js-server. Run `python scripts/check_docs.py` after changing
  documentation.
- The README quick start shows the templates of `gramlot <framework> new`
  (`src/gramlot_py_server/templates/`); `tests/test_readme.py` fails when they
  differ, and `tests/<framework>/test_<framework>_project.py` creates and serves
  each project. Change the README and the templates together. `examples/` holds
  the pages of the Uvicorn tutorial.
- The command `gramlot <environment> <verb>` (`cli.py`) loads the entry point of
  the group `gramlot_py_server.commands` named by the environment: the function
  `commands(verbs)` of each adapter module adds its verbs.
- Before a commit: `python -m pytest -q` with every extra installed.
- Use `develop` for new work; `main` holds verified, owner-accepted work.
- Git: `git switch`, never `git checkout`; never force-push a pushed branch;
  commit messages `<type>: <subject>` in English.
- **No AI, LLM or assistant references anywhere**: not in commits, pull
  requests, code, comments or documents. Never add `Co-Authored-By` trailers
  for assistants or `Generated with …` lines. This is a contractual
  obligation. `hooks/commit-msg` blocks the usual forms.
- Do not publish, release, tag, deploy or change visibility without owner
  authorization.

## History

The repository starts from the history of `gramlot-uvicorn` (`main`,
`9723fa2`). On 2026-10-02 the owner merged into it, with `git subtree`, the
histories of `gramlot-django` (`beeb3f6`), `gramlot-flask` (`3bb86a0`),
`gramlot-fastapi` (`02fda99`) and `gramlot-kajenn` (`7e73de2`); the merge
commits name each source. Only each adapter module and its tests entered; the
parts that depend on a database and the proof-of-concept code stayed out and
are listed in the commit that removed them. `git log <merge>^2 -- <old path>`
shows the history of a file before the merge. Historical names are not
compatibility aliases.
