# 010 · Native HTML hosts

Document ID: **GA-010**. [Expanded view](../docs/010-native-html.md).

<a id="ga-010-005"></a>

## 005 · Generic ASGI

Block ID: **GA-010-005**.

`NativeHtmlASGI` and `create_asgi_application` expose a Kajenn-free ASGI path
which Uvicorn can run. Browser close URLs match the mount for both generic ASGI
and Kajenn; explicit disposal and non-persisted `pagehide` attempt closure with
owner checking and TTL fallback.

<a id="ga-010-010"></a>

## 010 · Kajenn integration

Block ID: **GA-010-010**.

`KajennNativeHtmlApplication` is a real `BaseApplication`; mounted URL handling
and packaged asset reads use Kajenn's server contract and worker API.

<a id="ga-010-015"></a>

## 015 · Contract and status

Block ID: **GA-010-015**.

Both paths test owner cookies, expiring bounded entries, 4096-byte JSON input,
typed Source, assets and close. Database, production auth/sessions, release and
deployment are excluded.
