"""The HTTP rules of the shared adapter base, without a framework."""
import gc
import re
import weakref
from http.cookies import SimpleCookie
from pathlib import Path

import pytest

from gramlot_py_server import base


@pytest.fixture
def adapter(tmp_path):
    return base.Adapter(tmp_path, mount_path="py/")


def test_mount_path_is_normalised(tmp_path):
    assert base.Adapter(tmp_path).mount_path == ""
    assert base.Adapter(tmp_path, mount_path="/").mount_path == ""
    assert base.Adapter(tmp_path, mount_path="py").mount_path == "/py"
    assert base.Adapter(tmp_path, mount_path="/a/b/").mount_path == "/a/b"


def test_every_reply_carries_cache_control_no_store(adapter):
    replies = [
        adapter.reply(200, "ok"),
        adapter.reply(404, "missing"),
        adapter.refuse("GET"),
        adapter.redirect("a=1"),
    ]
    for reply in replies:
        assert dict(reply.headers)["Cache-Control"] == "no-store"
        assert [name for name, _ in reply.headers].count("Cache-Control") == 1


def test_refusal_lists_the_allowed_methods(adapter):
    reply = adapter.refuse("GET", "HEAD")
    assert reply.status == 405
    assert dict(reply.headers)["Allow"] == "GET, HEAD"


def test_redirect_keeps_the_query_string(adapter):
    reply = adapter.redirect("a=1&b=2")
    assert reply.status == 301
    assert dict(reply.headers)["Location"] == "/py/?a=1&b=2"
    assert dict(adapter.redirect().headers)["Location"] == "/py/"


def test_owner_cookie_is_a_session_cookie_below_the_mount_path(adapter, tmp_path):
    cookie = SimpleCookie(adapter.owner_cookie("abc"))
    morsel = cookie["gramlot_owner"]
    assert morsel.value == "abc"
    assert morsel["path"] == "/py"
    assert morsel["httponly"] is True
    assert morsel["samesite"] == "Lax"
    assert morsel["max-age"] == "" and morsel["expires"] == ""
    root = SimpleCookie(base.Adapter(tmp_path).owner_cookie("abc"))
    assert root["gramlot_owner"]["path"] == "/"


def test_owner_is_read_from_the_cookie_header(adapter):
    assert adapter.owner_of("a=1; gramlot_owner=abc; b=2") == "abc"
    assert adapter.owner_of("a=1") is None
    assert adapter.owner_of("") is None
    assert adapter.owner_of("a b=1") is None


def test_theme_media_types_of_the_core_themes_and_the_types_python_lacks(adapter):
    types = {name: adapter.media_type(Path("set") / name)
             for name in ("font.woff2", "logo.svg", "data.bin", "style.css", "photo.webp", "notes.md")}
    assert types == {"font.woff2": "font/woff2", "logo.svg": "image/svg+xml",
                     "data.bin": "application/octet-stream", "style.css": "text/css; charset=utf-8",
                     "photo.webp": "image/webp", "notes.md": "text/markdown; charset=utf-8"}


def test_media_types_belong_to_the_instance(tmp_path):
    first, second = base.Adapter(tmp_path), base.Adapter(tmp_path)
    assert first.mime_types is not second.mime_types
    first.mime_types.add_type("application/x-first", ".first")
    assert second.mime_types.guess_type("a.first")[0] is None
    assert not any(name in vars(base) for name in ("MEDIA_TYPES", "THEME_MEDIA_TYPES", "THEMES"))


def test_the_shutdown_forgets_every_page(adapter):
    adapter.gramlot_server._pages["x"] = (float("inf"), object, "owner")
    adapter.shutdown()
    assert adapter.gramlot_server._pages == {}


def test_close_at_exit_runs_at_exit_and_does_not_keep_the_adapter_alive(tmp_path):
    adapter = base.Adapter(tmp_path)
    server = adapter.gramlot_server
    finalizer = adapter.close_at_exit()
    assert finalizer.atexit
    server._pages["x"] = (float("inf"), object, "owner")
    reference = weakref.ref(adapter)
    del adapter
    gc.collect()
    assert reference() is None
    assert not finalizer.alive
    assert server._pages == {}


@pytest.mark.asyncio
@pytest.mark.parametrize("source", ["cdn", "local"])
async def test_the_page_policy_and_document_follow_the_library_source(tmp_path, source):
    (tmp_path / "index.py").write_text("from gramlot import Page\nclass Page(Page):\n    def main(self, root): root.h1('x')\n")
    adapter = base.Adapter(tmp_path, content_security_policy="script-src 'nonce-{nonce}'; object-src 'none'",
                           library_source=source)
    reply = await adapter.page(base.Request(method="GET", path="/", body=base.stored(b"")))
    policy = dict(reply.headers)["Content-Security-Policy"]
    html = reply.body.decode()
    nonce = re.search(r'nonce="([^"]+)"', html).group(1)
    origin = " https://cdn.jsdelivr.net" if source == "cdn" else ""
    assert policy == f"script-src 'nonce-{nonce}'{origin}; object-src 'none'"
    assert f'<html data-gramlot-library-source="{source}">' in html


def test_an_unknown_library_source_is_refused(tmp_path):
    with pytest.raises(ValueError, match="library source must be 'cdn' or 'local'"):
        base.Adapter(tmp_path, library_source="unpkg")


def conditional(**headers):
    """A ``GET`` with the conditions ``headers``."""
    return base.Request(method="GET", path="/x", body=base.stored(b""), **headers)


@pytest.mark.asyncio
async def test_a_revalidated_file_carries_its_validators_and_answers_304(adapter, tmp_path):
    file = tmp_path / "theme.css"
    file.write_text("h1 {}\n")
    first = await adapter.send_revalidated(conditional(), file, "text/css")
    headers = dict(first.headers)
    assert first.status == 200 and first.body == b"h1 {}\n"
    assert headers["Cache-Control"] == "no-cache"
    assert headers["ETag"].startswith('"') and len(headers["ETag"]) == 66
    for condition in ({"if_none_match": headers["ETag"]}, {"if_none_match": '"other", W/' + headers["ETag"]},
                      {"if_none_match": "*"}, {"if_modified_since": headers["Last-Modified"]}):
        reply = await adapter.send_revalidated(conditional(**condition), file, "text/css")
        assert reply.status == 304 and reply.body == b"", condition
        assert dict(reply.headers)["ETag"] == headers["ETag"]
        assert dict(reply.headers)["Cache-Control"] == "no-cache"
    for condition in ({"if_none_match": '"other"'}, {"if_modified_since": "Mon, 01 Jan 2001 00:00:00 GMT"},
                      {"if_modified_since": "not a date"},
                      {"if_none_match": '"other"', "if_modified_since": headers["Last-Modified"]}):
        reply = await adapter.send_revalidated(conditional(**condition), file, "text/css")
        assert reply.status == 200 and reply.body == b"h1 {}\n", condition


@pytest.mark.asyncio
async def test_the_etag_is_computed_once_per_file_content(adapter, tmp_path, monkeypatch):
    file = tmp_path / "gramlot.js"
    file.write_text("one")
    computed = []
    sha256 = base.hashlib.sha256
    monkeypatch.setattr(base.hashlib, "sha256", lambda data: computed.append(data) or sha256(data))
    etag = dict((await adapter.send_revalidated(conditional(), file, "text/javascript")).headers)["ETag"]
    assert dict((await adapter.send_revalidated(conditional(), file, "text/javascript")).headers)["ETag"] == etag
    assert computed == [b"one"]
    file.write_text("two!")
    changed = await adapter.send_revalidated(conditional(if_none_match=etag), file, "text/javascript")
    assert changed.status == 200 and changed.body == b"two!"
    assert dict(changed.headers)["ETag"] != etag
    assert computed == [b"one", b"two!"]
