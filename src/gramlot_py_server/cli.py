# Copyright 2026 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""The ``gramlot`` command: ``gramlot <environment> <verb>``.

Each environment is an entry point of the group ``gramlot_py_server.commands``
whose value is a function ``commands(subparsers)``: it adds the verbs of that
environment. The five adapters of this package register ``uvicorn``,
``django``, ``flask``, ``fastapi`` and ``kajenn``; another package can register
its own. Only the chosen environment is imported, so ``gramlot --help`` needs
no framework.
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import EntryPoint, entry_points

GROUP = "gramlot_py_server.commands"


def environments() -> dict[str, EntryPoint]:
    """The registered environments by name."""
    return {entry.name: entry for entry in entry_points(group=GROUP)}


def load_commands(entry: EntryPoint):
    """Import the ``commands`` of an environment, or explain the missing extra."""
    try:
        return entry.load()
    except ModuleNotFoundError as error:
        raise SystemExit(
            f"gramlot {entry.name}: {error.name} is not installed. "
            f'Install the extra: python -m pip install "gramlot-py-server[{entry.name}]"'
        ) from error


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    found = environments()
    parser = argparse.ArgumentParser(
        prog="gramlot", description="Create and serve Gramlot projects: gramlot <environment> <verb>.")
    parser.add_argument("environment", choices=sorted(found), help="the server environment")
    parser.add_argument("arguments", nargs=argparse.REMAINDER, help="the verb and its arguments")
    chosen = parser.parse_args(argv[:1] or argv)
    commands = load_commands(found[chosen.environment])
    environment = argparse.ArgumentParser(prog=f"gramlot {chosen.environment}")
    verbs = environment.add_subparsers(dest="verb", required=True, metavar="VERB")
    commands(verbs)
    options = environment.parse_args(argv[1:])
    status: int = options.run(options)
    return status


if __name__ == "__main__":
    sys.exit(main())
