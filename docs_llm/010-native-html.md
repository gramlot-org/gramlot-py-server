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
