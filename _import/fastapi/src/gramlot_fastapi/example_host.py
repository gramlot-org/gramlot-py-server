# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Compose Gramlot's repository examples without putting FastAPI code in core."""

import importlib.util
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .application import mount_gramlot

class Product(TypedDict):
    id: int
    name: str
    price: int
    available: bool


PRODUCTS: tuple[Product, ...] = (
    {"id": 1, "name": "Desk lamp", "price": 49, "available": True},
    {"id": 2, "name": "Notebook", "price": 12, "available": True},
    {"id": 3, "name": "Oak desk", "price": 320, "available": False},
)


class Quote(BaseModel):
    model_config = ConfigDict(strict=True)
    productId: int
    quantity: int = Field(ge=1)
    note: str | None = None


def create_example_application(
    *,
    framework_root: str | Path,
    examples_root: str | Path,
    preview: str | Path,
    navigation_path: str | Path,
    genropy_directory: str | Path | None = None,
    genropy_application=None,
) -> FastAPI:
    """Compose framework-owned examples from explicit checkout paths."""
    framework_root = Path(framework_root).resolve()
    examples_root = Path(examples_root).resolve()
    preview = Path(preview).resolve()
    navigation_path = Path(navigation_path).resolve()
    if not (preview / "index.html").is_file():
        raise ValueError("Build the example preview before creating the host")
    versions = [path for path in (preview / "runtime").iterdir() if path.is_dir()]
    if len(versions) != 1:
        raise ValueError("Expected one generated runtime version; rebuild the examples")

    app = FastAPI(title="Gramlot examples")
    mount_gramlot(app, framework_root / "tools/gramlot-ide", prefix="/ide", title="Gramlot IDE")

    @app.get("/page/gramlot-ide-local/", include_in_schema=False)
    def local_ide_redirect():
        return RedirectResponse("/ide/index/")

    mount_gramlot(app, examples_root / "triangle-rpc", prefix="/page", title="Triangle RPC")
    mount_gramlot(app, examples_root / "chartbox", prefix="/charts", title="Grid and chartBox")
    mount_gramlot(
        app, examples_root / "grid-editor", prefix="/grid-editor", title="Editable grid",
    )
    navigation_host = mount_gramlot(
        app, examples_root / "hello", prefix="/hello", title="Hello pages",
    )
    spec = importlib.util.spec_from_file_location("gramlot_example_navigation", navigation_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load example navigation: {navigation_path}")
    navigation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(navigation)
    entries = navigation.catalogue(preview, database=genropy_application is not None)

    @app.get("/example-navigation/")
    def navigation_document(current: str = "/"):
        query = urlencode({"current": current})
        return navigation_host.html_document(
            f"/example-navigation/recipe?{query}", inspector=False,
        )

    @app.get("/example-navigation/recipe")
    def navigation_recipe(current: str = "/"):
        return navigation_host.recipe_response(navigation.recipe(entries, current))

    app.add_middleware(
        navigation.ExampleNavigationShell, imports=navigation_host.runtime.import_map(),
    )

    if genropy_application is not None:
        if genropy_directory is None:
            raise ValueError("genropy_directory is required when the database profile is enabled")
        from .genropy import mount_genropy

        mount_genropy(
            app,
            genropy_directory,
            prefix="/database",
            genropy_application=genropy_application,
            title="Database examples",
        )

    @app.get("/api/products")
    def products(q: str = "", available: bool | None = None):
        return [
            product for product in PRODUCTS
            if q.lower() in product["name"].lower()
            and (available is None or product["available"] == available)
        ]

    @app.get("/api/products/{product_id}")
    def product(product_id: int):
        row = next((item for item in PRODUCTS if item["id"] == product_id), None)
        if row is None:
            raise HTTPException(404, "Product not found")
        return row

    @app.post("/api/quote")
    def quote(request: Quote):
        row = next((item for item in PRODUCTS if item["id"] == request.productId), None)
        if row is None:
            raise HTTPException(422, "Choose a valid product ID")
        return {
            "product": row["name"],
            "quantity": request.quantity,
            "total": row["price"] * request.quantity,
            "currency": "EUR",
            "note": request.note,
        }

    for directory in versions[0].iterdir():
        if directory.is_dir():
            app.mount(f"/runtime/{directory.name}", StaticFiles(directory=directory))
    app.mount(
        "/openapi", StaticFiles(directory=examples_root / "gramlot-api-poc", html=True),
    )
    app.mount("/", StaticFiles(directory=preview, html=True))
    return app


__all__ = ["create_example_application"]
