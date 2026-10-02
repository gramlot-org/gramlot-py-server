# 030 · Integration architecture

Document ID: **GD-030**.

[Concise counterpart](https://github.com/gramlot-org/gramlot-django/blob/develop/docs_llm/030-architecture.md).

<a id="gd-030-005"></a>

## 005 · Authority and current status

Block ID: **GD-030-005**.

This is the architecture of the Django POC, under review alongside Gramlot.
The product [constitution, sections 2, 7 and 8](https://github.com/gramlot-org/gramlot/blob/main/docs/00-constitution.md)
and [overview, section 5](https://github.com/gramlot-org/gramlot/blob/main/docs/01-overview.md)
define independent server and database boundaries. Experimental implementations
remain in [gramlot-poc](https://github.com/gramlot-org/gramlot-poc); they do not
become accepted product contracts merely by working here.

<a id="gd-030-010"></a>

## 010 · Two independent adaptations

Block ID: **GD-030-010**.

**Server adaptation** connects Gramlot pages and services to a hosting framework.
Each supported host provides its own adaptation. For Django this includes URL
mounting, request/response handling, authentication, permissions, CSRF and middleware.

**Database adaptation** connects shared data services to a database or ORM.
Each supported database integration provides its own implementation. Django also
participates here through its ORM: query projection, schema browsing and model
operations are database responsibilities, not HTTP responsibilities.

A single package can provide both adaptations; the roles remain independent.
Django is an ORM integration here, not a database engine. Independence is an
architectural boundary, not a claim that every host/backend combination is tested.

<a id="gd-030-015"></a>

## 015 · Implemented POC ownership

Block ID: **GD-030-015**.

| Owner | Responsibilities |
| --- | --- |
| Gramlot POC core | Python WebPage/builder, Source/Data transport, shared services, browser runtime |
| Django server adaptation | `DjangoPageCollection`, Django views/URLs, request context, permissions and CSRF |
| Django database adaptation | `selection_result`, explicit ORM projections, schema and model helpers |
| Django application | Models, settings, middleware, record authorization, transactions and Python pages |

`DjangoPage` adds request context and ORM helpers to `WebPage` in the current POC;
that convenience class does not merge the two architectural responsibilities.
`DjangoTablesPage` and `DjangoIdePage` provide specialized pages. The adapter uses
`gramlot.hosting` and `gramlot.transport`; runtime assets come from the installed
core package. Shared browser services are not copied into this integration.

<a id="gd-030-020"></a>

## 020 · Database contracts and remaining work

Block ID: **GD-030-020**.

The product constitution separates `common`, `fake`, `genropy` and `sqlalchemy`
database work and treats SQLite as a backend through SQLAlchemy. The owner's
2026-09-16 direction also identifies Django's ORM adaptation in this repository.
This explains Django's role without asserting that the product repository has
already accepted a complete Django database contract or adapter taxonomy amendment.

The local `gramlot-poc/docs/guides/database-handlers-and-proxies.md` guide
provides implementation evidence (inspected 2026-09-16; not yet available at that
path on the public develop branch). Its experimental SQLite handler is not a new
product adapter category. Current Django helpers do not establish the future
`dataRecord`, `dataSelection` or general capability protocol. Required minimum,
common optional and implementation-specific capabilities must remain distinguished.
Consolidating these contracts and reviewing ports are still open work.

<a id="gd-030-025"></a>

## 025 · Authoring and evidence

Block ID: **GD-030-025**.

Application UI and requests use Python-first Gramlot declarations, Source, Data,
bindings, controllers, stores and services. Framework gaps belong in reusable
framework components, not application-local DOM, fetch or parallel state code.
The customer, Polls and Bakery examples import this adapter. Behavior tests and
installed-package checks verify the POC; they do not imply stable product support.
