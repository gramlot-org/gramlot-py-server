# Server and database integration

Document ID: **GF-040**.

**Status:** architectural discussion recorded on 2026-09-15.
See the [current architecture](010-architecture.md) for the 2026-09-16 constitution
and the existing SQLite prototype in `gramlot-poc`; implementation statements
below describe this FastAPI extraction, not the absence of database work in the POC.
The common database interface and its implementation are still to be defined.
Class and module names below illustrate responsibilities; they are not a new
public API.

<a id="purpose"></a>
<a id="gf-040-005"></a>

## 005 · Purpose

Block ID: **GF-040-005**.

Gramlot applications should compose a server integration and, when needed, a
database integration. Each integration has internal machinery and an outer
surface available on the page.

The page is the surface that application developers work with. Adapters perform
the underlying preparation, translation and resource management. Developers
should not have to repeat that infrastructure in every page.

<a id="two-independent-integrations"></a>
<a id="gf-040-010"></a>

## 010 · Two independent integrations

Block ID: **GF-040-010**.

| Integration | Internal responsibilities | Surface available on the page |
| --- | --- | --- |
| Server | Adapt a particular host, such as FastAPI, Django or Genro ASGI; connect requests to page invocations; deliver responses and assets. | Selected host services and request context, where needed. |
| Database | Adapt the chosen data system to Gramlot's database interface; wrap backend objects where necessary; manage the resources required by an operation. | The standard Gramlot database interface. |

A server adapter must be usable without a database adapter. A database adapter
must not depend on FastAPI or another particular server. The application connects
the selected integrations and supplies their configuration.

The conceptual arrangement is:

```text
Application configuration
    selects a server adapter and an optional database adapter
                         |
                         v
Page: the developer-facing surface
    Gramlot page capabilities
    selected server capabilities
    standard Gramlot database interface, when enabled
                         |
                         v
Internal integration machinery
    server adapter                  database adapter
    FastAPI / Django / Genro ASGI    SQLAlchemy / Genropy / fake
```

This diagram describes responsibilities. It does not prescribe an inheritance
order or a concrete configuration API.

<a id="gramlot-owns-the-database-contract"></a>
<a id="gf-040-015"></a>

## 015 · Gramlot owns the database contract

Block ID: **GF-040-015**.

Gramlot will define its own standard database interface. The application page
will use that interface, and each database adapter will make its operations work
with the selected backend.

For example, a request for table records would follow this conceptual path:

```text
Page asks through the Gramlot database interface
    -> selected adapter interprets the operation
    -> backend supplies data, or the fake adapter supplies simulated data
    -> adapter returns a result following the Gramlot contract
    -> page consumes that result
```

The standard interface must define the meaning of operations and results, not
just give unrelated backend methods similar names. Its method names, supported
operations, result types and error behavior remain open design work.

In particular, merely exposing a native SQLAlchemy session on one page and a
native Genropy database on another would not satisfy this shared interface.
Whether an explicit escape hatch to native backend features is useful is a
separate, undecided question.

Changing adapters should preserve page code that uses the agreed contract and
the same application data model. This does not imply that unrelated schemas or
every native backend feature are automatically interchangeable.

<a id="internal-adapters-and-page-mixins"></a>
<a id="gf-040-020"></a>

## 020 · Internal adapters and page mixins

Block ID: **GF-040-020**.

Mixins can provide the page-facing part of an integration. A server mixin could
expose request context; a database mixin could expose the standard database
interface and delegate operations to the configured adapter.

The discussed names include `FastapiPageMixin`, `SqlalchemyPageMixin` and
`GenropyPageMixin`, together with a base Gramlot page. These names describe the
idea of composing capabilities. The exact classes, whether backend-specific
page mixins are needed, and their inheritance order are not settled.

A mixin is only one part of an integration. Inheriting from it does not by itself
create a server, configure a database or establish safe resource cleanup. Those
operations belong to the internal integration machinery.

Application configuration must connect the page surface to the actual adapters.
The details should run transparently during ordinary page use, while failures
must remain visible and diagnosable. Transparent operation does not mean silently
ignoring errors or choosing an undocumented transaction policy.

<a id="resource-lifecycle"></a>
<a id="gf-040-025"></a>

## 025 · Resource lifecycle

Block ID: **GF-040-025**.

The integrations need an explicit agreement about the lifetime of resources
during a page method invocation. This includes acquiring database resources,
making them available to the operation, preparing results, and releasing
resources even when execution fails.

The following policies have not yet been chosen:

- Session or connection lifetime and reuse.
- Explicit versus automatic commit, and rollback behavior.
- Synchronous and asynchronous execution.
- Which integration owns each resource and its cleanup.

The current Genropy integration already requires its database context, database
work and cleanup to run in the same worker thread. Separating the integrations
must preserve that constraint. `GnrApp` also provides model metadata and other
services; the standard interface must deliberately select what it exposes.

<a id="fake-database-adapter"></a>
<a id="gf-040-030"></a>

## 030 · Fake database adapter

Block ID: **GF-040-030**.

The fake adapter will implement the same Gramlot database interface and return
simulated data through it. Pages must not need fake-specific branches or a second
way to access data.

The agreed teaching dataset consists of **exactly three standard tables, each
containing a few rows**. Its purpose is to make the adapter mechanism easy to
understand with a small example.

The table names, columns and contents have not been selected. Relationships
between the three tables were suggested but have not been agreed. Whether the
fake adapter supports writes, how changes are reset, and which operations form
its first supported contract are also still open.

<a id="code-ownership"></a>
<a id="gf-040-035"></a>

## 035 · Code ownership

Block ID: **GF-040-035**.

The discussed direction places server-independent database integrations in
Gramlot's optional `contrib` area, for example `gramlot.contrib.sqlalchemy` and
`gramlot.contrib.genropy`, with a corresponding fake integration. Exact package
paths remain subject to implementation design.

Host-specific adapters remain in their integration repositories, including
`gramlot-fastapi`. Database dependencies must stay optional: ordinary Gramlot
imports and plain hosting must not require SQLAlchemy or Genropy.

This direction refines the earlier extraction scope. The existing Genropy code
was moved into this repository as part of the FastAPI extraction. Its reusable
database responsibilities are candidates for the new Gramlot contrib boundary;
the extraction alone did not establish that separation.

<a id="current-implementation-and-next-decisions"></a>
<a id="gf-040-040"></a>

## 040 · Current implementation and next decisions

Block ID: **GF-040-040**.

The repository implements FastAPI hosting, the legacy Genropy profile, and a
[provisional SQLAlchemy/SQLite profile](035-sqlalchemy.md). The latter connects the
core minimum `DbHandler.dbselect` contract through `db_handler` and `DbPageMixin`.
The broader interface and three-table fake adapter described here remain open.

Before extending this minimum implementation, settle:

1. The smallest useful database contract: operations, results and errors.
2. The three teaching tables and whether they have relationships.
3. The connection between page capabilities and configured adapters.
4. Resource and transaction policies.
5. Contract tests shared by adapters, plus tests for backend-specific lifecycle
   constraints.

These are design questions to resolve through focused discussion. This document
records the direction without supplying unapproved API details.
