"""Checks of the HTTP rules of the shared adapter base, the same on every adapter (GC-101 Part B)."""
from http.cookies import Morsel, SimpleCookie

# The methods that a page path refuses, HEAD included.
REFUSED_ON_A_PAGE = ("HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS")
# The URLs, below the mount path, that every adapter answers with Cache-Control: no-store, and how.
NO_STORE_URLS = ("/", "/index.css", "/index_aux.js", "/extra/logo.svg", "/missing", "/missing.css")
# The runtime and the core themes carry Cache-Control: no-cache and an ETag, as in the JavaScript servers.
RUNTIME_URL = "/assets/gramlot.js"
THEME_URL = "/themes/gramlot-base/theme.css"
REVALIDATED_URLS = (RUNTIME_URL, THEME_URL)
RULES_PAGE = """from gramlot import Page as BasePage
class Page(BasePage):
    title = 'Rules'
    def main(self, root): root.h1('Rules')
"""


def rules_pages(tmp_path):
    """Write the page ``index`` with its companions below ``tmp_path``; return the pages folder and the ``assets``."""
    folder = tmp_path / "pages"
    folder.mkdir()
    (folder / "index.py").write_text(RULES_PAGE)
    (folder / "index.css").write_text("h1 { color: teal; }\n")
    (folder / "index_aux.js").write_text("export class Logic {}\n")
    (tmp_path / "logo.svg").write_text("<svg/>")
    return folder, {"/extra/logo.svg": {"file": tmp_path / "logo.svg", "type": "image/svg+xml"}}


def lowered(headers):
    """The headers as ``{lowercase name: value}``."""
    return {name.lower(): value for name, value in headers.items()}


def check_refusal(method, status, headers, allowed="GET"):
    """The answer to ``method`` is 405 and its ``Allow`` header is exactly ``allowed``."""
    assert status == 405, method
    assert lowered(headers).get("allow") == allowed, method


def check_no_store(url, headers):
    """The response of ``url`` carries ``Cache-Control: no-store``."""
    assert lowered(headers).get("cache-control") == "no-store", url


def check_no_cache(url, headers):
    """The response of ``url`` carries ``Cache-Control: no-cache``, a strong ``ETag`` and ``Last-Modified``."""
    headers = lowered(headers)
    assert headers.get("cache-control") == "no-cache", url
    assert headers.get("etag", "").startswith('"'), url
    assert headers.get("last-modified", "").endswith(" GMT"), url


def check_owner_cookie(cookie, path):
    """The owner cookie: a ``Morsel``, or the text of a ``Set-Cookie`` header; return its value."""
    morsel = cookie if isinstance(cookie, Morsel) else SimpleCookie(cookie)["gramlot_owner"]
    assert morsel.key == "gramlot_owner"
    assert morsel["path"] == path
    assert morsel["httponly"]
    assert morsel["samesite"].lower() == "lax"
    assert morsel["max-age"] == "" and morsel["expires"] == ""
    return morsel.value
