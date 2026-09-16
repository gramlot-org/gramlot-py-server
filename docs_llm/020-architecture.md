# 020 · Architecture and integration

Document ID: **GFL-020**.

[Paired view](../docs/020-architecture.md).

<a id="gfl-020-005"></a>

## 005 · Host ownership

Block ID: **GFL-020-005**.

mount_gramlot registers HTML, recipes, typed Source/Data services and shared assets. PageRegistry provides fresh pages; WSGI work keeps Flask context on the request thread. Validate roles/methods/types/parameters, reject traversal, use no-store for data and immutable caching for assets. access_check guards all data routes; plain hosting is public by default.

<a id="gfl-020-010"></a>

## 010 · Application and database ownership

Block ID: **GFL-020-010**.

The wrapper preserves upstream Microblog and adds navigation to Python Gramlot UI. dbSelect uses SqliteDbHandler; bound identity drives remote profile/post Source from existing ORM models. Flask-Login guards HTML/recipes/services; Flask-SQLAlchemy owns request sessions and the CLI closes the selector engine. No UI bypass or duplicate database adapter.

<a id="gfl-020-015"></a>

## 015 · Evidence and open work

Block ID: **GFL-020-015**.

Use the checksummed experimental 0.1.5 core wheel; consolidated-core compatibility is unclaimed. Bundle Microblog revision/license. Tests cover dispatch/errors, isolation, assets, authentication, shared data, fixtures and CLI. External mail/search/translation/workers are absent; the explorer caps posts at 20. Upstream app/config imports require a dedicated demo process. Production, async transports and formal Live Object Tree semantics remain outside scope.
