# 070 · Django extraction — 2026-09-15

Document ID: **GD-070**.

The adapter now belongs to `gramlot_django`. This is a local migration from the
sibling Gramlot checkout, preserving its existing working changes.

<a id="gd-070-005"></a>

## 005 · Transferred ownership

Block ID: **GD-070-005**.

- Seven Python modules from `src/gramlot/contrib/django`.
- The real Django adapter test suite, now requiring Django instead of skipping.
- All 492 tracked Django example files, including Bakery's license, media and SQL dump.
- Django guide and offline handbook. The duplicate core manual entry now points
  to this repository; dated core development/context records remain historical.

Subsequent distribution work exposes the shared contract through `gramlot.hosting`
and `gramlot.transport`; see [release procedure](065-release.md) for current checks.

The old core package modules, test file, example files and Django extra are
removed. Applications import `gramlot_django`; the core retains WebPage,
Source/Data services, shared host utilities and JavaScript runtime.

Local virtual environments and running presentation services are separate from
tracked source: this migration does not replace their installed packages or
restart them. The existing workspace launcher still uses its prepared historical
Bakery environment. The migrated example has its own setup instructions.

<a id="gd-070-010"></a>

## 010 · Original extraction verification

Block ID: **GD-070-010**.

- 26 Django behavior cases pass in this repository's Python 3.12 environment.
- 26 cases pass against the installed adapter wheel and installed core in an
  independent Python 3.14 environment.
- 36 selected core regression cases pass: FastAPI, Genropy, shared page services,
  Data RPC and browser-distribution contracts.
- Ruff, strict Sphinx documentation and package metadata validation pass.
- Both the customer example and Bakery pass Django system checks.
- Bakery's public explorer and recipe return HTTP 200 using a fresh database
  restored from the supplied dump, with 11 published breads.
- Mypy remains advisory and reports missing Django typing information and
  inherited typing issues. It is not a clean typing result.

These original checks did not include a new interactive browser test or a full
core regression run. Subsequent distribution verification is recorded in
[candidate verification](085-candidate-verification.md). Historical verification claims in the offline handbook retain
their original scope and dates.

<a id="gd-070-015"></a>

## 015 · Coordinated dependency changes

Block ID: **GD-070-015**.

Only Gramlot 0.1.0a1 was available on PyPI at inspection. This adapter requires
the current local 0.1.5 core APIs, so development uses an explicit sibling source
override. The extraction initially used a separate core `develop` checkout in CI.
The subsequent distribution change replaces it with installed packages and an
optional checksummed candidate wheel. The local unpublished changes have not been pushed,
and remote CI has not been verified for this migration.

A compatible core release is needed before an index-only installation can work.
No package publication, commit, push or deployment is part of this extraction.
