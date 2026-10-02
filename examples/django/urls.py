"""URLconf of the example: the Gramlot pages at the site root."""
from pathlib import Path

from django.urls import include, path

from gramlot_py_server.django import Pages

PAGES = Path(__file__).resolve().parents[1] / "pages"

pages = Pages(
    PAGES,
    content_security_policy="script-src 'nonce-{nonce}' 'unsafe-eval'; object-src 'none'; base-uri 'none'",
)

urlpatterns = [path("", include(pages.urls))]
