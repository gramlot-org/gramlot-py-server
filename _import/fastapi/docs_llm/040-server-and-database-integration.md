# Server and database integration

Document ID: **GF-040**.

[Expanded counterpart](../docs/040-server-and-database-integration.md).

<a id="purpose"></a>
<a id="gf-040-005"></a>

## 005 · Purpose

Block ID: **GF-040-005**.

Agreed architecture direction; page declarations are the developer-facing surface. Internal adapters perform the underlying work. Proposed interfaces are not shipped APIs.

<a id="two-independent-integrations"></a>
<a id="gf-040-010"></a>

## 010 · Two independent integrations

Block ID: **GF-040-010**.

Server adapters handle requests, invocation and assets. Database adapters implement the Gramlot database contract independently of the host.

<a id="gramlot-owns-the-database-contract"></a>
<a id="gf-040-015"></a>

## 015 · Gramlot owns the database contract

Block ID: **GF-040-015**.

Gramlot defines portable operations/results. Backend adapters translate them. The complete standard interface remains to be defined.

<a id="internal-adapters-and-page-mixins"></a>
<a id="gf-040-020"></a>

## 020 · Internal adapters and page mixins

Block ID: **GF-040-020**.

Internal adapters supply services; mixins expose page capabilities. Mixins complement adapters. Composition and method resolution must be explicit; proposed class names are illustrative.

<a id="resource-lifecycle"></a>
<a id="gf-040-025"></a>

## 025 · Resource lifecycle

Block ID: **GF-040-025**.

Server owns dispatch; database adapter owns connection/session/transaction resources. Define acquisition, cleanup, failures and concurrency without leaking request state.

<a id="fake-database-adapter"></a>
<a id="gf-040-030"></a>

## 030 · Fake database adapter

Block ID: **GF-040-030**.

The fake adapter uses the same contract and three small teaching tables. Names, columns, relationships and write behavior remain open; fake results do not establish persistence.

<a id="code-ownership"></a>
<a id="gf-040-035"></a>

## 035 · Code ownership

Block ID: **GF-040-035**.

Host code belongs in host repositories; shared database adapters belong in core contrib. Plain hosting requires neither SQLAlchemy nor Genropy. Legacy Genropy extraction has not established its final shared boundary.

<a id="current-implementation-and-next-decisions"></a>
<a id="gf-040-040"></a>

## 040 · Current implementation and next decisions

Block ID: **GF-040-040**.

FastAPI, legacy Genropy and provisional SQLite/SQLAlchemy are implemented. SQLite uses core DbHandler.dbselect and DbPageMixin through host db_handler. Broader operations/results, teaching schema, capabilities, lifecycle/transactions and shared contract tests remain open.
