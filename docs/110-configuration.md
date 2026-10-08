# 110 · Uvicorn configuration

Document ID: **GP-110**.

Derived from a guide of the archived gramlot-uvicorn repository.

[Paired view](../docs_llm/110-configuration.md).

<a id="gp-110-005"></a>

## 005 · Options

Block ID: **GP-110-005**.

`create_application(pages, **options)` builds an `Application`. Both take the
same options. The Django, Flask and FastAPI adapters take the same options; the
Kajenn adapter takes all of them except `mount_path`, whose role its Kajenn
`mount` plays.

| Option | Type | Default | Effect |
| --- | --- | --- | --- |
| `pages` | `str` or `Path` | required | the pages folder served by the core `GramlotFileServer` |
| `mount_path` | `str` | `""` | the mount prefix of the browser URLs; see section 010 |
| `page_ttl` | `int` or `float`, seconds | `1800` | a page that is not closed expires after this time; must be finite and positive |
| `max_pages` | `int` | `1000` | the number of open pages the process accepts; the next opening answers 503 |
| `content_security_policy` | `str` or `None` | `None` | the `Content-Security-Policy` header of HTML pages; see section 015 |
| `assets` | `dict` or `None` | `None` | URLs below the prefix served from files; see section 030 |

`page_ttl` and `max_pages` are passed to `GramlotFileServer`. A value outside the rule
raises `ValueError` when the application is created.

The environment variable `GRAMLOT_DEV` of the core applies to every adapter.
Unset, the runtime URL serves the minified `gramlot.min.js` and each page file
runs once per process. `YES` runs the page file again at each opening. `DEBUG`
also serves the readable `gramlot.js`. Any other value raises `ValueError`.

<a id="gp-110-010"></a>

## 010 · Mount prefix

Block ID: **GP-110-010**.

`mount_path` is the prefix of the URLs of this application, for example
`/py`. The ASGI `path` carries it: the application answers `/py/…` with the
prefix removed, and 404 to every other path. `/py` without the final slash
answers 301 to `/py/`, with the query string, because pages link each other
with relative URLs. The application passes the prefix to `open_page` as
`prefix`. The core adds it once to the root-relative URLs of the bootstrap
document: runtime, main, source, close, companions and root-relative
`Page.css` URLs. The owner cookie is set with `Path=/py`, or `Path=/` without
a prefix. Leading and trailing slashes are normalized: `"py"`, `"/py"` and
`"/py/"` give `/py`.

The rule is the same in the Django, Flask and FastAPI adapters. Until 0.2.1
the Uvicorn application expected the prefix removed by a front server; a
proxy that removes it now makes every request answer 404.

<a id="gp-110-015"></a>

## 015 · Content Security Policy

Block ID: **GP-110-015**.

The application chooses the policy. Gramlot defines two profiles and never sets
the header itself. The adapter sends the configured string as the
`Content-Security-Policy` header of every HTML page, with `{nonce}` replaced by
the nonce of the bootstrap script of that opening. The header is not sent on
the runtime, the companions or the protocol responses. It is not sent at all
when the option is `None`. The rule is the same in all five adapters.

| Profile | Value | Pages that run |
| --- | --- | --- |
| Strict | `script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'` | named logic only: methods of the page's `class Logic` |
| Permissive | `script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'` | named logic and inline code (`formula`, `script`, `==`, button `action`, `connect_on<event>`, `_if`/`_else`) |

Under the strict profile an inline declaration fails in the browser with an
`EvalError` that names the node and the attribute, for example:

```text
dataFormula 'dataFormula_0' 'formula': inline code blocked by the Content Security Policy of the page (no 'unsafe-eval'); move the code to named logic (a method of the page's class Logic) or serve the page with the permissive CSP profile, which allows 'unsafe-eval'
```

Nothing is written to the Data and nothing is mounted. The logic module is
imported by the bootstrap script, which carries the nonce, so `script-src`
needs no `'self'`. The import map that resolves `@gramlot/gramlot/page` carries
the same nonce.

<a id="gp-110-020"></a>

## 020 · Owner and request identity

Block ID: **GP-110-020**.

The first `GET` of a page sets the cookie `gramlot_owner` (`HttpOnly`,
`SameSite=Lax`, `Path` as in section 010) with a random token when the browser
sends none. Every page opened by that browser is registered with this token as
its owner. `main`, `source` and `close` succeed only when the request carries
the cookie of the owner. Otherwise the page is "Unknown" and the answer is 404.
A page ID is not a login: the cookie identifies a browser, not a user. The
application adds its own authentication in front of the adapter.

<a id="gp-110-025"></a>

## 025 · Limits

Block ID: **GP-110-025**.

- Protocol requests (`main`, `source`, `close`) must be `POST` with
  `Content-Type: application/json`. Another media type answers 415.
- A request body above 4096 bytes answers 413.
- A body that is not a JSON object with a string `pageId` answers 400.
  `params` of a Source request must be a JSON object.
- Every response of this adapter carries `Cache-Control: no-store`, the runtime
  included.
- The page registry lives in the process: pages opened by one worker are
  unknown to another. On `lifespan.shutdown` the application forgets every
  open page.

<a id="gp-110-030"></a>

## 030 · Assets

Block ID: **GP-110-030**.

`assets` maps URLs below the mount prefix to files. Each value has `file`, a
path, and `type`, the media type of the answer:

```python
from gramlot_examples import build_gallery

application = create_application(
    "pages", mount_path="/py", assets=build_gallery()["assets"],
)
```

`GET` and `HEAD` of a URL of the map answer the file with its media type and
`Cache-Control: no-store`; another method answers 405. The map comes before the
companions and the pages, and after the runtime `/assets/gramlot.js` and the
core themes `/themes/…`, which every adapter serves without configuration. The form
is the `assets` part of `build_gallery` of `gramlot-examples`, which serves the
example gallery. A URL outside the map follows the rules of
[What is served](010-writing-pages.md).
