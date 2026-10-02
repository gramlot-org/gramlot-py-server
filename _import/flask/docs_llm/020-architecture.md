# 020 · Architecture and integration

Document ID: **GFL-020**.

[Paired view](../docs/020-architecture.md).

<a id="gfl-020-005"></a>

## 005 · Host ownership

Block ID: **GFL-020-005**.

`mount_native_html` adapts Flask requests to clean `gramlot.server.Host` for
trusted pages, packaged runtime and bounded main/source/close routes. The
`mount_gramlot`/PageRegistry/recipe/TYTX stack is historical PoC material,
outside native 0.1.0. The owning app controls access.

<a id="gfl-020-010"></a>

## 010 · Application and database ownership

Block ID: **GFL-020-010**.

The wrapper preserves upstream Microblog and adds navigation to Python Gramlot UI. dbSelect uses SqliteDbHandler; bound identity drives remote profile/post Source from existing ORM models. Flask-Login guards HTML/recipes/services; Flask-SQLAlchemy owns request sessions and the CLI closes the selector engine. No UI bypass or duplicate database adapter.

<a id="gfl-020-015"></a>

## 015 · Evidence and open work

Block ID: **GFL-020-015**.

Native hosting has focused clean-core 0.1.0 tests. The historical Microblog
demo retains its MIT notice and PoC tests, which do not establish native
compatibility. Production, async transport and formal LOT semantics remain
outside scope.
