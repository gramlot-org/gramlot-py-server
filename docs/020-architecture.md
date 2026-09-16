# 020 · Architecture and integration

Document ID: **GFL-020**.

[Paired view](../docs_llm/020-architecture.md).

<a id="gfl-020-005"></a>

## 005 · Host ownership

Block ID: **GFL-020-005**.

mount_gramlot registers shared runtime assets, HTML, recipes and TYTX Source/Data services with Flask. PageRegistry creates fresh pages; synchronous page work runs on the WSGI request thread with Flask context. Role, method, content-type and parameter checks precede dispatch. Pages/services use no-store, immutable runtime assets use long caching and traversal is rejected. The access_check callback guards every data-bearing route. Plain hosting is public by default.

<a id="gfl-020-010"></a>

## 010 · Application and database ownership

Block ID: **GFL-020-010**.

The demo wrapper preserves bundled upstream Microblog source and adds navigation to a Python-authored Gramlot explorer. dbSelect reuses SqliteDbHandler; a bound user identity triggers remote Source for profile and latest posts from Microblog ORM models. Flask-Login protects HTML, recipes and services. Flask-SQLAlchemy owns request sessions; the CLI closes the separate selector engine. No application-local DOM/event/request mechanism or duplicate database adapter is introduced.

<a id="gfl-020-015"></a>

## 015 · Evidence and open work

Block ID: **GFL-020-015**.

The runtime is the checksummed experimental Gramlot 0.1.5 wheel. The clean core remains architectural/port documentation, so this is not accepted core compatibility. Microblog source revision and MIT notice are bundled. Tests cover dispatch/errors, context isolation, assets, authentication, shared database reads, persistent fixtures and CLI behavior. The demo omits external search, translation, password-reset email and workers; shows at most 20 posts per user; and requires its own process for upstream app/config imports. Production, async transports and formal Live Object Tree semantics are not claimed.
