# 050 · Native HTML host

Document ID: **GF-050**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-fastapi/blob/main/docs_llm/050-native-html.md).

<a id="gf-050-005"></a>

## 005 · Public integration

Block ID: **GF-050-005**.

`NativeHtmlApplication(pages)` creates a ready-made FastAPI application.
`mount_native_html(app, pages, prefix="")` adds the same integration to an
existing application. Both use the neutral `gramlot.server.Host`; database
packages and the legacy recipe/RPC adapter are outside this profile.

The integration serves trusted Python page modules, the packaged
`/assets/gramlot.js`, and JSON POST operations at `/gramlot/main`,
`/gramlot/source` and `/gramlot/close`. A prefix moves all these routes and the
bootstrapped `closeUrl` together. The browser uses close on explicit disposal or
non-persisted `pagehide`; the Host checks the owner cookie and TTL covers loss.

<a id="gf-050-010"></a>

## 010 · Request and lifecycle contract

Block ID: **GF-050-010**.

The initial page response creates a random owner cookie and a bounded,
time-limited page entry. Main, remote Source and close requests must carry both
the page ID and that cookie. Page IDs are not authentication; deployments still
own user access control. JSON bodies are limited to 4096 bytes. Malformed media
or JSON returns 415 or 400, oversized input returns 413, unknown/unowned pages
and methods return 404, and exhausted page capacity returns 503. Unexpected page
exceptions remain server errors.

<a id="gf-050-015"></a>

## 015 · Status and verification

Block ID: **GF-050-015**.

This bounded native HTML profile is implemented and tested with FastAPI's real
test client for bootstrap, packaged assets, typed main/remote Source, ownership,
request limits, capacity and explicit close. It is experimental and has no
database, production session store, package release or deployment claim.
