# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""Discover Gramlot pages and serve them with FastAPI."""

import argparse
from pathlib import Path

from .application import GramlotApplication


class Cli:
    """Parse the development-server command and start Uvicorn."""

    def run(self) -> None:
        parser = argparse.ArgumentParser(description=__doc__)
        commands = parser.add_subparsers(dest="command", required=True)
        serve = commands.add_parser("serve", help="Discover pages and start FastAPI")
        serve.add_argument("directory", nargs="?", type=Path, default=Path.cwd())
        serve.add_argument("--host", default="127.0.0.1")
        serve.add_argument("--port", type=int, default=8000)
        serve.add_argument("--prefix", default="/page")
        options = parser.parse_args()
        self.serve(parser, options)

    @staticmethod
    def serve(parser: argparse.ArgumentParser, options: argparse.Namespace) -> None:
        import uvicorn

        try:
            app = GramlotApplication(directory=options.directory, prefix=options.prefix)
        except (ValueError, OSError) as error:
            parser.error(str(error))
        uvicorn.run(app, host=options.host, port=options.port)


def main() -> None:
    Cli().run()


if __name__ == "__main__":
    main()
