"""Loopback load-test application using isolated users and server page stores."""

import os
from pathlib import Path

from genro_routes import route
from genro_storage import StorageManager
from gramlot_py_server.kajennspa import Application
from kajenn import AuthApplicationBase
from kajenn.config.templates import DefaultConfiguration


class BenchAuth(AuthApplicationBase):
    def on_startup(self):
        super().on_startup()
        digest = self.store.hash_password(os.environ["BENCH_PASSWORD"])
        for index in range(int(os.environ["BENCH_USERS"])):
            self.store.save_user(
                {
                    "identity": f"u{index}",
                    "status": "confirmed",
                    "tags": [],
                    "groups": [],
                    "password_hash": digest,
                }
            )


class BenchApp(Application):
    def __init__(self, *, pages, page_limit=None, **kwargs):
        super().__init__(**kwargs)
        options = {"max_pages": page_limit} if page_limit is not None else {}
        self.dispatcher = self.add_pages("pages", pages, **options)

    @route()
    def ready(self):
        return {
            "pid": os.getpid(),
            "max_pages": self.dispatcher.gramlot_server.max_pages,
        }


class Site(DefaultConfiguration):
    def storage_section(self, cfg):
        storage = cfg.storage(app=StorageManager, storage_key=os.environ["BENCH_KEY"])
        for name in ("site", "home"):
            storage.local(name=name, base_path=os.environ["BENCH_HOME"])

    def applications_section(self, cfg):
        apps = cfg.applications()
        apps.application(code="_auth", app_class=BenchAuth)
        options = {"spawner": "subprocess"} if os.environ["BENCH_MODE"] == "subprocess" else {}
        if os.environ.get("BENCH_PAGE_LIMIT"):
            options["page_limit"] = int(os.environ["BENCH_PAGE_LIMIT"])
        apps.application(
            code="bench",
            app_class=BenchApp,
            pages=str(Path(__file__).with_name("pages")),
            **options,
        )
