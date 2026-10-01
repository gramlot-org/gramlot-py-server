# Gramlot Uvicorn

[![tests](https://github.com/gramlot-org/gramlot-uvicorn/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/gramlot-org/gramlot-uvicorn/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/gh/gramlot-org/gramlot-uvicorn/branch/main/graph/badge.svg)](https://app.codecov.io/gh/gramlot-org/gramlot-uvicorn)
[![Documentation](https://readthedocs.org/projects/gramlot-uvicorn/badge/?version=latest)](https://gramlot-uvicorn.readthedocs.io/en/latest/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

Framework-neutral ASGI adapter for Gramlot Python pages. It connects a trusted
directory of Python `Page` modules to the core `FileHost` and serves the
Gramlot browser runtime, the page documents and the main/source/close
endpoints. Uvicorn is an optional runner; any ASGI server works. The adapter
imports neither Uvicorn nor Kajenn.

| Profile | Page | Runtime |
| --- | --- | --- |
| Python / Uvicorn | Python `Page` | Generic ASGI adapter served by Uvicorn |

## Install

The package is not published on PyPI. Install the released core and the
adapter from this checkout:

```sh
python -m pip install "gramlot>=0.2.0" ".[uvicorn]"
```

Requires Python 3.11 or later and `gramlot` 0.2.0 or later.

## Usage

```python
from gramlot_uvicorn import create_asgi_application

application = create_asgi_application(
    "pages",
    mount_path="/py",
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)
```

```sh
uvicorn your_module:application
```

- `pages`: the directory of Python `Page` modules; it is trusted application
  source.
- `mount_path`: the prefix of the browser URLs when the application is mounted
  below the root. The adapter passes it to `open_page`, which adds it once to
  root-relative URLs; the adapter does not expect it in the ASGI `path`.
- `content_security_policy`: sent as the `Content-Security-Policy` header of
  each HTML page; `{nonce}` is replaced by the nonce of the bootstrap script.
  Without it no header is sent. The strict profile (`'nonce-{nonce}'`) allows
  named logic only; the permissive profile adds `'unsafe-eval'` for inline
  code. See [Usage](docs/010-usage.md).
- `page_ttl` (default 1800 s) and `max_pages` (default 1000) are passed to
  `FileHost`.

The Hello World application of
[gramlot-examples](https://github.com/gramlot-org/gramlot-examples) runs this
adapter with `python -m gramlot_example_app.server.uvicorn`.

## Companion rule

GET and HEAD serve a file of the pages folder whose name ends in `.css` or
`_aux.js`, when its real path is below the pages folder: the `FileHost`
companions `foo.css` and `foo_aux.js`, and `Page.css` files placed there. Every
other file answers 404 and every other method 405. A `Page.css` URL outside the
pages folder is an application asset, served by the application. This is the
companion rule of the core guide
[Classes and hosts](https://github.com/gramlot-org/gramlot/blob/main/docs/public/090-classes-and-hosts.md).

## Tests

```sh
python -m pip install "gramlot>=0.2.0" -e ".[test]"
python -m pytest -q
```

With coverage: `python -m coverage run -m pytest -q && python -m coverage report`.

The workflow `.github/workflows/tests.yml` runs the suite on Python 3.11 and
3.12 against the core released on PyPI (required) and against the `main` branch
of `gramlot-org/gramlot` (informational), and builds the documentation.

## Documentation

- Guides: `docs/` (expanded) and `docs_llm/` (concise), namespace GS, built
  with Sphinx and the Read the Docs theme (`.readthedocs.yaml`).
  Build locally: `python scripts/check_docs.py` (see `CONTRIBUTING.md`).
- Core documentation: [Classes and hosts](https://github.com/gramlot-org/gramlot/blob/main/docs/public/090-classes-and-hosts.md).
- Rules for contributors and coding agents: `AGENTS.md`, `CONTRIBUTING.md`.

[Architecture](docs/005-architecture.md) · [Usage](docs/010-usage.md) ·
[Verification](docs/020-verification.md).
