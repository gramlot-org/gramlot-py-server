"""Run the core conformance check of the server protocol GC-230 against one adapter.

The adapter runs with the ``serve`` of its module in a child process, on a free
port, and ``check_protocol`` of ``gramlot.server`` talks to it over HTTP.
"""
import socket
import subprocess
import sys
import time
from contextlib import contextmanager

from gramlot.server import check_protocol

STRICT_CSP = "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"
# The fragment and the endpoints that check_protocol calls, as in the core fixture page.
PAGE = """from gramlot import Page as BasePage, endpoint, source
class Page(BasePage):
    title = '{title}'
    def main(self, root): root.h1('{title}')
    @source
    def check_fragment(self, root, text='check'): root.span(text)
    @source
    def check_fragment_auth(self, root):
        root.span('check-public')
        root.div(auth='admin').span('check-refused')
    @endpoint
    def check_endpoint(self, value): return value
    @endpoint(auth='admin')
    def check_endpoint_auth(self): return 'allowed'
    @endpoint
    def check_endpoint_raise(self): raise ValueError('check')
"""
SERVE = """import sys
from importlib import import_module
framework, pages, port, mount_path, policy, page_ttl = sys.argv[1:]
import_module('gramlot_py_server.' + framework).serve(
    pages, host='127.0.0.1', port=int(port), mount_path=mount_path,
    content_security_policy=policy or None, **({'page_ttl': float(page_ttl)} if page_ttl else {}))
"""
# The conformance cases: no mount prefix, no policy and a short page_ttl for the check of the expiry
# (GC-230 item 18, which takes about 2.5 times page_ttl), a mount prefix and the strict policy.
PAGE_TTL = 2
CASES = [("", None, PAGE_TTL), ("/py", STRICT_CSP, None)]
CASE_IDS = ["root-and-page-ttl", "mount-and-policy"]


def conformance_pages(folder):
    """Write the index page with its companion stylesheet and logic, and the page ``orders``."""
    (folder / "index.py").write_text(PAGE.format(title="Index"))
    (folder / "index.css").write_text("h1 { color: teal; }\n")
    (folder / "index_aux.js").write_text("export class Logic {}\n")
    (folder / "orders.py").write_text(PAGE.format(title="Orders"))
    return folder


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@contextmanager
def served(framework, pages, mount_path, policy, page_ttl=None, timeout=30):
    """Run ``serve`` of the adapter module until the block ends; yield the base URL."""
    port = free_port()
    process = subprocess.Popen(
        [sys.executable, "-c", SERVE, framework, str(pages), str(port), mount_path, policy or "",
         "" if page_ttl is None else str(page_ttl)],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
    )
    try:
        deadline = time.monotonic() + timeout
        while True:
            if process.poll() is not None:
                raise RuntimeError(f"The {framework} server exited with {process.returncode}:\n"
                                   f"{process.stderr.read()}")
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"The {framework} server did not listen on {port}")
                time.sleep(0.1)
        yield f"http://127.0.0.1:{port}{mount_path}"
    finally:
        process.terminate()
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


def check_adapter(framework, tmp_path, mount_path, policy, page_ttl):
    """Check the index page (``/``) and the page ``/orders`` of one running adapter.

    With ``page_ttl`` the adapter runs with that page lifetime and the check of ``/orders`` includes
    the renewal and the expiry of a page.
    """
    pages = conformance_pages(tmp_path)
    with served(framework, pages, mount_path, policy, page_ttl) as base_url:
        check_protocol(base_url, "/")
        check_protocol(base_url, "/orders", page_ttl=page_ttl)
