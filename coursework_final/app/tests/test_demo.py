"""Розширений демонстраційний набір (seed rich=True, serve.py): цілісність даних, сторінки списків, дії ролей."""
import re

import psycopg
import pytest

import pgtemp
import seed
from conftest import login, one, post


@pytest.fixture(scope="module")
def dsn():
    with pgtemp.TempCluster(port=54391) as pg:
        pg.psql_file(pgtemp.SCHEMA)
        pg.psql_file(pgtemp.IMPL)
        with psycopg.connect(pg.dsn) as c:
            seed.seed(c, rich=True)
        yield pg.dsn


def shown(resp):
    m = re.search(r"Показано (\d+)–(\d+) з (\d+)", resp.get_data(as_text=True))
    return tuple(map(int, m.groups())) if m else None


def test_rich_data_covers_every_state(conn):
    for table, col, skip in (("mission", "state", {"перепризначена"}), ("interceptor", "state", set()),
                             ("sensor", "status", set()), ("personnel", "status", set())):
        have = {r["s"] for r in conn.execute(f"SELECT DISTINCT {col}::text AS s FROM {table}")}
        enum = {r["s"] for r in conn.execute(f"SELECT unnest(enum_range(NULL::{table}_{col}))::text AS s")}
        assert enum - skip <= have, (table, enum - have)
    assert one(conn, "SELECT count(*) FROM mission") > 130
    assert one(conn, "SELECT broken FROM fn_audit_verify()") == 0


def test_lists_are_paged(client, conn):
    login(client, "och1")
    total = one(conn, "SELECT count(*) FROM mission")
    p1, p2 = client.get("/missions"), client.get("/missions?page=2")
    assert shown(p1) == (1, 12, total) and shown(p2) == (13, 24, total)
    nos = lambda r: set(re.findall(r"М-\d{4}-\d{2}", r.get_data(as_text=True)))     # noqa: E731
    assert nos(p1).isdisjoint(nos(p2))
    closed = one(conn, "SELECT count(*) FROM mission WHERE state = 'закрита'")
    assert shown(client.get("/missions?state=закрита&page=999"))[2] == closed      # фільтр + остання сторінка
    assert shown(client.get("/resources?state=на складі"))[2] == 16


def test_roles_have_pending_work(client, conn):
    login(client, "och1")
    mid = one(conn, "SELECT mission_id FROM mission WHERE state = 'запропонована' LIMIT 1")
    assert "Очікують санкції (2)" in client.get("/").get_data(as_text=True)
    post(client, f"/missions/{mid}", {"action": "state", "to_state": "санкціонована"})
    assert one(conn, "SELECT state::text FROM mission WHERE mission_id = %s", mid) == "санкціонована"
    login(client, "an1")
    tid = one(conn, "SELECT track_id FROM v_threat_queue WHERE state = 'підтверджений' LIMIT 1")
    post(client, f"/tracks/{tid}", {"action": "classify", "identity": "ворожа", "target_type": "ударний БпЛА"})
    assert one(conn, "SELECT identity::text FROM air_track WHERE track_id = %s", tid) == "ворожа"
