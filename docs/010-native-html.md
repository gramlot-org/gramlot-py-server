# 010 · Kajenn native HTML host

Document ID: **GA-010**.
[Concise counterpart](https://github.com/gramlot-org/gramlot-genro-asgi/blob/develop/docs_llm/010-native-html.md).

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
