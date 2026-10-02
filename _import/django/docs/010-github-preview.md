# 010 · Install the experimental preview

Document ID: **GD-010**.

This download is a POC under review, not the forthcoming consolidated prerelease.
Gramlot itself is being reviewed and consolidated; see [repository roles](005-overview.md).

This GitHub prerelease pairs gramlot-django 0.1.0 with a compatible Gramlot 0.1.5
candidate. Neither version is published on PyPI as part of this release.

<a id="gd-010-005"></a>

## 005 · Installation

Block ID: **GD-010-005**.

Create and activate a Python 3.11+ virtual environment, then run:

```sh
python -m pip install 'git+https://github.com/gramlot-org/gramlot-django.git@main'
gramlot-django demo --open
```

This one-command installation from `main` automatically resolves the core wheel
from GitHub, including its SHA-256 pin. Git is needed; Node.js and sibling core
checkouts are not. The package version `gramlot==0.1.5` identifies the supplied
experimental snapshot, not an available tag in either core source repository.
The clean `gramlot` repository is not yet the installable product; development
experiments live in `gramlot-poc`.

The older adapter tag `v0.1.0-preview.1` does not declare this direct dependency.
To reproduce that archived preview, download and install **both** wheels attached
to its release. For the current usable POC, use the command above.

These previews evaluate API and design choices. Described behavior is intended
behavior; bugs and unfinished cases may exist. Passing checks cover specific
scenarios and are not a bug-free guarantee. Polls is bundled; Bakery needs the
separate repository example and Wagtail dependencies; see [Bakery](025-bakery-demo.md).

<a id="gd-010-010"></a>

## 010 · Artifact provenance

Block ID: **GD-010-010**.

The Gramlot core wheel and matching source archive are the locally built candidate
used to verify the Bakery inspector theme correction on 2026-09-15. They are
provided here to make the extracted adapter installable while the coordinated
core release is pending. This does not publish or tag the core repository's
other ongoing development. `SHA256SUMS` covers every attached distribution.
The archived adapter artifacts correspond to the preview tag. Current source
installation follows `main`; use its full commit SHA for reproducibility.

This is an experimental preview. The demo server is for local development.

<a id="gd-010-015"></a>

## 015 · Verification

Block ID: **GD-010-015**.

The preview was checked with Python 3.12 in a fresh environment using the attached
wheels: Django system checks and nested runtime delivery pass without editable
checkouts. The installed Polls demo is also exercised in Chromium with external
requests blocked. Repository checks include Ruff, 33 behavior tests and strict
Sphinx documentation builds.
