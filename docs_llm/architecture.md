# Integration scope

[Expanded](../docs/architecture.md).

Native 0.1.0 uses `NativeHtmlASGI` or `KajennNativeHtmlApplication` to adapt
clean `gramlot.server.Host`; see [GA-010](010-native-html.md). The following
PageRegistry and GnrApp architecture is historical PoC work, outside native
compatibility.

Genro ASGI owns workers/server; shared experimental Gramlot PageRegistry owns
page discovery, allowlisting, validation, fresh instances and Source. Adapter owns
HTTP/assets and optional caller-owned GnrApp lifecycle. Synchronous GenropyPage.db
access, close and environment reset stay in the same worker, including failures;
async DB access rejected. Application owns queries/permissions/commits. No generic
DB contract lives here. Legacy first; SQLAlchemy deferred; plain host independent.
[Contract](005-genro-asgi-legacy.md) defines dependencies/omissions. No LOT semantics.
