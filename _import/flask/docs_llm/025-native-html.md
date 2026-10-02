# 025 · Native HTML host

Document ID: **GFL-025**. [Paired view](../docs/025-native-html.md).

<a id="gfl-025-005"></a>

## 005 · Integration

Block ID: **GFL-025-005**.

`mount_native_html` mounts the neutral Host through Flask, including trusted
pages, packaged runtime and main/source/close. A prefix updates the browser's
close URL. Explicit disposal and non-persisted `pagehide` attempt owner-checked
closure; TTL remains the fallback. It has no database dependency.

<a id="gfl-025-010"></a>

## 010 · Ownership and bounds

Block ID: **GFL-025-010**.

Random owner cookies, expiring bounded entries, a 4096-byte JSON limit and
explicit close are tested with Flask's client. Production auth/sessions,
databases, releases and deployment remain outside this profile.
