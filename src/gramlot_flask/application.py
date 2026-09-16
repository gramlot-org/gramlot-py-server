"""Flask request integration; shared discovery, invocation and assets stay in Gramlot."""
import asyncio
from functools import partial

from flask import Blueprint, Response, abort, current_app, request, send_from_directory
from gramlot.builder import GramlotBuilder
from gramlot.database import DbHandler, DbPageMixin
from gramlot.hosting import PageRegistry, RuntimeAssets, ServiceParameterError, render_document
from gramlot.transport import TYTX_FORMAT, TYTX_MEDIA_TYPE, from_tytx, to_tytx
from werkzeug.exceptions import HTTPException


def mount_gramlot(app, directory, *, prefix="/gramlot", title="Gramlot", db_handler=None,
                  access_check=None):
    """Mount a collection. The caller owns the optional handler and its shutdown.

    access_check runs on every page, recipe and service request, before dispatch;
    it can return a Flask response or abort. Assets contain no application data.
    """
    pages = PageCollection(directory, prefix=prefix, title=title, db_handler=db_handler)
    name = "gramlot_" + prefix.strip("/").replace("/", "_").replace("-", "_")
    blueprint = Blueprint(name, __name__, url_prefix=prefix)

    @blueprint.before_request
    def authorize():
        if access_check and not request.endpoint.startswith(name + ".asset_"):
            return access_check()

    for rule, endpoint, view, methods in [
        ("/", "index", pages.index, ["GET"]),
        ("/recipe", "index_recipe", pages.index_recipe, ["GET"]),
        ("/<name>/", "document", pages.document, ["GET"]),
        ("/<name>/recipe", "recipe", pages.recipe, ["GET"]),
        ("/<name>/rpc/<role>/<method>", "service", pages.service, ["POST"]),
        ("/<name>/rpc/<method>", "rpc", partial(pages.service, role="data"), ["POST"]),
    ]:
        blueprint.add_url_rule(rule, endpoint, view, methods=methods)
    for index, mount in enumerate(pages.runtime.asset_mounts()):
        def asset(filename, mount=mount):
            # Reject symlinks escaping the runtime directory as well as traversal.
            if not (mount.directory / filename).resolve().is_relative_to(mount.directory.resolve()):
                abort(404)
            response = send_from_directory(mount.directory, filename)
            response.headers["Cache-Control"] = (
                "public, max-age=31536000, immutable" if mount.immutable else "no-cache"
            )
            return response
        blueprint.add_url_rule(mount.url_prefix[len(prefix):] + "<path:filename>",
                               f"asset_{index}", asset)
    app.register_blueprint(blueprint)
    app.extensions.setdefault("gramlot", {})[prefix] = pages
    return pages


class PageCollection(PageRegistry):
    def __init__(self, directory, *, prefix, title, db_handler):
        if db_handler is not None and not isinstance(db_handler, DbHandler):
            raise TypeError("db_handler must implement Gramlot DbHandler")
        self.db_handler = db_handler
        super().__init__(directory, prefix=prefix, title=title)
        self.runtime = RuntimeAssets(prefix)
        self.template = self.runtime.document_template()

    async def run_sync(self, function, *args):
        # Keep Flask context and ORM session on the WSGI request thread.
        return function(*args)

    def create_page(self, page_class):
        page = super().create_page(page_class)
        if isinstance(page, DbPageMixin):
            if self.db_handler is None:
                raise RuntimeError("DbPageMixin requires db_handler")
            page.dbhandler = self.db_handler
        return page

    def require_page(self, name):
        if name not in self.pages:
            abort(404)
        return self.pages[name]

    @staticmethod
    def response(value, status=200):
        response = Response(to_tytx(value, TYTX_FORMAT), status=status, mimetype=TYTX_MEDIA_TYPE)
        response.headers["Cache-Control"] = "no-store"
        return response

    def error(self, kind, message, status):
        return self.response({"ok": False, "error": {"kind": kind, "message": message}}, status)

    def html(self, startup):
        response = Response(render_document(self.template, self.runtime, self.title, startup),
                            mimetype="text/html")
        response.headers["Cache-Control"] = "no-store"
        return response

    def index(self):
        return self.html({"recipe": f"{self.prefix}/recipe", "inspector": True})

    def document(self, name):
        page = self.require_page(name)
        return self.html({"recipe": None, "rpc": f"{self.prefix}/{name}/rpc", "main": "main",
                          "inspector": page.source_inspection, "exampleView": page.example_view})

    def index_recipe(self):
        builder = GramlotBuilder("index")
        links = builder.root.nav(aria_label="Pages").ul()
        for name, page in self.pages.items():
            links.li().a(getattr(page, "title", name), href=f"{self.prefix}/{name}/")
        return self.response(builder.source)

    def recipe(self, name):
        self.require_page(name)
        return self.response(asyncio.run(self.invoke(name, "source", "main", {},
                                                     request._get_current_object())))

    def service(self, name, role, method):
        self.require_page(name)
        if role not in ("source", "data"):
            return self.error("role", "Unknown service role", 404)
        registered = self.registered_method(name, method)
        if registered is None:
            return self.error("method", "Service method not found", 404)
        if registered.role != role:
            return self.error("role", "Service role mismatch", 409)
        if request.mimetype != TYTX_MEDIA_TYPE:
            return self.error("request", "Expected TYTX JSON", 415)
        try:
            params = from_tytx(request.get_data().decode("utf-8"), transport=TYTX_FORMAT)
        except Exception:
            return self.error("request", "Invalid TYTX parameters", 400)
        if not isinstance(params, dict):
            return self.error("request", "RPC parameters must be a mapping", 400)
        try:
            result = asyncio.run(self.invoke(name, role, method, params,
                                             request._get_current_object()))
        except ServiceParameterError as error:
            return self.error("parameters", str(error), 422)
        except HTTPException:
            raise
        except Exception:
            current_app.logger.exception("Gramlot service failed")
            return self.error("application", "Service failed", 500)
        return self.response({"ok": True, "result": result})
