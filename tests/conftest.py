"""Fixtures shared by the example tests of every framework."""
import importlib.util
import re
from pathlib import Path

import pytest
from genro_tytx import from_tytx

from gramlot_py_server.cli import main

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def load_module(filename, name):
    """Execute the module file ``filename`` under ``name`` and return it."""
    spec = importlib.util.spec_from_file_location(name, filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def load_example():
    """Return a loader of an example module by its path below ``examples/``."""
    return lambda relative: load_module(EXAMPLES / relative, f"example_{Path(relative).parent.name}")


@pytest.fixture
def new_project(tmp_path):
    """Return a creator of the project of an environment with ``gramlot <environment> new``.

    It returns the project folder and its framework module, loaded by name.
    """

    def create(environment, module=None):
        folder = tmp_path / f"{environment}-project"
        assert main([environment, "new", str(folder)]) == 0
        loaded = None if module is None else load_module(folder / module, f"project_{environment}")
        return folder, loaded

    return create


@pytest.fixture
def source_tags():
    """Return a reader of ``{tag: attributes}`` of a Source document, depth first."""

    def read(source):
        found = {}

        def walk(bag):
            for node in bag.nodes:
                found[node.label.split("_")[0]] = dict(node.attr)
                if hasattr(node.value, "nodes"):
                    walk(node.value)

        walk(from_tytx(source))
        return found

    return read


@pytest.fixture
def page_id():
    """Return a reader of the page ID in a bootstrap document."""
    return lambda document: re.search(r'"pageId":"([0-9a-f]+)"', document).group(1)
