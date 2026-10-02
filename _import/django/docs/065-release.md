# 065 · Candidate verification and coordinated release

Document ID: **GD-065**.

Status: POC GitHub preview published; PyPI release preparation only.
The GitHub prerelease label identifies an experimental download, not the
reviewed prerelease planned after core and adapter consolidation.
Candidate versions are Gramlot 0.1.5 and gramlot-django 0.1.0. Project maturity
remains pre-alpha; the final version syntax allows normal pip selection.

<a id="gd-065-005"></a>

## 005 · Verify the exact candidate files

Block ID: **GD-065-005**.

Gramlot owns JavaScript compilation. Prepare its assets and browser distribution,
then build its Python wheel/sdist. Build this adapter separately. Keep the exact
verified files in a candidate directory and retain their SHA-256 hashes.

Test in a new environment using wheels, not editable checkouts:

```sh
python -m venv temp/consumer
# On Windows use temp/consumer/Scripts/python.exe instead.
temp/consumer/bin/python -m pip install --find-links temp/candidate-dist gramlot-django
python scripts/verify_installation.py --python temp/consumer/bin/python
```

Before publication, `temp/candidate-dist` must contain the tested core and adapter
wheels. Third-party dependencies resolve normally. This is a candidate rehearsal;
it does not prove a public-PyPI installation.

For the real browser gate, install the runner's optional browser tools separately:

```sh
python -m pip install '.[browser]'
python -m playwright install chromium
python scripts/verify_installation.py --python temp/consumer/bin/python --browser
```

The target environment contains only application dependencies. The runner copies
the quickstart outside both repositories, checks installed import paths, runs
`pip check`, starts Django with a PATH containing only its Python environment,
and verifies binding, Data RPC, remote Source and lazy CodeMirror, HTML and Markdown editor resources.
All off-site browser requests are blocked and reported as failures.

<a id="gd-065-010"></a>

## 010 · CI

Block ID: **GD-065-010**.

Adapter CI installs package dependencies; it does not clone core develop or build
JavaScript. It tests Python/Django combinations on Linux, with additional Windows
and macOS consumer smoke checks. The Linux Python 3.12 job runs the browser gate
and uploads the exact tested distributions.

Before core publication, manual CI dispatch can accept a core wheel HTTPS URL
and its SHA-256 checksum. Both are required together. After core publication,
leave those inputs empty so dependency resolution exercises PyPI.

The ordinary push/release gate cannot resolve an unpublished core from PyPI.
Run candidate verification first, then publish core, then validate/release the
adapter. Never replace this gate with a moving-branch source checkout.

<a id="gd-065-015"></a>

## 015 · Account configuration

Block ID: **GD-065-015**.

An owner with PyPI project access must configure these Trusted Publishers:

| PyPI project | GitHub owner | Repository | Workflow file | Environment |
| --- | --- | --- | --- | --- |
| gramlot | gramlot-org | gramlot | publish.yml | pypi |
| gramlot-django | gramlot-org | gramlot-django | publish.yml | pypi |

For the new project, configure a pending publisher if the project is not yet
registered. Configure GitHub environment reviewers for `pypi` in both repositories
and `release` in core before using the publication workflow. Inspection on 2026-09-15 found core `pypi` and `release` environments with no
protection rules and no adapter environment. PyPI publisher setup has not been
verified by writing these workflow files.

[PyPI Trusted Publishing documentation](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
explains the account-side configuration. No registry token belongs in Git.

<a id="gd-065-020"></a>

## 020 · Release sequence

Block ID: **GD-065-020**.

1. Review and select the complete commit set in core and the adapter. Preserve
   unrelated work; the current dirty core includes concurrent feature changes.
   Run required checks before commits/pushes. Confirm available version numbers.
2. Consolidate accepted changes onto main and create matching version tags. Both
   publication workflows require the selected tag to match package metadata and
   its commit to belong to main. Replace draft core release notes with the full
   reviewed release scope.
3. With owner authorization, manually dispatch the core publication workflow on
   its version tag. It publishes the verified Python distributions to PyPI and
   the matching browser ZIP/checksums to GitHub, subject to environment gates.
4. Confirm Gramlot 0.1.5 resolves from public PyPI in a fresh environment.
5. Remove the temporary sibling `tool.uv.sources` override, regenerate the adapter
   lock from PyPI, and verify ordinary adapter CI with no candidate URL. Commit
   and tag the final adapter state after checks.
6. Manually dispatch the adapter publication workflow on its version tag. It
   publishes the same wheel/sdist uploaded by the successful consumer test job.
7. In a fresh environment with no candidate directory or configured private index,
   run `python -m pip install gramlot-django` and `python -m pip check`, then repeat
   the documented project/browser check. Record installed versions and build ID.
8. Update release/status documents and public links after these checks succeed.

The workflows are manual and have not been triggered. If a job fails, inspect
which artifacts actually reached each service before retrying failed jobs. Never
replace existing files under an already published version. A faulty public
version requires an explicit corrected release/yank decision.

GitHub publication alone does not make the unqualified pip command work. The
final acceptance gate is public PyPI plus a working installed Django page.

<a id="gd-065-025"></a>

## 025 · Current direct dependency

Block ID: **GD-065-025**.

The GitHub POC declares a checksummed core wheel URL so source installs work without
an unavailable registry version. Replace this direct reference with a coordinated
registry dependency before any PyPI publication. The archived preview tag is unchanged.
