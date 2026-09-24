# 025 · Native HTML host

Document ID: **GFL-025**. [Paired view](../docs_llm/025-native-html.md).

<a id="gfl-025-005"></a>

## 005 · Integration

Block ID: **GFL-025-005**.

`mount_native_html(app, pages, prefix="")` mounts the clean
`gramlot.server.Host` contract as a Flask Blueprint. It serves trusted Python
pages, the packaged browser runtime and main/source/close JSON operations. It is
separate from the legacy recipe/RPC and optional Microblog/database profiles.
A prefix updates the bootstrapped close URL. Explicit browser disposal and
non-persisted `pagehide` attempt closure through the owner-checked route; TTL
remains the fallback.

<a id="gfl-025-010"></a>

## 010 · Ownership and bounds

Block ID: **GFL-025-010**.

The page response sets a random HttpOnly owner cookie. Main, remote Source and
close require that cookie and page ID. Entries expire, capacity is bounded and
JSON requests are limited to 4096 bytes. Tests cover status mapping, packaged
assets, typed Source, ownership, capacity and cleanup. Authentication,
production sessions, databases, release and deployment are excluded.
