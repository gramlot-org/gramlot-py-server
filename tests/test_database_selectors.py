import importlib.util
import json

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from gramlot import Page, endpoint
from gramlot.db import DatabaseSelectors
from gramlot.page.base import endpoint_methods
from gramlot_py_server.db.sqlalchemy import SQLAlchemySelect


@pytest.fixture
def provider(tmp_path):
    engine = create_engine("sqlite:///" + str(tmp_path / "test.sqlite"))
    metadata = MetaData()
    table = Table("people", metadata, Column("id", Integer, primary_key=True),
                  Column("name", String), Column("country", String), Column("secret", String))
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(table.insert(), [
            {"id":0,"name":"Ada","country":"GB","secret":"private"},
            {"id":1,"name":"ada","country":"IT","secret":"private"},
            {"id":2,"name":"100%_literal","country":"IT","secret":"private"}])
    provider = SQLAlchemySelect(engine).register("people", table, identifier="id", caption="name",
                                                columns=("country",), filters=("country",))
    yield provider, table
    engine.dispose()


def test_search_identity_projection_and_literal_search(provider):
    db, _ = provider
    result = db.select(dbtable="people", _id=0, hiddenColumns="country")
    assert result == {"identifier":"id", "caption":"name", "rows":[{"id":0,"name":"Ada","country":"GB"}]}
    assert len(db.select(dbtable="people", _querystring="ADA")["rows"]) == 2
    assert len(db.select(dbtable="people", _querystring="Ada", ignoreCase=False)["rows"]) == 1
    assert len(db.select(dbtable="people", _querystring="%_")["rows"]) == 1
    assert db.select(dbtable="people", _querystring="' OR 1=1 --")["rows"] == []
    assert db.select(dbtable="people", _querystring="", order_by="-id", limit=1)["rows"][0]["id"] == 2
    assert db.select(dbtable="people", _id=99)["rows"] == []


def test_filters_and_dedicated_predicates_also_apply_to_identity(provider):
    db, table = provider
    assert db.select(dbtable="people", _id=0, country="IT")["rows"] == []
    assert db.select(dbtable="people", _id=0, where=(table.c.id > 0,))["rows"] == []
    assert len(db.select(dbtable="people", _querystring="", country="IT")["rows"]) == 2


@pytest.mark.parametrize("params", [
    {"dbtable":"secret", "_querystring":""}, {"_id":"0"}, {"_id":True},
    {"_id":9007199254740992}, {"_querystring":"", "columns":"secret"},
    {"_querystring":"", "order_by":"name; DROP TABLE people"},
    {"_querystring":"", "limit":0}, {"_querystring":"", "limit":True},
    {"_querystring":"", "unknown":"x"}, {"_id":0,"_querystring":""}, {},
])
def test_invalid_requests_fail_explicitly(provider, params):
    db, _ = provider
    with pytest.raises((ValueError, TypeError)):
        db.select(**{"dbtable":"people", **params})


def test_shared_endpoint_and_dedicated_method(provider):
    db, table = provider
    class Example(DatabaseSelectors, Page):
        database = db
        @endpoint
        def eligible(self, **parameters):
            return self.database.select(dbtable="people", where=(table.c.id > 0,), **parameters)
    assert set(endpoint_methods(Example)) == {"dbSelect", "eligible"}
    page = Example()
    assert page.dbSelect(dbtable="people", _id=0)["rows"][0]["id"] == 0
    assert page.eligible(_id=0)["rows"] == []


def test_registered_descending_order_and_invalid_order_configuration(provider):
    db, table = provider
    db.register("descending", table, identifier="id", caption="name", order_by=("-id",))
    assert [row["id"] for row in db.select(dbtable="descending", _querystring="")["rows"]] == [2, 1, 0]
    with pytest.raises(ValueError, match="ordering fields must be exposed"):
        db.register("hidden_order", table, identifier="id", caption="name", order_by=("secret",))
    with pytest.raises(ValueError, match="Search is required"):
        db.register("no_search", table, identifier="id", caption="name", search=())
    with pytest.raises(ValueError, match="Ordering field"):
        db.select(dbtable="people", _querystring="", order_by="")

@pytest.mark.parametrize('parameters', [
    {'condition': '$country=:country', 'country': 'IT'},
    {'weakCondition': True}, {'weakCondition': '$country=:country', 'country': 'IT'},
])
def test_legacy_conditions_are_explicitly_asqueel_only(provider, parameters):
    from gramlot_py_server.db.django import DjangoSelect
    db, _ = provider
    for selection in (db, DjangoSelect()):
        with pytest.raises(ValueError, match='Asqueel-only'):
            selection.select(dbtable='people', _querystring='', **parameters)
