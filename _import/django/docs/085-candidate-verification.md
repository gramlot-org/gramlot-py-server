# 085 · Distribution candidate verification — 2026-09-15

Document ID: **GD-085**.

<a id="gd-085-005"></a>

## 005 · Candidate and scope

Block ID: **GD-085-005**.

Gramlot 0.1.5 and gramlot-django 0.1.0 are local candidates, not a public release.
The Django adapter, examples and maintained guides are extracted; generic Python
services and the complete browser runtime remain in Gramlot. FastAPI consumes
the same public hosting/transport contract.

The working trees contain concurrent development. These results concern the
local candidate files; they do not identify an approved release commit set.

<a id="gd-085-010"></a>

## 010 · Checks

Block ID: **GD-085-010**.

- Django: 33 tests, Ruff and Sphinx with warnings treated as errors pass.
- Core: 161 Python tests pass with the CI client-module configuration.
- JavaScript: 422 tests pass, including the local editor dependency graph and
  Jodit plugin registration regression.
- FastAPI: 45 tests pass, 2 optional/environment cases skip.
- Changed shared Python code passes Ruff.
- The installed-wheel Django project passes with Python 3.12 and Django 6.0.8,
  DEBUG=False and nested mounting. Its environment contains neither editable
  checkouts, FastAPI nor Wagtail, and `pip check` passes.
- The real browser verifies initial rendering, binding, Data RPC, remote Source
  and CodeMirror, Markdown and Jodit (including plugin toolbar controls) while
  blocking all off-site requests. The server PATH contains
  only the consumer Python environment, with no Node/npm.

- The installed `gramlot-django demo polls` console command starts outside the
  checkout, migrates and seeds SQLite, and passes the offline browser vote/reload
  test across ordinary Django pages and the embedded SPA. The package includes the demo; Bakery has a separate project-aware launcher and optional dependencies.
- Browser build ID: `83610a8307c07647`.
- Core wheel and standalone browser ZIP contain 204 identical files.
- Core wheel builds from its sdist with Node absent from PATH.
- Core and adapter package metadata pass strict Twine validation.
- Core hosting documentation passes strict Sphinx validation.
- The toolbar regression fails against the earlier wheel missing Jodit plugins
  and passes against the corrected candidate.

Candidate artifacts and `SHA256SUMS` are retained in the local ignored
`temp/candidate-dist/` directory. These files are not published artifacts.

<a id="gd-085-015"></a>

## 015 · Remaining release work

Block ID: **GD-085-015**.

1. Review the combined core release scope and create the release commits/tags.
2. Configure PyPI Trusted Publishers and GitHub release environments.
3. Run the prepared remote CI matrix; local checks do not establish Linux,
   Windows or all Python/Django combinations.
4. Publish core, remove the temporary local development override and regenerate
   the adapter lock from PyPI, then validate and publish the adapter.
5. Verify `pip install gramlot-django` in a new environment using public PyPI only.

GitHub inspection found existing core `pypi` and `release` environments without
protection rules; the adapter has no release environment yet. PyPI publisher
configuration remains unverified and requires account access.

See [release procedure](065-release.md) for the exact manual sequence. No publication,
commit, push or deployment has been performed by this task.
