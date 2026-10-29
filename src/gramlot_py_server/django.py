# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Translate the Gramlot server protocol into Django views and URLs."""

from __future__ import annotations

import inspect
from pathlib import Path
from secrets import token_urlsafe

from asgiref.sync import async_to_sync, iscoroutinefunction, sync_to_async
from django.http import HttpRequest, HttpResponse
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from gramlot_py_server import base
from gramlot_py_server.collection_resources import _CollectionFileServer
from gramlot_py_server.gallery import add_gallery
from gramlot_py_server.scaffold import add_new


class _DjangoFileServer(_CollectionFileServer):
    """Run synchronous page/ORM calls in Django's thread-sensitive context."""

    async def _invoke(self, function, *args, **kwargs):
        if iscoroutinefunction(function):
            return await function(*args, **kwargs)
        result = await sync_to_async(function, thread_sensitive=True)(*args, **kwargs)
        return await result if inspect.isawaitable(result) else result


class Pages(base.Adapter):
    """Own a Gramlot ``GramlotFileServer`` and expose it at one Django URLconf mount point.

    Add ``urlpatterns`` to the URLconf: it includes ``urls`` at ``mount_path``,
    which is also passed to ``open_page`` as the mount prefix of browser URLs.
    The prefix without the final slash (``/py``) answers 301 to ``/py/``: pages
    link each other with relative URLs. The cookie associates browser requests
    with in-process page records; it is not authentication.

    Django has no shutdown signal: the registered pages are forgotten when the
    interpreter exits or the ``Pages`` is collected (``close_at_exit``).
    The HTTP rules, the same in every adapter, are those of ``gramlot_py_server.base``.
    """

    server_class = _DjangoFileServer

    def __init__(self, pages: str | Path, **options) -> None:
        super().__init__(pages, **options)
        self.finalizer = self.close_at_exit()
        # Exempt from CSRF so that a POST answers 405 here, not 403 from the middleware.
        self.urls = [
            path("", csrf_exempt(self.view)),
            path("<path:page_path>", csrf_exempt(self.view)),
        ]

    @property
    def urlpatterns(self):
        """The URL patterns of the pages at ``mount_path``, with the redirect of the bare prefix."""
        if not self.mount_path:
            return [path("", include(self.urls))]
        prefix = self.mount_path.strip("/")
        return [path(prefix, csrf_exempt(self.mount_view)), path(prefix + "/", include(self.urls))]

    def mount_view(self, request: HttpRequest) -> HttpResponse:
        """The bare mount prefix."""
        return self.response(self.redirect(request.META.get("QUERY_STRING", "")))

    def view(self, request: HttpRequest, page_path: str = "") -> HttpResponse:
        """Every URL below the mount prefix."""
        reply = async_to_sync(self.handle)(base.Request(
            method=request.method or "GET",
            path="/" + page_path,
            body=base.stored(request.body),
            query=request.META.get("QUERY_STRING", ""),
            content_type=request.META.get("CONTENT_TYPE", ""),
            owner=request.COOKIES.get(self.OWNER_COOKIE),
        ))
        return self.response(reply)

    @staticmethod
    def response(reply: base.Reply) -> HttpResponse:
        """The Django response of a ``Reply``."""
        response = HttpResponse(reply.body, status=reply.status, content_type=reply.content_type)
        for name, value in reply.headers:
            if name == "Set-Cookie":
                # The test client keeps the cookies of ``response.cookies``, not the header.
                response.cookies.load(value)
            else:
                response[name] = value
        return response


class _URLconf:
    """A ``ROOT_URLCONF`` object: Django reads its ``urlpatterns`` and caches it by identity."""

    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns


def serve(pages: str | Path, *, host: str = "127.0.0.1", port: int = 8000, **options) -> None:
    """Serve ``pages`` with the Django development server until it stops.

    Django is configured here with the URLconf of one ``Pages``: the process must
    not have configured it before.
    """
    import django
    from django.conf import settings
    from django.core.management import call_command

    settings.configure(
        SECRET_KEY=token_urlsafe(32),
        ALLOWED_HOSTS=["127.0.0.1", "localhost", host],
        ROOT_URLCONF=_URLconf(Pages(pages, **options).urlpatterns),
        MIDDLEWARE=["django.middleware.csrf.CsrfViewMiddleware"],
    )
    django.setup()
    call_command("runserver", f"{host}:{port}", use_reloader=False)


def commands(verbs) -> None:
    """The verbs of ``gramlot django``: an entry point of ``gramlot_py_server.commands``."""
    add_new(verbs, "django", start="django-admin runserver --settings=settings --pythonpath=.", url="http://127.0.0.1:8000/")
    add_gallery(verbs, "django", serve)


__all__ = ["Pages"]
