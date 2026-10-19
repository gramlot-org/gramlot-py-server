# 505 · Kajenn

Document ID: **GP-505**.

Derived from GA-010 (gramlot-kajenn).

[Paired view](../docs_llm/505-kajenn.md).

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

The extra `kajenn` installs `kajenn>=0.4.1`, which provides the command
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
- `page_ttl`, `max_pages`, `content_security_policy` and `assets`, with the
  meaning of the [Uvicorn options](110-configuration.md). There is no
  `mount_path` option.

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
  `GramlotServer.call` as text. The adapter fixes no size, and Kajenn 0.1
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
content_security_policy=None, assets=None, **kwargs)`: the other keyword arguments go to
Kajenn's `RoutedApplication`. The site recipe passes them.

- `gramlot_server`: a subclass of the core `GramlotFileServer` built on `pages`
  with the URLs `/assets/gramlot.js`, `/gramlot/rpc`, `/gramlot/close`. Its
  `capabilities` is `["auth"]`; `evaluate_auth(rule, *, owner, identity)`
  evaluates a rule against the tags of `identity`, the Kajenn avatar that the
  application passes with the call. The server keeps no avatar between calls.
- `content_security_policy`: the configured policy or `None`.
- `assets`: the map of URLs to files, `{}` when not given.
- `index`: the route of every path below the mount.
- `mount_path`: `/<mount>`, or `""` at the site root.
- `on_shutdown()`: the Kajenn lifecycle hook; it forgets every open page.
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
use `dataRpc` for endpoint values and `dataRemote` for lazy Data. See the
[shared authoring guide](https://github.com/gramlot-org/gramlot/blob/main/docs/public/095-writing-pages.md#gc-095-100).

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

**Release stage:** core 0.2.14 endpoint rules, then 0.2.15 Source rules.
**Goal:** distinguish an anonymous request, a refused identity and an allowed
identity, then prove that the next anonymous request loses authorization.
**Before this lesson:** [c11 Call on click](https://github.com/gramlot-org/gramlot-examples/blob/main/src/gramlot_examples/pages/controllers/11_call_on_click.md) and the site
configuration above. This is a controlled adapter test walkthrough, not a new
application login system.

### Read the fixture

`tests/kajenn/test_kajenn.py` already defines `auth_site(pages)`. Its site uses
Kajenn's existing Basic credentials and `ServerApplication` from the current
`kajenn.server_app` module. Older Kajenn installations used the separate import
name `kajenn_server_app`; update Kajenn rather than adding an import fallback:

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

Use the repository's configured development environment with the current
released core. Source-element authorization requires core 0.2.15 or later; an
older 0.2.14 installation can pass the endpoint test while failing the Source
filtering test. Update the environment rather than copying a filter into the
adapter:

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
c11's `hidden=True` branch, which is present but not displayed. The final request
proves that a previous allowed request does not authorize an anonymous one; it
does not demonstrate a browser logout interface. The HTTP calls in these tests
observe the protocol and are not application request code to copy.

### Change it and check yourself

In a local test copy, add `admin` to Bob's tags. Predict and update only Bob's
expected endpoint outcome and protected-branch presence, then rerun the tests.

**Answer:** Bob becomes allowed in both cases. Neither anonymous row changes.
Restore the original fixture after the exercise. Page ownership and identity
remain separate even when a single client makes all four calls.

### The same example across stages

c11 first taught an endpoint result/error and default refusal. Its later section
adds server-side Source omission. Kajenn now supplies the existing identity to
those same rules; the application needs no second authorization state in Data,
manual hiding controller or alternative Source representation.

### Limits and next step

The common FileServer does not provide an identity. Named resource groups still
require the separate genro-kajenn resource host; this authentication capability
does not supply it. Continue with c12–c14 at the core 0.2.16 stage, keeping remote
method names fixed and allowing only the documented variable parameters.
