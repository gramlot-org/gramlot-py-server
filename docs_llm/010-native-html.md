# 010 · Kajenn native HTML host

Document ID: **GA-010**. [Expanded view](../docs/010-native-html.md).

<a id="ga-010-005"></a>

## 005 · Integration boundary

Block ID: **GA-010-005**.

`gramlot-kajenn` exports `gramlot_kajenn.KajennNativeHtmlApplication`, a real
`genro_asgi.BaseApplication` backed by `gramlot.server.Host`. It supplies
mounted URLs and uses the owning server's `run_sync` for packaged assets.
Generic `NativeHtmlASGI` and `create_asgi_application` belong to
`gramlot-minimal`; Kajenn imports the former without re-exporting either.
The upstream server still uses the `genro-asgi` distribution and `genro_asgi`
import names.

<a id="ga-010-010"></a>

## 010 · Native behavior

Block ID: **GA-010-010**.

Real `BaseServer` tests cover mounted routes, typed Source, owner isolation,
limits, assets, error mapping and close. The generic transport contract comes
from `gramlot-minimal`.

<a id="ga-010-015"></a>

## 015 · Status and omissions

Block ID: **GA-010-015**.

No native database integration, production auth/session storage, WebSockets or
deployment. Legacy PoC modules and CLI require APIs absent from clean core;
see [GA-005](005-genro-asgi-legacy.md). Accepted 0.1.0 artifacts are unchanged.


<a id="ga-010-020"></a>

## 020 · Shared examples from Gramlot

Kajenn executes the shared Python pages inside its server application; generic ASGI hosting belongs to Minimal.

Gramlot is the upstream reference for framework documentation and the shared
teaching suite: pages, READMEs, runner, logo and theme. Read its manual first,
then the chosen integration's guide; clone that downstream repository for its
adapter, configuration and launch instructions. Read the Docs is the documentation
target, not a claim that all integration sites are already published.

Integrations consume Gramlot's examples without maintaining local source copies.
Python runs in Flask/FastAPI/Django/Kajenn or Minimal with Uvicorn; JavaScript runs
in Node.js/Bun or Minimal's browser Worker. The integration selects the language.
Update the Gramlot dependency, then restart or regenerate the standalone export
to receive changes. Installed environments and exports do not refresh themselves.
Generated assets are outputs, not another source. First-party dependencies remain
unpinned; published 0.1.0 archives are immutable.

Agreed model, not completed ecosystem rollout: sources exist in `examples/html_svg`,
`examples/00-runner` and `themes/gramlot-base`; uniform dependency packaging and
launch commands for all six integrations remain to be implemented and verified.
Historical demos and existing Hello World smoke launchers are separate evidence.

See the [Gramlot guide](https://github.com/gramlot-org/gramlot/blob/main/docs/public/025-try.md#gc-025-020) for the authoritative shared policy. Public documentation follows `main`; unpublished development changes are not yet part of that public reference.
