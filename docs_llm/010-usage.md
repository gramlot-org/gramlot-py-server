# 010 · Usage

Document ID: **GS-010**.

<a id="gs-010-025"></a>
## 025 · Run Python pages with Uvicorn

Install the Gramlot core, then `python -m pip install ".[uvicorn]"` from the
Uvicorn checkout and a Gramlot Python page package. Expose the ASGI application from a Python module:

```python
from gramlot_uvicorn import create_asgi_application
application = create_asgi_application("pages")
```

Run `uvicorn your_module:application`. The pages directory is trusted application
source. The Hello World package provides
`python -m gramlot_example_app.server.uvicorn` as a ready-to-run example.
No Kajenn dependency is required for this profile.

<a id="gs-010-035"></a>
## 035 · Content Security Policy

The application chooses the policy and passes it as `content_security_policy`:

```python
application = create_asgi_application(
    "pages", content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"
)
```

The adapter sends it as the `Content-Security-Policy` header of each HTML page.
`{nonce}` is replaced by the nonce that `open_page` puts on the bootstrap
script; it changes at every opening. Without the parameter no header is sent.

| Profile | `script-src` | Page logic |
| --- | --- | --- |
| Strict | `'nonce-{nonce}'`, no `'unsafe-eval'` | Named logic only; inline code raises an error |
| Permissive | `'nonce-{nonce}' 'unsafe-eval'` | Named logic and inline code |

The companion `foo_aux.js` is imported by the bootstrap script, so the nonce
covers it; no `'self'` is needed in `script-src`.
