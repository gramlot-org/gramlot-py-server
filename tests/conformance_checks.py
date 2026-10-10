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
framework, pages, port, mount_path, policy = sys.argv[1:]
import_module('gramlot_py_server.' + framework).serve(
    pages, host='127.0.0.1', port=int(port), mount_path=mount_path,
    content_security_policy=policy or None)
"""
# The conformance cases: no mount prefix and no policy, a mount prefix and the strict policy.
CASES = [("", None), ("/py", STRICT_CSP)]
CASE_IDS = ["root", "mount-and-policy"]


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
def served(framework, pages, mount_path, policy, timeout=30):
    """Run ``serve`` of the adapter module until the block ends; yield the base URL."""
    port = free_port()
    process = subprocess.Popen(
        [sys.executable, "-c", SERVE, framework, str(pages), str(port), mount_path, policy or ""],
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


def check_adapter(framework, tmp_path, mount_path, policy):
    """Check the index page (``/``) and the page ``/orders`` of one running adapter."""
    pages = conformance_pages(tmp_path)
    with served(framework, pages, mount_path, policy) as base_url:
        check_protocol(base_url, "/")
        check_protocol(base_url, "/orders")
