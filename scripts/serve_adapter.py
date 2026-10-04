"""Serve a pages folder under /py with one adapter, for the browser check.

Usage: python scripts/serve_adapter.py FRAMEWORK PAGES PORT ASSETS_JSON

``ASSETS_JSON`` is the ``assets`` option as JSON: ``{url: {"file": path, "type": media type}}``.
The application sends the strict Content Security Policy profile; ``serve`` of the
adapter module runs the server of the framework.
"""

import importlib
import json
import sys

STRICT_CSP = "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"

if __name__ == "__main__":
    framework, pages, port, assets = sys.argv[1:]
    adapter = importlib.import_module(f"gramlot_py_server.{framework}")
    adapter.serve(pages, host="127.0.0.1", port=int(port), mount_path="/py",
                  content_security_policy=STRICT_CSP, assets=json.loads(assets))
