"""Спільні фікстури тестів прототипу: тимчасовий кластер PostgreSQL, еталонна БД (schema + impl + seed),
окрема копія БД для кожного тестового модуля, клієнт Flask з входом і маркером CSRF."""
import itertools
import sys
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

HERE = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(HERE), str(HERE / "db")]
import pgtemp  # noqa: E402
import seed  # noqa: E402

_n = itertools.count(1)


@pytest.fixture(scope="session")
def cluster():
    with pgtemp.TempCluster(port=54390) as pg:
        pg.psql_file(pgtemp.SCHEMA)
        pg.psql_file(pgtemp.IMPL)
        with psycopg.connect(pg.dsn) as c:
            seed.seed(c)
        pg.psql("ALTER DATABASE shchit IS_TEMPLATE true", db="postgres")
        yield pg


@pytest.fixture(scope="module")
def dsn(cluster):
    name = f"t{next(_n)}"
    cluster.psql(f"CREATE DATABASE {name} TEMPLATE shchit", db="postgres")
    return cluster.dsn.replace("dbname=shchit", f"dbname={name}")


@pytest.fixture
def conn(dsn):
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row) as c:
        yield c


@pytest.fixture(scope="module")
def webapp(dsn):
    import app as appmod
    appmod.DSN = dsn.replace("user=postgres", "user=shch_app")
    appmod.app.config.update(TESTING=True)
    return appmod


@pytest.fixture
def client(webapp):
    return webapp.app.test_client()


def csrf(client):
    with client.session_transaction() as s:
        if "csrf" not in s:
            s["csrf"] = "test-csrf"
        return s["csrf"]


def post(client, url, data=None, **kw):
    return client.post(url, data={**(data or {}), "csrf": csrf(client)}, **kw)


def login(client, user, password=seed.DEMO_PASSWORD):
    client.get("/logout")
    client.get("/login")
    return post(client, "/login", {"login": user, "password": password})


def one(conn, sql, *args):
    r = conn.execute(sql, args or None).fetchone()
    return None if r is None else next(iter(r.values()))


def as_user(conn, login_):
    """Виконати наступні запити від імені користувача (для тригерів прав і аудиту)."""
    uid = one(conn, "SELECT user_id FROM personnel WHERE login = %s", login_)
    conn.execute("SELECT set_config('app.user_id', %s, false)", (str(uid),))
    return uid
