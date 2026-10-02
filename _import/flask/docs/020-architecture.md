# 020 · Architecture and integration

Document ID: **GFL-020**.

[Paired view](../docs_llm/020-architecture.md).

<a id="gfl-020-005"></a>

## 005 · Host ownership

Block ID: **GFL-020-005**.

`mount_native_html` adapts Flask requests to the clean core's neutral Host,
serving trusted Python pages, packaged runtime and bounded main/source/close
routes. `mount_gramlot`, PageRegistry, recipes and TYTX Source/Data services
belong to the separate historical PoC profile. Native hosting has no database
or production authentication service; the owning Flask app controls access.

<a id="gfl-020-010"></a>

## 010 · Application and database ownership

Block ID: **GFL-020-010**.

The demo wrapper preserves bundled upstream Microblog source and adds navigation to a Python-authored Gramlot explorer. dbSelect reuses SqliteDbHandler; a bound user identity triggers remote Source for profile and latest posts from Microblog ORM models. Flask-Login protects HTML, recipes and services. Flask-SQLAlchemy owns request sessions; the CLI closes the separate selector engine. No application-local DOM/event/request mechanism or duplicate database adapter is introduced.

<a id="gfl-020-015"></a>

## 015 · Evidence and open work

Block ID: **GFL-020-015**.

Native hosting has focused tests against clean core 0.1.0. The Microblog demo
below remains historical PoC material with a bundled MIT notice. Its tests
cover dispatch, isolation, authentication, database reads, fixtures and CLI;
they do not establish native 0.1.0 compatibility. Production, async transports
and formal Live Object Tree semantics are not claimed.
