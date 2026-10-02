# 010 · Kajenn native HTML host

Document ID: **GA-010**.
[Concise counterpart](https://github.com/gramlot-org/gramlot-kajenn/blob/develop/docs_llm/010-native-html.md).

<a id="ga-010-005"></a>

## 005 · Integration boundary

Block ID: **GA-010-005**.

`gramlot-kajenn` supplies `gramlot_kajenn.KajennNativeHtmlApplication`, a
mountable `genro_asgi.BaseApplication` backed by the neutral
`gramlot.server.Host`. The Kajenn server strips the mount from incoming paths;
the application supplies public URLs with that mount. Packaged runtime reads use
the owning server's `run_sync` worker API.

Generic `NativeHtmlASGI` and `create_asgi_application` are owned and exported by
`gramlot-minimal`, which has no Kajenn dependency. Kajenn imports its generic
adapter from `gramlot_minimal.asgi` and adds the mount and worker integration.
It does not re-export the generic APIs. The external server dependency retains
its current `genro-asgi` distribution and `genro_asgi` import names.

<a id="ga-010-010"></a>

## 010 · Native behavior

Block ID: **GA-010-010**.

`KajennNativeHtmlApplication` mounts on a real `genro_asgi.BaseServer`. Its
browser-facing routes serve the packaged runtime and bounded main/source/close
operations. The close URL includes the Kajenn mount. Owner-checked close,
page lifetime bounds, the 4096-byte JSON input limit and status mapping come
from `gramlot-minimal`'s ASGI implementation. Native tests exercise this class
through a real `BaseServer`, including owner isolation, assets, source requests,
request limits, errors and close.

<a id="ga-010-015"></a>

## 015 · Status and omissions

Block ID: **GA-010-015**.

This native profile has no database integration. The old `GramlotApplication`,
GenroPy `GnrApp` integration and CLI use PoC APIs absent from clean core; see
[GA-005](005-genro-asgi-legacy.md). Production authentication/session storage,
WebSockets and deployment are outside this bounded profile. The accepted
0.1.0 artifacts remain unchanged by this development reorganization.


<a id="ga-010-020"></a>

## 020 · Shared examples from Gramlot

Kajenn executes the shared Python pages inside its server application; generic ASGI hosting belongs to Minimal.

Gramlot is the primary reference for framework concepts, APIs and the shared
teaching examples. Start with its documentation on Read the Docs and its source
repository. Then choose an integration, read its environment-specific guide and
clone that integration repository to configure and run the examples in that host.
Read the Docs is the documentation delivery target; this policy does not claim
that every integration site is already connected or published.

The integration repositories are downstream consumers of Gramlot. Gramlot owns
the example pages, their READMEs, the runner, logo and shared theme. Integrations
own adapters, environment configuration, launch commands and hosting instructions.
They must consume the shared material from the Gramlot dependency rather than
maintain copied teaching suites. Generated installation or export assets are
reproducible outputs, not independently maintained sources.

Python examples run inside Flask, FastAPI, Django, Kajenn or Minimal's Uvicorn
profile. JavaScript examples run inside Node.js/Bun or Minimal's browser Worker
standalone profile. The integration selects the execution language; the shared
runner does not ask users to switch between Python and JavaScript.

To receive changed examples, update the Gramlot dependency following the chosen
integration's setup instructions, then restart the host or rebuild the standalone
export. An existing installation or exported folder does not update itself when
upstream changes. First-party dependencies remain unpinned; the published 0.1.0
archives remain immutable.

This is the agreed distribution model. The teaching sources already live in
Gramlot under `examples/html_svg`, the runner under `examples/00-runner`, and the
theme under `themes/gramlot-base`. Uniform dependency packaging and example launch
commands across all six integrations still need implementation and verification.
Existing Hello World smoke launchers and historical demos do not establish that
this shared teaching-suite workflow is already available in every integration.

See the [Gramlot guide](https://github.com/gramlot-org/gramlot/blob/main/docs/public/025-try.md#gc-025-020) for the authoritative shared policy. Public documentation follows `main`; unpublished development changes are not yet part of that public reference.
