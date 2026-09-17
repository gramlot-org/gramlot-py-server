# Integration scope

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
