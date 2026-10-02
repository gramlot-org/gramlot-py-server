# gramlot-django: native integration scope

The current installable package owns Django request and response translation for the native Gramlot 0.1.0 `Host` and `Page` contract. Core owns page execution, Source transport, runtime assets and the neutral host registry; Django owns URL mounting, HTTP method and body handling, owner cookie delivery and status mapping. The adapter depends on core, never the reverse.

`NativeHtmlPages(pages, prefix="")` exposes `urls` for Django `include`. The caller mounts those URLs at the same prefix. It serves page HTML and the packaged runtime by GET, and main/source/close by JSON POST. A same-site HttpOnly cookie associates requests with in-process page records. It is not an authentication or permission system. The browser transport does not send Django CSRF tokens, so the three JSON endpoints are CSRF-exempt; sites must apply their authorization policy at their own boundary. One process owns each registry; multi-process shared state is not implemented.

The former DjangoPage, ORM/schema helpers, Polls/Bakery demos and legacy tests remain historical evidence under `historical/` and `examples/`. They require the PoC APIs and are not exported by the native package or accepted as 0.1.0 behavior. Their future transfer needs a separate contract and review. No ORM/database adapter is introduced in this native slice.

This work is local development. GitHub source publication, package registry releases and application deployment are not authorized by this specification.
