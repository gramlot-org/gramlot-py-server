# 505 · Kajenn

Document ID: **GP-505**.

Derived from GA-010 (gramlot-kajenn).

[Paired view](../docs/505-kajenn.md).

`gramlot_py_server.kajenn.Application` serves a pages folder as an application
of a Kajenn site. It is a Kajenn `RoutedApplication`. The rules common to every
adapter are in the [Introduction](005-introduction.md) and in
[Writing pages for these hosts](010-writing-pages.md).

<a id="gp-505-005"></a>

## 005 · Install

Block ID: **GP-505-005**.

```sh
python -m pip install "gramlot-py-server[kajenn]"
```

The extra `kajenn` installs `kajenn>=0.6.0`, which provides the command
`kajenn`.

<a id="gp-505-010"></a>

## 010 · Create a project

Block ID: **GP-505-010**.

`gramlot kajenn new` writes the quick start project of the README
([The gramlot command](020-command.md)):

```sh
gramlot kajenn new my-site
cd my-site
python -m pip install -r requirements.txt
kajenn serve config.py --port 8000
```

Beside `pages/index.py`, `pages/index.js` and `requirements.txt` the project has
`config.py`:

`config.py`:

```python
"""Kajenn site: ``kajenn serve config.py --port 8000``, pages under ``/pages/``."""
from pathlib import Path

from kajenn.config.templates import DefaultConfiguration

from gramlot_py_server.kajenn import Application

PAGES = Path(__file__).resolve().parent / "pages"


class Site(DefaultConfiguration):
    def applications_section(self, cfg):
        cfg.applications().application(
            code="pages",
            mount="pages",
            app_class=Application,
            pages=PAGES,
            content_security_policy=(
                "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"
            ),
        ).request(body="raw")
```

Open <http://127.0.0.1:8000/pages/>. The page shows a field with `Ada` and the
text `Hello, Ada`. It has no inline code, so the project sends the strict
profile. Without `--port`, Kajenn binds this configuration to a free port
and the server log prints it. The test `tests/kajenn/test_kajenn_project.py`
creates the project and serves it through a Kajenn `AsgiServer`.

`gramlot kajenn gallery` serves the example gallery with this adapter.

<a id="gp-505-015"></a>

## 015 · Mounting and options

Block ID: **GP-505-015**.

The application is declared in the site recipe, as in the example:

- `app_class=Application` and `pages=` the pages folder.
- `mount=` the mount of the application: a single lowercase URL segment (a
  letter, then letters, digits, `_` or `-`), or `""` for the site root, without
  prefix. Any other value raises `ValueError` ("mount must be a single lowercase
  URL segment or empty") when the application is created.
- `.request(body="raw")`. The request envelope reaches `GramlotServer.call` as
  the TYTX text the browser sent, not through Kajenn's TYTX hydration. Without it every protocol request raises
  `RuntimeError` ("Application requires request(body='raw')") and answers 500.
- `page_ttl`, `max_pages`, `content_security_policy`, `assets` and `collections`,
  with the meaning of the [Uvicorn options](110-configuration.md). There is no
  `mount_path` option: `Application` raises `TypeError` when it is given. The
  option `css_theme` of the core server is not exposed: the base theme is
  `gramlot-base`.

The Kajenn server removes the mount from the request path. The application
passes `/<mount>` to `open_page` as the prefix of the browser URLs and uses it
as the `Path` of the owner cookie: `/pages` in the example. Kajenn routes
`/pages` and `/pages/` alike; the application tells them apart by the ASGI
`raw_path` and answers `/pages` with 301 to `/pages/`, with the query string:
pages link each other with relative URLs. A server that sends no `raw_path`
serves `/pages` as `/pages/`. With `mount=""` the application answers every
path that no other application claims, the prefix is empty and the cookie
`Path` is `/`.

<a id="gp-505-020"></a>

## 020 · What is served and Kajenn specifics

Block ID: **GP-505-020**.

- **Routes.** One `index` route receives every path below the mount,
  `assets/gramlot.js` and `gramlot/rpc` included. It reads `request.path` and
  serves the runtime, the pages, the core themes, the files of `assets`, the
  companions and the protocol URLs.
- **Methods.** A page accepts `GET` only; `HEAD` and every other method answer
  405 `Method not allowed` with `Allow: GET`. A file accepts `GET` and `HEAD`,
  the protocol URLs `POST`. Every 405 carries an `Allow` header.
- **Responses.** Pages, companions and protocol answers carry
  `Cache-Control: no-store`. The runtime carries
  `Content-Type: text/javascript; charset=utf-8` and `Cache-Control: no-cache`.
  Errors are plain text with `Content-Type: text/plain; charset=utf-8`, as in the
  other adapters, for example `Invalid envelope`. The
  outcomes of a call are not errors: they arrive in the 200 response envelope.
- **Request body.** The application reads the raw body and passes it to
  `GramlotServer.call` as text. The adapter fixes no size, and Kajenn 0.5
  reads the whole body before the route runs; a size limit declared on the
  application is kajenn-org/kajenn#32. The media type of `Content-Type` is compared with
  `application/json`; parameters such as `charset` are ignored.
- **Cookies.** The page response carries `gramlot_owner`. In the example the
  Kajenn site also sets its own `session_id` cookie; the adapter does not read
  it.
- **Errors.** An exception of the page's own code while a page opens reaches
  Kajenn, which answers 500. In a call through `/gramlot/rpc` it is the outcome
  `application_error` of a 200 response.
- **Workers.** The page registry lives in the process. Run one worker, or keep
  a browser on the same worker.

<a id="gp-505-025"></a>

## 025 · API reference

Block ID: **GP-505-025**.

`from gramlot_py_server.kajenn import Application`

Module functions, outside `__all__`:

- `serve(pages, *, host="127.0.0.1", port=8000, mount_path="", **options)`:
  declares an `Application` with the Kajenn mount `mount_path` in a Kajenn site
  and serves it; an empty `mount_path` puts it at the site root.
- `commands(verbs)`: adds the verbs `new` and `gallery` of `gramlot kajenn`, an
  entry point of `gramlot_py_server.commands` ([The gramlot command](020-command.md)).

`Application(pages, *, page_ttl=1800, max_pages=1000,
content_security_policy=None, assets=None, collections=(), **kwargs)`: a subclass
of `gramlot_py_server.base.Adapter` ([Uvicorn reference](120-reference.md),
section 020) and of Kajenn's `RoutedApplication`; the other keyword arguments go
to `RoutedApplication`. The site recipe passes them.

- `gramlot_server`: a subclass of the core `GramlotFileServer` built on `pages`
  with the URLs `/assets/gramlot.js`, `/gramlot/rpc`, `/gramlot/close`. Its
  `capabilities` is `["auth"]`; `evaluate_auth(rule, *, owner, identity)`
  evaluates a rule against the tags of `identity`, the Kajenn avatar that the
  application passes with the call. The server keeps no avatar between calls.
- `content_security_policy`: the configured policy or `None`.
- `assets`: the map of URLs to files, `{}` when not given.
- `index`: the route of every path below the mount.
- `mount_path`: `/<mount>`, or `""` at the site root.
- `on_shutdown()`: the Kajenn lifecycle hook; it calls `shutdown()` and forgets
  every open page.
- `read_body(body_raw)`: the raw request body of the site recipe's
  `request(body="raw")`.

Paths below are without the mount.

| Method and path | Answer |
| --- | --- |
| `GET /<page path>` | 200 `text/html; charset=utf-8`, the bootstrap document, with `Set-Cookie: gramlot_owner=…` and, when configured, `Content-Security-Policy`; 404 `Page not found`; 503 `Page capacity reached` |
| `GET /<page path>/index.html`, `GET /index.html` | as `GET /<page path>` for the page `<page path>`, as `GET /` for the page `index` |
| `GET`, `HEAD /assets/gramlot.js` | 200 `text/javascript; charset=utf-8`, the runtime |
| `GET /pages` (the mount without the final slash) | 301, `Location: /pages/` with the query string |
| `GET`, `HEAD /themes/<file>` | 200, the file of the core themes with the media type of its extension; a file the core does not have goes on to the rows below |
| `GET`, `HEAD` of a URL of `assets` | 200, the file with the media type of the map |
| `GET`, `HEAD /<file>.css`, `/<file>.js` | 200 `text/css; charset=utf-8` or `text/javascript; charset=utf-8` when the real path is below the pages folder; 404 `Not found` otherwise |
| `POST /gramlot/rpc`, `/gramlot/close` | as the [Uvicorn endpoints](120-reference.md) |
| other methods | 405 `Method not allowed`, with `Allow`: `GET` on a page path, `GET, HEAD` on a file, `POST` on `/gramlot/*` |

Declare Source fragments with `@source` and mount them with `remote`;
use `dataRpc` for endpoint values and `dataRemote` for lazy Data. See
[Calling the server](https://github.com/gramlot-org/gramlot/blob/main/docs/public/098-server-calls.md#gc-095-100)
and [Remote content and lazy Data](https://github.com/gramlot-org/gramlot/blob/main/docs/public/099-remote-content.md#gc-095-105).

The Kajenn adapter passes the envelope to `GramlotServer.call` as the other
adapters do and announces the capability `auth`: the bootstrap `config` carries
`"capabilities": ["auth"]`. With each call through `/gramlot/rpc` the
application passes the request's Kajenn avatar (`request.avatar()`), or `None`
when the request is anonymous, as the `identity` of `GramlotServer.call`. The
`evaluate_auth` of `gramlot_server` evaluates an `auth` rule with
`genro_toolbox.tags_match` against the tags of that avatar, the evaluation the genro-routes
`AuthPlugin` applies to route entries: no avatar answers `not_authenticated`, tags
that do not satisfy the rule answer `not_authorized`. The avatar comes from the
Kajenn site: for example a `basic_user` with `tags` under
`authentication().credentials()` of the site recipe, sent as HTTP Basic
credentials. Kajenn verifies the `Authorization` header through the route
`/_server/auth/authenticate`, so the site also declares Kajenn's
`ServerApplication` (`kajenn.server_app`, code `_server`); without it a request
with credentials answers 401. A rule with a syntax error is the outcome `application_error`.
Registering the endpoints as genro-routes `RouterNode`s, with the OpenAPI, env
and logging plugins, belongs to genro-kajenn, not to this adapter.

<a id="gp-505-030"></a>

## 030 · Learn authorization through the existing Kajenn identity

Block ID: **GP-505-030**.

**Goal:** distinguish an anonymous request, a refused identity and an allowed
identity, then prove that the next anonymous request loses authorization.
**Before this lesson:** the lesson *Call on click* of the
[examples manual](https://gramlot-examples.readthedocs.io/en/latest/) and the
site configuration above. This is a controlled adapter test walkthrough, not a
new application login system.

### Read the fixture

`tests/kajenn/test_kajenn.py` already defines `auth_site(pages)`. Its site uses
Kajenn's existing Basic credentials and `ServerApplication` from the module
`kajenn.server_app`:

```python
from kajenn.server_app import ServerApplication
```

The existing configuration is:

```python
credentials = cfg.authentication().credentials()
credentials.basic_user(username="ada", password="ada-secret", tags="admin,staff")
credentials.basic_user(username="bob", password="bob-secret", tags="staff")
applications = cfg.applications()
applications.application(code="_server", app_class=ServerApplication)
applications.application(
    code="pages", mount="page", app_class=Application, pages=pages
).request(body="raw")
```

These are local test credentials. The `_server` application verifies each
request's identity; an owner cookie alone does not grant the `admin` tag.
The shared page fixture declares an `@endpoint(auth="admin")` and a Source
fragment containing a public span and `root.div(auth="admin")`.

### Try it and predict the result

Use the repository's development environment, with the core and Kajenn at the
versions that `pyproject.toml` requires. Update the environment rather than
copying a filter into the adapter:

```sh
python -m pip install --upgrade gramlot kajenn
```

Then run:

```sh
python -m pytest -q tests/kajenn/test_kajenn.py -k 'auth_capability or source_auth_filters'
```

Both tests retain the page owner while changing request credentials. Predict
each row before reading its assertions:

| Request identity | Protected endpoint | Source fragment |
| --- | --- | --- |
| Anonymous | `not_authenticated` | Public span only |
| Bob, `staff` | `not_authorized` | Public span only |
| Ada, `admin,staff` | `allowed` | Public span and protected branch |
| Anonymous again | `not_authenticated` | Public span only |

The Source response omits a refused branch before delivery. This differs from
the `hidden=True` branch of the lesson *Call on click*, which is present but
not displayed. The final request proves that a previous allowed request does
not authorize an anonymous one; it does not demonstrate a browser logout
interface. The HTTP calls in these tests observe the protocol and are not
application request code to copy.

### Change it and check yourself

In a local test copy, add `admin` to Bob's tags. Predict and update only Bob's
expected endpoint outcome and protected-branch presence, then rerun the tests.

**Answer:** Bob becomes allowed in both cases. Neither anonymous row changes.
Restore the original fixture after the exercise. Page ownership and identity
remain separate even when a single client makes all four calls.

### The same rules in the lesson

The lesson *Call on click* teaches an endpoint result and error, the default
refusal of an `auth` rule and the server-side omission of protected Source.
Kajenn supplies the existing identity to those same rules; the application needs
no second authorization state in Data, manual hiding controller or alternative
Source representation.

### Limits and next step

The core `GramlotFileServer` provides no identity: this adapter passes the
Kajenn avatar of each call to it. Named resource groups (`js_requires`) still
require a server with a resource system, which genro-kajenn provides; this
authentication capability does not supply it. Continue with the lessons on
`remote` and `dataRemote` in the examples manual and with
[Remote content and lazy Data](https://github.com/gramlot-org/gramlot/blob/main/docs/public/099-remote-content.md#gc-095-105),
which states the form of the method name and the request rule.


<a id="gp-505-035"></a>

## 035 · Shared WebSocket and PageStore

Block ID: **GP-505-035**.

Set `websocket=True` on the Kajenn application declaration to enable the Gramlot
channel. Kajenn routes the connection through `serve_websocket`; the adapter uses
Kajenn's `WebSocket` for accept, text messages, refusal and close. It registers
and releases the connection in Kajenn's native WebSocket registry. The payloads
remain Gramlot's TYTX envelopes, not Kajenn WSX envelopes.

```python
class Site(DefaultConfiguration):
    def applications_section(self, cfg):
        cfg.applications().application(
            code="pages", mount="pages", app_class=Application,
            pages=PAGES, websocket=True,
        ).request(body="raw")
```

The primary page opens `/pages/gramlot/store?pageId=...`; its Gramlot iframe and
popup descendants share that socket through the existing window protocol. Every
page retains its own ID, PageStore and binder subscriptions. The channel carries
initial snapshots, changes, RPC with cancellation, and topic publications in both
directions. A refused publication returns an error for that message; it does not
close the connection. Acceptance precedes subscriber execution.

Kajenn authenticates the handshake using its configured authentication service;
that identity is passed to Gramlot RPC authorization. The Gramlot owner cookie,
same-origin handshake and ownership checks remain mandatory. Connection identity
is resolved at the handshake, as in Kajenn's own WebSocket service. An owner cookie
alone does not authenticate a user. Kajenn's required application handshake cookie,
when configured, must also be present.

The WebSocket option is off by default. For the optional PageStore catalogue:

```sh
gramlot kajenn gallery --mount /py --websocket --catalog /path/to/catalog.json /path/to/pages
```

Use the catalogue and pages from `gramlot_examples/trials/page_store` in the
installed examples package. The ordinary gallery catalogue is unchanged. The
same channel contract is tested on Uvicorn and Kajenn; real-browser tests cover
nested iframe/popup routing, publication metadata and recursive closure. Stores
remain process-local and are closed when their primary connection is lost;
this integration does not add persistence or reconnect/replay.


<a id="gp-505-040"></a>

## 040 · Databases supplied by Kajenn

Block ID: **GP-505-040**.

Page and PageStore expose `db(name=None)` and `async_db(name=None)`. The adapter
passes these calls to its Kajenn application, using Kajenn's default-database
selection and named databases unchanged. The result is the backend's own object;
Gramlot adds no ORM, query translation, automatic commit or database selector.
An unconfigured database raises Kajenn's error. Hosts without database access
raise an explicit error from these methods.

Install the backend separately from the host:

```sh
python -m pip install "gramlot-py-server[kajenn]" "kajenn-db[asqueel]"
# Other available handlers:
python -m pip install "kajenn-db[sqlalchemy]"
python -m pip install "kajenn-db[django]"
```

Declare it with Kajenn's configuration grammar:

```python
from kajenn_db.asqueel import AsqueelDbHandler

class Site(DefaultConfiguration):
    def applications_section(self, cfg):
        cfg.databases(handler_class=AsqueelDbHandler).database(
            code="default", source="shop.xml",
        )
        cfg.applications().application(
            code="pages", mount="pages", app_class=Application,
            pages=PAGES, websocket=True,
        ).request(body="raw")
```

`shop.xml` is an existing Asqueel model/configuration; migration remains a host
administration operation. With `SqlAlchemyDbHandler`, declare `url` instead of
`source`. With `DjangoDbHandler`, configure Django in the process and declare its
`alias`. Multiple named databases may use different handler classes; select one
with `self.db("name")` or `self.async_db("name")`.

A synchronous PageStore controller can load a record when a binder changes its key:

```python
from genro_bag import Bag
from gramlot import Page as BasePage, PageStore as BasePageStore

class Page(BasePage):
    def main(self, root):
        root.dataBinder("customer", "customer")
        root.input(value="^customer.pkey")
        root.div("^customer.status")
        root.div("^customer.record.name")

class PageStore(BasePageStore):
    def main(self, root):
        self.data.set_item("customer", Bag({"record": Bag(), "status": "unset"}))
        root.dataController(func="load_customer", pkey="^customer.pkey")

    def load_customer(self, node, pkey):
        if pkey is None or pkey == "":
            return
        self.data.set_item("customer.status", "loading")
        try:
            row = self.db().table("app.customer").query(
                where="$id=:pkey", pkey=pkey,
            ).fetchRecord()
        except LookupError as error:
            self.data.set_item("customer.error", str(error))
            self.data.set_item("customer.status", "error")
            return
        self.data.set_item("customer.record", Bag(dict(row.items())))
        self.data.set_item("customer.error", "")
        self.data.set_item("customer.status", "loaded")
```

Use the names declared by the application's model. The result and status are
Data; the binder sends their changes to the client. A subscribed controller may
perform the same operation after a publish. For an asynchronous Page endpoint,
use `db = self.async_db()` and await the backend's I/O methods, for example
`await db.table("app.customer").query(where="$id=:pkey", pkey=pkey).fetchRecord()`
with Asqueel. Convert its named row to a Bag before returning it. PageStore's
recipe execution remains synchronous; exposing `async_db` does not activate
asynchronous dataController recipes.

Each HTTP request or WebSocket operation has a Kajenn call context. Repeated
access to a named database within that operation reuses its session. Synchronous
page methods and store controllers execute on Kajenn's pool, and release their
databases on the same worker thread. Do not retain a connection or cursor in a
PageStore or return it to the client. Commit writes explicitly; rollback and
close follow the backend's transaction semantics. In particular, Django defaults
to autocommit: a caller requiring rollback must open an explicit transaction.

Synchronous operations are serialized within this application to protect its
live Bags. Asynchronous Page methods release that gate while awaiting, so their
RPCs can complete independently. A cancelled synchronous worker is drained before
its resources are released; cancellation does not interrupt Python threads or
undo a database commit.

Qualification uses actual SQLite databases with all three handlers. Asqueel
and SQLAlchemy have tested asynchronous views. Django's handler rejects
`async_db`; its synchronous Page/PageStore path is tested with access and cleanup
on the same thread. SQLAlchemy and Django remain probes in kajenn-db; this
integration does not imply every backend capability or every database engine is
qualified. Asqueel, PostgreSQL or other SQLAlchemy engines retain their own driver,
configuration and migration requirements.

**Development qualification limitation:** Kajenn 0.7.0's pool can finish an await
on cancellation while its worker is still running. Async database cleanup may
then race that worker. The issue is reproduced and tracked in [Kajenn #89](https://github.com/kajenn-org/kajenn/issues/89); it must be resolved in Kajenn;
this branch does not claim safe cancellation of an in-flight async database I/O.
This increment requires the matching unreleased core database API; it is not a
claim that the preceding published core already provides these accessors.


<a id="gp-505-045"></a>

## 045 · Customer gallery with Asqueel and SQLite

Block ID: **GP-505-045**.

The optional `gramlot_examples.trials.kajenn_db` catalogue contains customer
read/save pages and their separate PageStore classes. The host runner lives here:

```sh
python scripts/serve_kajenn_db_gallery.py --database /absolute/path/demo/customers.sqlite --port 8768
```

Install the matching development core, adapter and examples, with this adapter's
`kajenn,gallery` extras and `kajenn-db[asqueel]`. The increment is not yet published.
Open `http://127.0.0.1:8768/py/` and expand **Kajenn and Asqueel**. Use a dedicated
demonstration database. A new file is migrated and seeded with customers 1 and 2;
an existing file is preserved and must already match the model. Runtime database
access uses `self.db()` and the native Asqueel handler. Controllers explicitly
commit successful reads/writes and roll back failed operations.

The first lesson loads on a bound key change and saves through a subscribed
controller. Status and error are Bag data; a publication acknowledgement only
confirms acceptance. Missing IDs preserve the previous record and loaded ID;
failed saves preserve the draft. Try an empty name or the other customer's email
to check validation and SQLite's unique constraint. Reload reads stored data.

The second lesson has direct/nested iframes and connected descendant windows.
Each keeps an independent PageStore draft. Save in one, then reload in another:
SQLite supplies the committed record. The last successful save wins; there is
no automatic cross-draft synchronization or conflict detection. All descendants
share the primary gallery's physical WebSocket and close with their parent.
The synchronous controllers do not exercise Kajenn #89's async cancellation case.

Run the browser qualification with:

```sh
node scripts/verify_kajenn_db_gallery.mjs /absolute/path/python /absolute/path/playwright/index.mjs chromium webkit
```

It uses temporary SQLite files and verifies reads, commits, lookup/validation errors,
rollback and recovery, family routing and one physical WebSocket. The optional
`tests/kajenn/test_kajenn_db_gallery.py` checks persistence across startup; it needs
the matching examples catalogue and Asqueel installed. These checks qualify this
local development increment and do not constitute a release or deployment.
