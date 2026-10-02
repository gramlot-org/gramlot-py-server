# 050 · Native HTML host

Document ID: **GF-050**. [Expanded view](../docs/050-native-html.md).

<a id="gf-050-005"></a>

## 005 · Public integration

Block ID: **GF-050-005**.

`NativeHtmlApplication` and `mount_native_html` adapt `gramlot.server.Host` to
FastAPI. They serve trusted pages, the packaged runtime and main/source/close
JSON operations. A prefix also updates the bootstrapped close URL. Browser
disposal or non-persisted `pagehide` attempts owner-checked closure; TTL remains
the fallback. This profile imports no database adapter.

<a id="gf-050-010"></a>

## 010 · Request and lifecycle contract

Block ID: **GF-050-010**.

A random HttpOnly owner cookie is paired with each page ID. The registry is
bounded and expiring; close removes owned pages. JSON input is limited to 4096
bytes. Status mapping covers media, JSON, size, ownership, unknown methods and
capacity; unexpected page failures remain server errors. Hosts still own access
control.

<a id="gf-050-015"></a>

## 015 · Status and verification

Block ID: **GF-050-015**.

Focused client tests cover assets, typed main/remote Source, ownership, limits,
capacity and close. Database, production sessions, release and deployment are
excluded.
