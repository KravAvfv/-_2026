"""Бізнес-правила, реалізовані в БД (функції, тригери, обмеження)."""
from datetime import timedelta

import psycopg
import pytest

from conftest import as_user, one


def err(conn, sql, *args):
    with pytest.raises(psycopg.Error) as e:
        with conn.transaction():
            conn.execute(sql, args or None)
    return e.value.diag.message_primary


def test_schema_objects(conn):
    tables = one(conn, "SELECT count(*) FROM pg_tables WHERE schemaname = 'public'")
    assert tables == 20                     # 18 сутностей + mission_transition + sensor_transition
    assert one(conn, "SELECT count(*) FROM pg_views WHERE schemaname = 'public'") == 2


def test_seed_volumes(conn):
    assert one(conn, "SELECT count(*) FROM role") == 13
    assert one(conn, "SELECT count(*) FROM mission") >= 28
    assert one(conn, "SELECT count(*) FROM detection") > 500
    assert one(conn, "SELECT broken FROM fn_audit_verify()") == 0


def test_two_person_rule(conn):
    mid = one(conn, "SELECT mission_id FROM mission WHERE state = 'санкціонована' LIMIT 1")
    with pytest.raises(psycopg.errors.CheckViolation):
        with conn.transaction():
            conn.execute("UPDATE mission SET approved_by = proposed_by WHERE mission_id = %s", (mid,))


def test_invalid_transition(conn):
    mid = one(conn, "SELECT mission_id FROM mission WHERE state = 'санкціонована' LIMIT 1")
    msg = err(conn, "UPDATE mission SET state = 'закрита' WHERE mission_id = %s", mid)
    assert "Недопустимий перехід" in msg


def test_transition_needs_permission(conn):
    mid = one(conn, "SELECT mission_id FROM mission WHERE state = 'санкціонована' LIMIT 1")
    as_user(conn, "och1")                                   # ОЧ не має права mission.accept
    assert "Немає права mission.accept" in err(conn, "UPDATE mission SET state = 'прийнята' WHERE mission_id = %s", mid)


def test_crew_scope(conn):
    m = conn.execute("SELECT mission_id, crew_id FROM mission WHERE state = 'санкціонована' LIMIT 1").fetchone()
    other = one(conn, "SELECT u.login FROM personnel u JOIN role r USING (role_id) WHERE r.code = 'R-04' "
                "AND u.crew_id <> %s LIMIT 1", m["crew_id"])
    as_user(conn, other)
    assert "іншому розрахунку" in err(conn, "UPDATE mission SET state = 'прийнята' WHERE mission_id = %s",
                                      m["mission_id"])
    own = one(conn, "SELECT u.login FROM personnel u JOIN role r USING (role_id) WHERE r.code = 'R-04' "
              "AND u.crew_id = %s", m["crew_id"])
    as_user(conn, own)
    conn.execute("UPDATE mission SET state = 'прийнята' WHERE mission_id = %s", (m["mission_id"],))
    assert one(conn, "SELECT status FROM crew WHERE crew_id = %s", m["crew_id"]) == "на завданні"


def test_report_guard(conn):
    m = conn.execute("SELECT mission_id, crew_id FROM mission WHERE state = 'виконується' LIMIT 1").fetchone()
    uid = as_user(conn, "och1")                             # ОЧ не має права mission.report
    assert "командир розрахунку" in err(conn, "INSERT INTO engagement_report (mission_id, assessment, submitted_by) "
                                        "VALUES (%s, 'влучання', %s)", m["mission_id"], uid)


def test_launch_requires_ready_interceptor(conn):
    m = conn.execute("SELECT mission_id, crew_id, state FROM mission WHERE state IN ('санкціонована', 'прийнята') "
                     "LIMIT 1").fetchone()
    cmd = one(conn, "SELECT u.login FROM personnel u JOIN role r USING (role_id) WHERE r.code = 'R-04' "
              "AND u.crew_id = %s", m["crew_id"])
    as_user(conn, cmd)
    if m["state"] == "санкціонована":
        conn.execute("UPDATE mission SET state = 'прийнята' WHERE mission_id = %s", (m["mission_id"],))
    assert "перехоплювач" in err(conn, "UPDATE mission SET state = 'виконується' WHERE mission_id = %s",
                                 m["mission_id"])


def test_sensor_state_machine(conn):
    sid = one(conn, "SELECT sensor_id FROM sensor WHERE status = 'поза мережею' LIMIT 1")
    as_user(conn, "r07_1")
    assert "Недопустимий перехід стану сенсора" in err(
        conn, "UPDATE sensor SET status = 'зареєстрований' WHERE sensor_id = %s", sid)
    conn.execute("UPDATE sensor SET status = 'у мережі' WHERE sensor_id = %s", (sid,))
    assert one(conn, "SELECT status FROM sensor WHERE sensor_id = %s", sid) == "у мережі"
    as_user(conn, "r08_1")                                  # логіст не має права sensor.manage
    assert "sensor.manage" in err(conn, "UPDATE sensor SET status = 'деградований' WHERE sensor_id = %s", sid)


def test_role_permission_guard(conn):
    r10 = one(conn, "SELECT role_id FROM role WHERE code = 'R-10'")
    approve = one(conn, "SELECT permission_id FROM permission WHERE code = 'mission.approve'")
    manage = one(conn, "SELECT permission_id FROM permission WHERE code = 'role.manage'")
    assert "не має бойових прав" in err(conn, "INSERT INTO role_permission (role_id, permission_id) VALUES (%s, %s)",
                                        r10, approve)
    assert "не може втратити" in err(conn, "DELETE FROM role_permission WHERE role_id = %s AND permission_id = %s",
                                     r10, manage)


def test_audit_immutable_and_chain(conn):
    assert "незмінний" in err(conn, "UPDATE audit_log SET action = 'x' WHERE entry_id = 3")
    assert "незмінний" in err(conn, "DELETE FROM audit_log WHERE entry_id = 3")
    assert one(conn, "SELECT count(*) FROM audit_log WHERE details::text LIKE '%password_hash%'") == 0
    with conn.transaction():
        conn.execute("ALTER TABLE audit_log DISABLE TRIGGER audit_immutable")
        conn.execute("UPDATE audit_log SET details = details || '{\"x\": 1}' WHERE entry_id = 7")
        conn.execute("ALTER TABLE audit_log ENABLE TRIGGER audit_immutable")
    v = conn.execute("SELECT * FROM fn_audit_verify()").fetchone()
    assert v["broken"] >= 1 and v["first_broken"] == 7


def test_ingest_creates_and_confirms_track(conn):
    s1, s2 = [r["hw_serial"] for r in conn.execute("SELECT hw_serial FROM sensor WHERE status = 'у мережі' "
                                                    "AND kind = 'акустичний' ORDER BY hw_serial LIMIT 2")]
    t0 = one(conn, "SELECT now()")
    ids = set()
    for k, s in enumerate([s1, s2, s1]):
        r = conn.execute("SELECT * FROM fn_ingest_detection(%s, %s, 51.9, 31.9, 200, 50, NULL, 'ударний поршневий', "
                         "0.9)", (s, t0 - timedelta(seconds=10 - k))).fetchone()
        ids.add(r["track_id"])
    assert len(ids) == 1
    assert one(conn, "SELECT state FROM air_track WHERE track_id = %s", ids.pop()) == "підтверджений"


def test_ingest_rejects_offline_sensor(conn):
    s = one(conn, "SELECT hw_serial FROM sensor WHERE status = 'у карантині' LIMIT 1")
    assert "виявлення не приймаються" in err(conn, "SELECT * FROM fn_ingest_detection(%s, now(), 51.9, 31.9, 200, 50, "
                                              "NULL, 'x', 0.9)", s)


def test_search_and_candidates(conn):
    no = one(conn, "SELECT mission_no FROM mission LIMIT 1")
    assert any(r["label"] == no for r in conn.execute("SELECT * FROM fn_search(%s)", (no,)))
    tid = one(conn, "SELECT track_id FROM v_threat_queue LIMIT 1")
    for c in conn.execute("SELECT c.status FROM fn_crew_candidates(%s) f JOIN crew c USING (crew_id)", (tid,)):
        assert c["status"] == "готовий"


def test_threat_queue_ordered(conn):
    sc = [float(r["threat_score"]) for r in conn.execute("SELECT threat_score FROM v_threat_queue")]
    assert sc and sc == sorted(sc, reverse=True)


def test_reassign_by_duty_officer_needs_new_approval(conn):
    tid = one(conn, "SELECT track_id FROM v_threat_queue WHERE active_mission IS NULL LIMIT 1")
    crews = [r["crew_id"] for r in conn.execute("SELECT crew_id FROM crew WHERE status = 'готовий' LIMIT 2")]
    as_user(conn, "obu2")
    mid = one(conn, "SELECT fn_propose_mission(%s, %s)", tid, crews[0])
    as_user(conn, "och1")
    conn.execute("UPDATE mission SET state = 'санкціонована' WHERE mission_id = %s", (mid,))
    m, other = {"mission_id": mid}, crews[1]
    och = as_user(conn, "och2")                                 # ОЧ має право mission.reassign
    conn.execute("UPDATE mission SET state = 'перепризначена' WHERE mission_id = %s", (m["mission_id"],))
    conn.execute("UPDATE mission SET state = 'запропонована', crew_id = %s WHERE mission_id = %s",
                 (other, m["mission_id"]))
    r = conn.execute("SELECT proposed_by, approved_by FROM mission WHERE mission_id = %s", (m["mission_id"],)).fetchone()
    assert r["proposed_by"] == och and r["approved_by"] is None
    with pytest.raises(psycopg.errors.CheckViolation):          # той, хто перепризначив, не санкціонує сам
        with conn.transaction():
            conn.execute("UPDATE mission SET state = 'санкціонована' WHERE mission_id = %s", (m["mission_id"],))
    as_user(conn, "och3")
    conn.execute("UPDATE mission SET state = 'санкціонована' WHERE mission_id = %s", (m["mission_id"],))
    assert one(conn, "SELECT state FROM mission WHERE mission_id = %s", m["mission_id"]) == "санкціонована"


def test_app_role_cannot_change_state_without_user(dsn):
    """Роль веб-застосунку shch_app не є суперкористувачем: без app.user_id змінити стан місії не можна."""
    with psycopg.connect(dsn.replace("user=postgres", "user=shch_app"), autocommit=True) as c:
        assert not c.execute("SELECT rolsuper FROM pg_roles WHERE rolname = current_user").fetchone()[0]
        mid, to = c.execute("SELECT m.mission_id, t.to_state FROM mission m JOIN mission_transition t "
                            "ON t.from_state = m.state LIMIT 1").fetchone()       # допустимий перехід
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("UPDATE mission SET state = %s WHERE mission_id = %s", (to, mid))
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            c.execute("UPDATE audit_log SET action = action")
