# Integration scope

[Expanded](../docs/architecture.md).

Native `KajennNativeHtmlApplication` mounts clean `gramlot.server.Host` on
`genro_asgi.BaseServer`; generic transport comes from `gramlot-minimal`.
Kajenn owns mounted URLs and server worker integration; see
[GA-010](010-native-html.md). The server dependency is outside core.

Historical PageRegistry and GnrApp modules require PoC APIs, not clean core.
The old host owns HTTP/assets and caller-owned GnrApp lifecycle; services own
queries, permissions and commits. See [GA-005](005-genro-asgi-legacy.md).
No formal Live Object Tree semantics are implied.
