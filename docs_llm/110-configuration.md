# 110 · Uvicorn configuration

Document ID: **GP-110**.

Derived from GS-120 (gramlot-uvicorn).

[Paired view](../docs/110-configuration.md).

<a id="gp-110-005"></a>

## 005 · Options

Block ID: **GP-110-005**.

`create_application(pages, **options)` builds an `Application`. Both take the
same options. The Django, Flask and FastAPI adapters take the same options; the
Kajenn adapter takes all of them except `mount_path`.

| Option | Type | Default | Effect |
| --- | --- | --- | --- |
| `pages` | `str` or `Path` | required | the pages folder served by the core `FileHost` |
| `mount_path` | `str` | `""` | the mount prefix of the browser URLs; see section 010 |
| `page_ttl` | `int` or `float`, seconds | `1800` | a page that is not closed expires after this time; must be finite and positive |
| `max_pages` | `int` | `1000` | the number of open pages the process accepts; the next opening answers 503 |
| `content_security_policy` | `str` or `None` | `None` | the `Content-Security-Policy` header of HTML pages; see section 015 |

`page_ttl` and `max_pages` are passed to `FileHost`. A value outside the rule
raises `ValueError` when the application is created.

<a id="gp-110-010"></a>

## 010 · Mount prefix

Block ID: **GP-110-010**.

`mount_path` is the prefix the browser puts before the URLs of this
application, for example `/py` when a front server routes `/py/…` to the
application and strips `/py` before it dispatches. The application passes it
to `open_page` as `prefix`. The core adds it once to the root-relative URLs of
the bootstrap document: runtime, main, source, close, companions and
root-relative `Page.css` URLs. The application does not expect the prefix in
the ASGI `path`. The owner cookie is set with `Path=/py`, or `Path=/` without a
prefix. Leading and trailing slashes are normalized: `"py"`, `"/py"` and
`"/py/"` give `/py`.

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
| Strict | `script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'` | named logic only: methods of the companion `_aux.js` |
| Permissive | `script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'` | named logic and inline code (`formula`, `script`, `==`, button `action`, `connect_on<event>`, `_if`/`_else`) |

Under the strict profile an inline declaration fails in the browser with an
`EvalError` that names the node and the attribute, for example:

```text
dataFormula 'dataFormula_0' 'formula': inline code blocked by the Content Security Policy of the page (no 'unsafe-eval'); move the code to named logic (a method of the page companion _aux.js) or serve the page with the permissive CSP profile, which allows 'unsafe-eval'
```

Nothing is written to the Data and nothing is mounted. The companion module is
imported by the bootstrap script, which carries the nonce, so `script-src`
needs no `'self'`.

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
