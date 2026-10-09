"""The envelope of ``POST /gramlot/rpc`` for the tests of every adapter (GC-230-020)."""
import json
from uuid import uuid4

from genro_tytx import to_tytx

RPC_HEADERS = {"content-type": "application/json"}


def envelope(page_id, name="main", params=None, content_type="source"):
    """The request envelope as TYTX text: the fragment ``main`` by default."""
    return to_tytx({"id": uuid4().hex, "pageId": page_id, "contentType": content_type,
                    "name": name, "params": {} if params is None else params})


def rpc_source(text):
    """The fragment document (TYTX text) of a response envelope; fails on an outcome."""
    response = json.loads(text)
    assert "error" not in response, response["error"]
    return response["value"]


def rpc_outcome(text):
    """The ``code`` of the outcome of a response envelope; fails on a value."""
    response = json.loads(text)
    assert "error" in response, response
    return response["error"]["code"]
