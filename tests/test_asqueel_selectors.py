"""Real SQLite queries for the explicitly configured Asqueel selector provider."""
from contextlib import contextmanager
import re
import json
from importlib.resources import files
from pathlib import Path

import httpx
import pytest
from kajenn import AsgiServer
from kajenn.config.templates import DefaultConfiguration

from gramlot_py_server.db.asqueel import AsqueelSelect
from selector_fixture import create_database, selection_provider
from gramlot_py_server.kajenn import Application
from rpc_checks import RPC_HEADERS, envelope


@pytest.fixture
def provider(tmp_path):
    shared = create_database(tmp_path / "selectors.sqlite")
    yield selection_provider(shared), shared
    shared.close()


def test_prefix_fallback_zero_and_projection(provider):
    db, _ = provider
    assert db.select(dbtable="customers", _querystring="b", hiddenColumns="city")["rows"] == [
        {"id": 3, "name": "Elena Bianchi", "city": "Trento"}]
    assert [r["id"] for r in db.select(dbtable="customers", _querystring="a")["rows"]] == [0]
    assert db.select(dbtable="customers", _id=0)["rows"][0]["name"] == "Ada Rossi"
    assert db.select(dbtable="customers", _querystring="rossi", limit=1)["rows"][0]["id"] == 0
    assert db.select(dbtable="customers", _querystring="", order_by="-id", limit=1)["rows"][0]["id"] == 6


def test_hard_condition_and_filter_apply_to_every_stage_and_lookup(provider):
    db, _ = provider
    assert db.select(dbtable="customers", _id=9)["rows"] == []
    assert db.select(dbtable="customers", _querystring="Bruno")["rows"] == []
    assert db.select(dbtable="customers", _id=0, city="Roma")["rows"] == []
    assert db.select(dbtable="customers", _querystring="bianchi", city="Roma")["rows"] == []
    assert db.select(dbtable="customers", _querystring="mario", city="Firenze")["rows"] == [
        {"id": 5, "name": "Mario Rossi"}]


def test_literal_case_sensitive_null_and_database_changes(provider):
    db, shared = provider
    with shared.session() as session:
        session.table("demo.customer").insert({"id": 11, "name": "100%_literal\\path", "city": None, "active": 1})
        session.commit()
    assert db.select(dbtable="customers", _querystring="%_literal\\path")["rows"][0]["id"] == 11
    assert db.select(dbtable="customers", _querystring="' OR 1=1 --")["rows"] == []
    assert db.select(dbtable="customers", _querystring="ada", ignoreCase=False)["rows"] == []
    assert db.select(dbtable="customers", _querystring="ADA", ignoreCase=True)["rows"][0]["id"] == 0
    assert db.select(dbtable="customers", _querystring="", city=None)["rows"][0]["id"] == 11
    with shared.session() as session:
        session.table("demo.customer").sql_update({"id": 3, "name": "Elena Verdi"})
        session.commit()
    assert db.select(dbtable="customers", _querystring="bianchi")["rows"] == []
    assert db.select(dbtable="customers", _querystring="verdi")["rows"][0]["id"] == 3


def test_model_formula_caption_and_independent_search_fields(provider):
    _, shared = provider
    db = AsqueelSelect(shared).register("people", "demo.customer", identifier="id",
        caption="display", search=("name", "city"), columns=("name", "city"))
    assert db.select(dbtable="people", _querystring="trento")["rows"] == [
        {"id": 3, "display": "Elena Bianchi (Trento)"}]


@pytest.mark.parametrize("parameters", [
    {"dbtable": "unknown", "_querystring": ""}, {"_id": "0"}, {"_id": True},
    {"_id": 2**54}, {"_id": None}, {"_querystring": 42}, {}, {"_id": 0, "_querystring": ""},
    {"_querystring": "", "columns": "secret"}, {"_querystring": "", "hiddenColumns": "secret"},
    {"_querystring": "", "order_by": "name; DROP TABLE customer"},
    {"_querystring": "", "limit": 0}, {"_querystring": "", "limit": True},
    {"_querystring": "", "ignoreCase": "false"}, {"_querystring": "", "where": "1=1"},
    {"_querystring": "", "sqlparams": {"enabled": 0}}, {"_querystring": "", "active": 0},
])
def test_invalid_or_unexposed_requests_are_refused(provider, parameters):
    db, _ = provider
    with pytest.raises((TypeError, ValueError)):
        db.select(**{"dbtable": "customers", **parameters})


def test_session_context_exits_on_success_and_query_failure(provider, monkeypatch):
    db, shared = provider
    original = shared.session
    exited = []

    @contextmanager
    def session():
        try:
            with original() as opened:
                yield opened
        finally:
            exited.append(True)

    monkeypatch.setattr(shared, "session", session)
    db.select(dbtable="customers", _id=0)
    assert len(exited) == 1
    broken = AsqueelSelect(shared).register("broken", "demo.customer", identifier="id", caption="name",
                                          where="missing_column = 1")
    count = len(exited)
    with pytest.raises(Exception):
        broken.select(dbtable="broken", _querystring="Ada")
    assert len(exited) == count + 1


@pytest.mark.asyncio
@pytest.mark.parametrize("mount", ["", "py"])
async def test_kajenn_data_rpc_uses_real_asqueel_database(tmp_path, mount, provider, monkeypatch):
    import selector_fixture
    monkeypatch.setattr(selector_fixture, "database", provider[0], raising=False)
    (tmp_path / "index.py").write_text("""from gramlot import Page as BasePage
from gramlot.db import DatabaseSelectors
from gramlot.collections.inputs import mygramlot as inputs
from selector_fixture import database

class Page(DatabaseSelectors, BasePage):
    gramlots = [inputs]
    database = database
    def main(self, root):
        root.dbSelect(value='^.customer', dbtable='customers')
""")
    from gramlot.collections.inputs import mygramlot as inputs
    prefix = f"/{mount}" if mount else ""

    class Site(DefaultConfiguration):
        def applications_section(self, cfg):
            cfg.applications().application(code="pages", mount=mount, app_class=Application,
                                           pages=tmp_path, collections=[inputs]).request(body="raw")

    server = AsgiServer(config=Site)
    transport = httpx.ASGITransport(app=server, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test" + prefix) as client:
        document = await client.get("/")
        assert document.status_code == 200
        page_id = re.search(r'"pageId":"([^"]+)"', document.text).group(1)
        source = await client.post("/gramlot/rpc", headers=RPC_HEADERS, content=envelope(page_id))
        assert "gramlot-db-select" in source.json()["value"]

        async def select(**parameters):
            response = await client.post("/gramlot/rpc", headers=RPC_HEADERS,
                content=envelope(page_id, "dbSelect", {"dbtable": "customers", **parameters}, content_type="data"))
            assert response.status_code == 200
            return response.json()

        result = await select(_querystring="b", hiddenColumns="city")
        assert "error" not in result, result
        assert result["value"]["rows"] == [{"id": 3, "name": "Elena Bianchi", "city": "Trento"}]
        assert (await select(_id=0))["value"]["rows"][0]["id"] == 0
        assert (await select(_id=9))["value"]["rows"] == []
        assert "error" in await select(_querystring="", hiddenColumns="secret")
        auxiliary = await select(_id=0, auxColumns='active', hiddenColumns='active')
        assert auxiliary['value']['rows'][0]['active'] == 1
        assert auxiliary['value']['columns'] == ['name', 'active']
        invalid = await select(_querystring='', auxColumns='missing_column')
        assert 'error' in invalid and 'value' not in invalid
        async with httpx.AsyncClient(transport=transport, base_url="http://test" + prefix) as stranger:
            response = await stranger.post("/gramlot/rpc", headers=RPC_HEADERS,
                content=envelope(page_id, "dbSelect", {"dbtable": "customers", "_id": 0}, content_type="data"))
            assert "error" in response.json()
