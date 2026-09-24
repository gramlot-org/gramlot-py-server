# Integration scope

For native 0.1.0, `NativeHtmlASGI` adapts raw ASGI HTTP to clean
`gramlot.server.Host`; `KajennNativeHtmlApplication` mounts that contract on a
real Genro ASGI server. Both serve packaged runtime and bounded
main/source/close routes. See [GA-010](010-native-html.md). The older
PageRegistry and `GnrApp` architecture below is historical PoC work, outside
native 0.1.0 compatibility.

Genro ASGI owns server execution. Gramlot's experimental host-independent
PageRegistry owns discovery, service allowlisting, parameter validation and fresh
page/Source creation. This adapter owns HTTP transport and packaged asset delivery.

The optional `GenropyApplication` attaches a caller-owned legacy `GnrApp` to
`GenropyPage` invocations. Synchronous page code uses `self.db` in the server's
worker; connection closure and environment reset happen in that same worker,
including failure paths. Async database access is rejected. Queries, permissions
and explicit commits remain with the application; no SQL or generic database
capability contract is introduced in the host.

The first slice prioritizes Genro ASGI + legacy GenroPy; SQLAlchemy is deferred.
Plain hosting remains independent of database choice. Shared contracts belong in
Gramlot; Genro ASGI dependencies remain in this adapter.

See [the current contract](005-genro-asgi-legacy.md) for exact dependency versions,
verification scope and omissions. No formal Live Object Tree semantics are implied.
