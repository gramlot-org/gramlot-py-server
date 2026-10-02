# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Serve the common Gramlot showcase through FastAPI."""
from fastapi.responses import RedirectResponse
import uvicorn

from gramlot.showcase import get_showcase_directory
from gramlot_fastapi import GramlotApplication


def create_app():
    app = GramlotApplication(get_showcase_directory(), title='gramlot.showcase')

    @app.get('/', include_in_schema=False)
    def home():
        return RedirectResponse('/page/index/')

    return app


if __name__ == '__main__':
    uvicorn.run(create_app(), host='127.0.0.1', port=8075)
