# Building and hosting the documentation

Document ID: **GF-030**.

[Expanded counterpart](../docs/030-readthedocs.md).

<a id="1-build-and-theme"></a>
<a id="gf-030-005"></a>

## 005 · Build and theme

Block ID: **GF-030-005**.

- Sphinx + MyST + sphinx_rtd_theme; Gramlot logo, blue header, dark sidebar, light content, POC notice.
- Version from pyproject.toml; no FastAPI/core/adapter installation needed.
- Install `docs/requirements.txt`; build:
  `python -m sphinx -n -W --keep-going -b html docs docs/_build/html`.
- Warnings and unresolved references fail; preview `docs/_build/html/index.html`.

<a id="2-ci"></a>
<a id="gf-030-010"></a>

## 010 · CI

Block ID: **GF-030-010**.

- Documentation workflow: main/develop/codex pushes, PRs to main/develop, manual dispatch.
- Docs-only dependencies; `documentation-html` artifact. Regular checks also build docs.
- Verification only: Actions workflow does not publish a site.

<a id="3-read-the-docs"></a>
<a id="gf-030-015"></a>

## 015 · Read the Docs

Block ID: **GF-030-015**.

- `.readthedocs.yaml`: Ubuntu 24.04, Python 3.12, docs requirements/conf, warnings fatal.
- Maintainer imports GitHub repo, selects main, enables versions and verifies webhook/build.
- External project connection remains separate;
  no live site claimed until a hosted build succeeds. Canonical URL comes from RTD environment.

<a id="4-maintenance"></a>
<a id="gf-030-020"></a>

## 020 · Maintenance

Block ID: **GF-030-020**.

- Update paired guides together; see [policy](015-documentation.md) for incomplete mirror coverage.
- Separate POC records from user navigation; synchronize docs requirements and pyproject extra.
- Official RTD/theme references are in the expanded guide.
