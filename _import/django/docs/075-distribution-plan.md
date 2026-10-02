# 075 · Plan: install Gramlot Django with one pip command

Document ID: **GD-075**.

Status: implementation in progress, 2026-09-15, following owner authorization.
This document retains the acceptance plan; see [release procedure](065-release.md)
for candidate installation and the remaining publication gates. Earlier
migration results are baselines, not acceptance of the final public release.

<a id="gd-075-005"></a>

## 005 · Implementation status

Block ID: **GD-075-005**.

The adapter has been extracted and uses the public core hosting/transport API.
Candidate wheels include the complete local browser dependency graph, including
lazy editors. The external-project browser gate passes with off-site requests
blocked. Package-based CI and manual publication workflows are prepared.

Still pending: the final reviewed release commit set, remote CI matrix execution,
PyPI publisher configuration and publication, removal of the temporary development
source override after core publication, and the final public-index installation.
See [candidate verification](085-candidate-verification.md) for measured local results.

<a id="gd-075-010"></a>

## 010 · Target developer experience

Block ID: **GD-075-010**.

In a fresh supported Python environment:

```sh
python -m pip install gramlot-django
python -m pip check
```

This installs Django, compatible Gramlot Python APIs and the complete compiled
browser runtime through ordinary package dependencies. No Git checkout, uv,
Node, npm, GitHub token, custom package index, `--pre`, separate asset download
or JavaScript build is required. Installing libraries does not create a Django
project, choose its database or install the Bakery/Wagtail demonstration.

The developer then uses normal Django project conventions: create or reuse a
project, mount a page collection in its URLconf and write a Python DjangoPage.
A documented minimal page must render and execute a Source/Data RPC with the
installed packages. No CDN or external runtime download is needed after setup.

<a id="gd-075-015"></a>

## 015 · Agreed distribution boundary

Block ID: **GD-075-015**.

| Deliverable | Owner | Distribution |
| --- | --- | --- |
| Python core and complete browser payload | Gramlot | `gramlot` wheel on PyPI |
| Django server, database and page integration | gramlot-django | `gramlot-django` wheel on PyPI |
| Standalone browser payload | Gramlot | Matching ZIP and checksums on GitHub Releases |
| Project configuration and business pages | Consumer | Normal Django application |

Build/minify JavaScript only in Gramlot's build pipeline. Include modules,
chunks, startup code, inspector/editor resources, required CSS/assets, browser
dependencies, manifest and license notices. The ZIP and Python package must
contain the same payload. Django serves the installed assets through its
existing runtime URLs by default; production static offloading is optional and
must not become a prerequisite for the first page.

Do not add an installation hook that downloads JavaScript from GitHub. pip's
normal package dependency resolution supplies the runtime through `gramlot`.

<a id="gd-075-020"></a>

## 020 · Initial gaps observed before implementation

Block ID: **GD-075-020**.

- `gramlot-django` is `0.0.0.dev0` and requires local `gramlot==0.1.5` through
  `tool.uv.sources`. Earlier registry inspection found only core `0.1.0a1` on
  PyPI; recheck current registry state before choosing release versions.
- The adapter imports `gramlot.contrib._shared.pages` and `.runtime` directly.
- Core already builds a browser ZIP and embeds it in the wheel, with parity
  verification; source runtime fallback must not conceal missing release assets.
- Adapter CI checks out core `develop` and runs npm. This does not test what an
  ordinary pip consumer receives.
- Core's inspected publishing workflow creates GitHub prereleases, uses a
  hard-coded old release-note filename and does not publish to PyPI.
- The core is undergoing other changes, including FastAPI extraction. Its
  current optional extra refers to `gramlot-fastapi`, while the inspected core
  CI still requests that extra. Coordinate this dependency before release;
  do not include unrelated working changes automatically.
- No final public-index installation or fresh-project browser gate exists yet.

<a id="gd-075-025"></a>

## 025 · Establish the release baseline and compatibility contract

Block ID: **GD-075-025**.

Owners: both repositories. Dependency: none.

- Inventory current changes and agree the exact core and adapter commits to
  release, preserving unrelated work. Work on develop and consolidate main only
  after required checks. Recheck repository instructions at execution time.
- Identify the shared symbols used by Django: page discovery/invocation,
  request-independent service contracts, startup rendering and asset discovery.
- Expose a small documented, supported core interface for those functions and
  update the adapter to use it. Settle names during implementation; do not copy
  shared implementations or move generic WebPage/JavaScript into this package.
- Add boundary tests: core imports without Django/FastAPI; adapter imports
  without the old `gramlot.contrib.django` or a FastAPI installation.
- Select available release numbers and a Python/Django compatibility matrix.
  Prefer an initial exact core pin, widening only after compatibility tests.
  Verify supported Django/Python combinations against their release metadata.
- Choose versioning that allows the exact unqualified pip command. A preliminary
  alpha can be tested explicitly, but it does not replace the final no-`--pre`
  acceptance check. Keep maturity descriptions honest regardless of numbering.

Done: written supported boundary, selected candidate commits/versions and passing
contract tests. Resolve any unpublished dependency needed by core release CI,
including the concurrent FastAPI integration, without widening Django's scope.

<a id="gd-075-030"></a>

## 030 · Make the Gramlot artifact self-contained

Block ID: **GD-075-030**.

Owner: Gramlot. Dependency: phase 1.

- Retain and verify the existing browser compilation/minification pipeline and
  its locked JavaScript dependencies; include every lazy-loaded resource.
- Build the browser payload once for the candidate commit and embed the same
  files in the Python wheel and standalone ZIP, with manifest/build ID and hashes.
- Build an sdist containing prepared assets. Building a wheel from the extracted
  sdist must work without Node, npm, checkout paths or fetching browser assets.
- Verify archives contain neither Django integration nor local environments,
  generated development data or source-path dependencies.
- In an installed release, require a complete valid browser payload. Report a
  useful error for missing/incompatible assets rather than silently relying on
  source-tree files. Keep any source development fallback explicit and tested.
- Run the full relevant core Python/JavaScript suite and strict packaging/docs
  checks; resolve failures before accepting the release candidate.

Done: candidate wheel, sdist and browser ZIP pass integrity/parity checks;
wheel installation and sdist reconstruction work on a Python-only machine.

<a id="gd-075-035"></a>

## 035 · Make gramlot-django consume published-style packages

Block ID: **GD-075-035**.

Owner: gramlot-django. Dependencies: phases 1 and 2.

- Declare ordinary index-resolvable runtime requirements for Django and the
  selected core release; verify the entire transitive dependency set is available.
- Remove the required sibling path override from the standard setup and regenerate
  uv.lock. Optional contributor overrides must be explicit and unnecessary for
  normal tests/installations. Before publication, CI can use exact candidate
  wheels; after publication, its consumer gate must use PyPI alone.
- Ensure runtime URL generation uses the core manifest, correct MIME types and
  versioned caching. Check nested URL prefixes, DEBUG=False and lazy assets.
- Keep Wagtail/Bakery, test tools, docs tools and Node out of the base install.
- Keep the adapter wheel small: Python integration only, without a second browser
  runtime or bundled demo database/media. Keep downloadable examples separate
  from mandatory installed runtime content.
- Validate metadata, licenses, public imports and sdist-to-wheel installation.

Done: candidate `gramlot-django` installs with its core wheel into a new environment
and runs the existing behavior suite without editable/source installations.

<a id="gd-075-040"></a>

## 040 · Add consumer-focused CI and browser acceptance

Block ID: **GD-075-040**.

Owners: both repositories. Dependencies: phases 2 and 3.

- Replace the adapter's core-develop checkout/npm build with candidate artifact
  testing before release and package-index installation after release. Normal
  adapter CI must not depend on a moving core branch or the developer workspace.
- Run the 26-case baseline plus migration/asset contracts against installed wheels,
  with actual Django middleware, CSRF, auth, ORM, transactions and ASGI behavior.
- Test the declared Python/Django matrix on Linux, and install/start smoke checks
  on Windows and macOS. Include the minimum supported versions explicitly.
- Build a minimal Django project in a temporary directory outside both checkouts,
  following only the public quickstart. SQLite is sufficient for this gate.
- In a real browser verify initial rendering, binding, a Data RPC and remote
  Source, plus a lazy-loaded resource such as the inspector. Assert no missing
  assets, console errors or external runtime/CDN requests.
- Verify the production settings path with DEBUG=False and correct ALLOWED_HOSTS;
  include nested mounting and existing-template integration.
- Run `pip check`, inspect import locations/installation reports and ensure neither
  node/npm nor a source checkout is needed. Verify startup/rendering still works
  when outgoing internet access is unavailable after dependencies are installed.
- Keep Bakery as an additional integration smoke with its own dependencies and
  restored disposable database; it must not be required for the minimal install.

Done: automated install, package-boundary and browser gates pass against the exact
candidate artifacts. Ruff/test failures block delivery; mypy remains advisory.

<a id="gd-075-045"></a>

## 045 · Write the complete quickstart and release documentation

Block ID: **GD-075-045**.

Owners: both repositories. Dependencies: phases 1 through 4.

- Document the single install command, supported versions and a complete minimal
  Django project example: settings assumptions, page file, URLconf and runserver.
- Explain installation versus creating an application and configuring its DB.
- Document self-hosted runtime assets, cache/version behavior and the default
  working route; describe optional production offloading separately.
- Keep Bakery/Wagtail setup in its own guide. Add migration instructions from
  `gramlot.contrib.django` to `gramlot_django` and remove obsolete install advice
  from maintained manuals, including the offline Django handbook.
- Explain the wheel versus standalone GitHub browser ZIP, their common build ID
  and compatibility policy. Refresh repository URLs and release notes.
- Update historical status notices with current pointers without rewriting the
  historical claims themselves. Verify quickstart commands in the CI consumer test.

Done: a developer unfamiliar with these repositories can reach a working page by
following the public guide; both documentation builds pass with warnings as errors.

<a id="gd-075-050"></a>

## 050 · Prepare the coordinated publication procedure

Block ID: **GD-075-050**.

Owners: release maintainers. Dependencies: phases 1 through 5.

- Verify ownership/access for the PyPI project names `gramlot` and
  `gramlot-django`, and GitHub release permissions. Identify account configuration
  requiring the owner before publication becomes the last remaining step.
- Prepare PyPI Trusted Publishing for the intended repository/workflow/environment,
  with an explicit manual release gate. Planning is not authorization to enable
  or trigger automatic publication.
- Prepare candidate artifacts once, record commit IDs, versions, test results and
  checksums, and publish those same verified files. Make release notes/version/tag
  handling generic instead of retaining a hard-coded historical note filename.
- Rehearse with a local candidate wheelhouse or staging index. Any TestPyPI test
  is provisional: it does not prove the final public-PyPI command works.
- Prepare recovery instructions: if a published version is faulty, stop the second
  package release, diagnose, and use a corrected version/yank where appropriate;
  never overwrite an existing version or silently change the browser payload.

Done: a concrete reviewable release set and executable runbook are ready. Actual
publication follows explicit owner authorization, consistent with AGENTS.md's
rule: "Do not introduce automatic package publication or deployment without authorization."

<a id="gd-075-055"></a>

## 055 · Publish in dependency order and verify the exact promise

Block ID: **GD-075-055**.

Owners: release maintainers. Dependencies: phase 6 and publication authorization.

1. Publish the compatible Gramlot wheel and sdist to PyPI; attach the matching
   browser ZIP and checksums to its GitHub release.
2. Wait until the core version resolves from PyPI and verify it in a fresh
   environment with no local artifacts or private indexes.
3. Publish gramlot-django to PyPI using the tested dependency metadata.
4. From a clean machine/environment, run exactly:

   ```sh
   python -m pip install gramlot-django
   python -m pip check
   ```

5. Run the documented minimal project and the browser smoke again, asserting the
   resolved package versions and browser build ID match the release set.
6. Record the public URLs and final verification, update installation/status
   documentation and release notes, and enable routine registry-consumer CI.

Done: the exact command succeeds from public PyPI with no additional flags or
manual downloads, and the resulting packages render and run the minimal Django
application. Only then mark the one-command installation objective complete.

<a id="gd-075-060"></a>

## 060 · Scope exclusions

Block ID: **GD-075-060**.

This plan does not deploy a user's site, automatically configure a production
database, replace standard Django management commands, move generic core features
into the adapter or require npm/CDN access on consumer machines. Existing local
presentation environments may be upgraded separately after the release is verified.

<a id="gd-075-065"></a>

## 065 · References

Block ID: **GD-075-065**.

- [pip installation and prerelease selection](https://pip.pypa.io/en/stable/cli/pip_install/#pre-release-versions)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [GitHub release assets](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
