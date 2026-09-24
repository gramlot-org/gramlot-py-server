# 010 · Native HTML hosts

Document ID: **GA-010**.
[Concise counterpart](https://github.com/gramlot-org/gramlot-genro-asgi/blob/main/docs_llm/010-native-html.md).

<a id="ga-010-005"></a>

## 005 · Generic ASGI

Block ID: **GA-010-005**.

`NativeHtmlASGI` and `create_asgi_application` are reusable ASGI integrations
with no Kajenn import. Uvicorn can run this path directly. They adapt the neutral
`gramlot.server.Host`, serve the packaged runtime and implement bounded JSON
main/source/close operations. The browser receives a close URL matching the
mount; explicit disposal and non-persisted `pagehide` attempt owner-checked
closure, with TTL fallback.

<a id="ga-010-010"></a>

## 010 · Kajenn integration

Block ID: **GA-010-010**.

`KajennNativeHtmlApplication` is a separate real `genro_asgi.BaseApplication`.
Its mount supplies public browser URLs while Kajenn strips the mount for dispatch;
packaged asset reads use the owning server's `run_sync` worker API. It is not a
renamed generic Uvicorn application.

<a id="ga-010-015"></a>

## 015 · Contract and status

Block ID: **GA-010-015**.

Both paths use a random HttpOnly owner cookie, bounded/expiring page entries,
4096-byte JSON input, explicit close and the same status mapping. Focused tests
exercise both raw ASGI and a real `BaseServer`. Databases, production auth/session
storage, WebSockets, release and deployment are excluded.
