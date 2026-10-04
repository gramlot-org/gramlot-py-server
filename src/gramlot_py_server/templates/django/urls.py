"""URLconf: the Gramlot pages at the site root."""
from pathlib import Path

from gramlot_py_server.django import Pages

PAGES = Path(__file__).resolve().parent / "pages"

pages = Pages(
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'",
)

urlpatterns = [*pages.urlpatterns]
