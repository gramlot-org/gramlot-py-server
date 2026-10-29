"""Shared channel contract through raw ASGI."""
from gramlot_py_server.uvicorn import create_application
from page_store_checks import PageStoreChecks


class TestPageStore(PageStoreChecks):
    create_application = staticmethod(create_application)
