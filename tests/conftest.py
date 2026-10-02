"""Fixtures shared by the example tests of every framework."""
import importlib.util
import re
from pathlib import Path

import pytest
from genro_tytx import from_tytx

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def load_example():
    """Return a loader of an example module by its path below ``examples/``."""

    def load(relative):
        filename = EXAMPLES / relative
        spec = importlib.util.spec_from_file_location(f"example_{filename.parent.name}", filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    return load


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
