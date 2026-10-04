"""Serve a pages folder under /py with one adapter, for the browser check.

Usage: python scripts/serve_adapter.py FRAMEWORK PAGES PORT ASSETS_JSON

``ASSETS_JSON`` is the ``assets`` option as JSON: ``{url: {"file": path, "type": media type}}``.
The application sends the strict Content Security Policy profile.
"""

import json
import sys
from pathlib import Path

STRICT_CSP = "script-src 'nonce-{nonce}'; object-src 'none'; base-uri 'none'"
HOST = "127.0.0.1"


def serve(framework, pages, port, assets):
    options = {"content_security_policy": STRICT_CSP, "assets": assets}
    if framework == "uvicorn":
        import uvicorn

        from gramlot_py_server.uvicorn import create_application

        uvicorn.run(create_application(pages, mount_path="/py", **options), host=HOST, port=port)
    elif framework == "fastapi":
        import uvicorn

        from gramlot_py_server.fastapi import Application

        uvicorn.run(Application(pages, mount_path="/py", **options), host=HOST, port=port)
    elif framework == "flask":
        from flask import Flask

        from gramlot_py_server.flask import mount_pages

        app = Flask(__name__)
        mount_pages(app, pages, mount_path="/py", **options)
        app.run(host=HOST, port=port)
    elif framework == "django":
        import django
        from django.conf import settings
        from django.core.management import call_command

        from gramlot_py_server.django import Pages

        settings.configure(
            SECRET_KEY="browser-check-only",
            DEBUG=True,
            ALLOWED_HOSTS=[HOST],
            ROOT_URLCONF=__name__,
            MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
        )
        django.setup()
        globals()["urlpatterns"] = Pages(pages, mount_path="/py", **options).urlpatterns
        call_command("runserver", f"{HOST}:{port}", use_reloader=False)
    elif framework == "kajenn":
        from kajenn import AsgiServer
        from kajenn.config.templates import DefaultConfiguration

        from gramlot_py_server.kajenn import Application

        class Site(DefaultConfiguration):
            def applications_section(self, cfg):
                cfg.applications().application(
                    code="pages", mount="py", app_class=Application, pages=pages, **options,
                ).request(body="raw")

        AsgiServer(config=Site).serve(host=HOST, port=port)
    else:
        raise ValueError(f"Unknown framework: {framework}")


if __name__ == "__main__":
    framework, pages, port, assets = sys.argv[1:]
    serve(framework, Path(pages), int(port), json.loads(assets))
