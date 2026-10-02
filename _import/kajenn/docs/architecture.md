# Integration scope

For native 0.1.0, `KajennNativeHtmlApplication` mounts the neutral
`gramlot.server.Host` on `genro_asgi.BaseServer`. It imports the generic ASGI
transport from `gramlot-minimal` and provides Kajenn-specific mount and worker
behavior. See [GA-010](010-native-html.md). The `genro-asgi` server dependency
remains in this integration, outside Gramlot core and minimal ASGI hosting.

The older PageRegistry and `GnrApp` architecture is historical PoC work,
outside native clean-core compatibility. In that profile, Genro ASGI owns server
execution; experimental PageRegistry owns discovery, service allowlisting,
parameter validation and fresh page/Source creation. The adapter owns transport
and assets. Optional `GenropyApplication` uses a caller-owned legacy `GnrApp`;
synchronous service execution and database cleanup stay in one worker.
Application services own queries, permissions and commits. No database contract
is introduced here. See [GA-005](005-genro-asgi-legacy.md). No formal Live
Object Tree semantics are implied.
