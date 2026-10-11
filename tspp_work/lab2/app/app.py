"""АРМ IoT-платформи «Щит-Лінк» — веб-застосунок (Flask) над БД PostgreSQL (ЛР2).

Бізнес-правила (переходи станів, правило двох осіб, журнал аудиту) виконуються в БД функціями й тригерами
(tspp_work/lab2/db/impl.sql); застосунок відповідає за автентифікацію, подання даних і передавання користувача в
БД через set_config('app.user_id', …, true).

    SHCH_DSN="host=… dbname=shchit user=postgres" python app.py
"""
import os
import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import psycopg
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from psycopg.rows import dict_row

app = Flask(__name__)
app.secret_key = os.environ.get("SHCH_SECRET", secrets.token_hex(16))
DSN = os.environ.get("SHCH_DSN", "dbname=shchit")
GATEWAY_TOKEN = os.environ.get("SHCH_GATEWAY_TOKEN", "demo-gateway-token")

STATE_CLASS = {"запропонована": "s-new", "санкціонована": "s-ok", "прийнята": "s-ok", "виконується": "s-run",
               "перепризначена": "s-warn", "відхилена": "s-off", "скасована": "s-off", "закрита": "s-done"}
TRANSITION_LABEL = {"санкціонована": "Санкціонувати", "відхилена": "Відхилити", "перепризначена": "Перепризначити",
                    "запропонована": "Запропонувати повторно", "прийнята": "Прийняти завдання",
                    "виконується": "Пуск", "скасована": "Скасувати", "закрита": "Закрити"}


# ------------------------------------------------------------------------------------------ доступ до БД
def db():
    if "db" not in g:
        g.db = psycopg.connect(DSN, row_factory=dict_row)
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    c = g.pop("db", None)
    if c is not None:
        c.close()


@contextmanager
def tx():
    """Транзакція від імені поточного користувача (для тригерів аудиту й перевірки прав)."""
    with db().transaction():
        cur = db().cursor()
        cur.execute("SELECT set_config('app.user_id', %s, true)", (session.get("uid", ""),))
        yield cur


def rows(sql, *args):
    with tx() as cur:
        return cur.execute(sql, args).fetchall()


def row(sql, *args):
    r = rows(sql, *args)
    return r[0] if r else None


def db_error(e):
    msg = e.diag.message_primary if getattr(e, "diag", None) and e.diag.message_primary else str(e)
    flash(msg, "error")


# ------------------------------------------------------------------------------------------ автентифікація
@app.before_request
def load_user():
    g.user, g.perms = None, set()
    if request.endpoint in ("login", "static") or request.path.startswith("/api/"):
        return None
    uid = session.get("uid")
    if uid:
        g.user = row("SELECT u.user_id, u.full_name, u.login, u.rank, r.code AS role_code, r.name AS role_name, "
                     "c.call_sign FROM personnel u JOIN role r USING (role_id) LEFT JOIN crew c USING (crew_id) "
                     "WHERE u.user_id = %s AND u.status = 'активний'", uid)
    if not g.user:
        return redirect(url_for("login"))
    g.perms = {r["code"] for r in rows("SELECT p.code FROM personnel u JOIN role_permission rp USING (role_id) "
                                       "JOIN permission p USING (permission_id) WHERE u.user_id = %s", uid)}
    return None


def need(perm):
    if perm not in g.perms:
        abort(403)


@app.context_processor
def helpers():
    return dict(can=lambda p: p in g.perms, state_class=STATE_CLASS,
                fmt_dt=lambda d: d.astimezone().strftime("%d.%m %H:%M:%S") if d else "—",
                fmt_eta=lambda s: f"{s // 60}:{s % 60:02d}" if s is not None else "—")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = row("SELECT user_id FROM personnel WHERE login = %s AND status = 'активний'", request.form["login"])
        if u:
            session["uid"] = str(u["user_id"])
            return redirect(url_for("index"))
        flash("Обліковий запис не знайдено або заблоковано", "error")
    users = rows("SELECT u.login, u.full_name, r.code, r.name AS role FROM personnel u JOIN role r USING (role_id) "
                 "WHERE u.status = 'активний' AND r.code IN ('R-01', 'R-02', 'R-03', 'R-04', 'R-08', 'R-09', "
                 "'R-11') ORDER BY r.code, u.login")
    return render_template("login.html", users=users)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------------------------------------ обстановка
@app.route("/")
def index():
    """Стартова сторінка — перший розділ, на який користувач має право."""
    for perm, ep in (("track.read", "situation"), ("mission.read", "missions"), ("resource.read", "resources"),
                     ("analytics.read", "analytics"), ("audit.read", "audit")):
        if perm in g.perms:
            return redirect(url_for(ep))
    abort(403)


@app.route("/situation")
def situation():
    need("track.read")
    queue = rows("SELECT * FROM v_threat_queue")
    kpi = row("SELECT (SELECT count(*) FROM v_threat_queue) AS threats, "
              "(SELECT count(*) FROM mission WHERE state IN ('санкціонована', 'прийнята', 'виконується')) AS active, "
              "(SELECT count(*) FROM crew WHERE status = 'готовий') AS crews, "
              "(SELECT count(*) FROM sensor WHERE status IN ('у мережі', 'деградований')) AS sensors_on, "
              "(SELECT count(*) FROM sensor) AS sensors")
    return render_template("situation.html", queue=queue, kpi=kpi)


@app.route("/tracks/<uuid:tid>", methods=["GET", "POST"])
def track(tid):
    need("track.read")
    if request.method == "POST":
        try:
            if request.form["action"] == "classify":
                need("track.classify")
                with tx() as cur:
                    cur.execute("SELECT fn_classify_track(%s, %s, %s)",
                                (tid, request.form["identity"], request.form["target_type"]))
                flash("Класифікацію збережено", "ok")
            elif request.form["action"] == "propose":
                need("mission.propose")
                with tx() as cur:
                    mid = cur.execute("SELECT fn_propose_mission(%s, %s) AS id",
                                      (tid, request.form["crew_id"])).fetchone()["id"]
                flash("Місію запропоновано — очікує санкції оперативного чергового", "ok")
                return redirect(url_for("mission", mid=mid))
        except psycopg.Error as e:
            db_error(e)
        return redirect(url_for("track", tid=tid))
    t = row("SELECT t.*, o.name AS object_name, u.full_name AS classified_name, p.lat, p.lon, p.speed "
            "FROM air_track t LEFT JOIN protected_object o ON o.object_id = t.predicted_object_id "
            "LEFT JOIN personnel u ON u.user_id = t.classified_by, fn_track_pos(t.track_id) p "
            "WHERE t.track_id = %s", tid)
    if not t:
        abort(404)
    dets = rows("SELECT d.detected_at, s.hw_serial, s.kind, d.lat, d.lon, d.altitude_m, d.speed_mps, d.confidence "
                "FROM detection d JOIN sensor s USING (sensor_id) WHERE d.track_id = %s "
                "ORDER BY d.detected_at DESC LIMIT 6", tid)
    cands = rows("SELECT * FROM fn_crew_candidates(%s) LIMIT 5", tid)
    active = row("SELECT mission_id, mission_no, state FROM mission WHERE track_id = %s "
                 "AND state NOT IN ('відхилена', 'скасована', 'закрита')", tid)
    return render_template("track.html", t=t, dets=dets, cands=cands, active=active,
                           identities=["ворожа", "невідома", "нейтральна", "дружня"])


# ------------------------------------------------------------------------------------------ місії
@app.route("/missions")
def missions():
    need("mission.read")
    st = request.args.get("state", "")
    ms = rows("SELECT m.mission_id, m.mission_no, m.state, m.proposed_at, m.closed_at, t.track_number, "
              "c.call_sign, r.assessment FROM mission m JOIN air_track t USING (track_id) JOIN crew c USING (crew_id) "
              "LEFT JOIN engagement_report r USING (mission_id) WHERE %s = '' OR m.state::text = %s "
              "ORDER BY m.proposed_at DESC LIMIT 12", st, st)
    states = [r["s"] for r in rows("SELECT unnest(enum_range(NULL::mission_state))::text AS s")]
    return render_template("missions.html", ms=ms, states=states, st=st)


@app.route("/missions/<uuid:mid>", methods=["GET", "POST"])
def mission(mid):
    need("mission.read")
    if request.method == "POST":
        try:
            with tx() as cur:
                if request.form["action"] == "report":
                    need("mission.report")
                    cur.execute("INSERT INTO engagement_report (mission_id, assessment, submitted_by) "
                                "VALUES (%s, %s, %s)", (mid, request.form["assessment"], session["uid"]))
                else:
                    to = request.form["to_state"]
                    cur.execute("UPDATE mission SET state = %s, interceptor_id = coalesce(%s, interceptor_id), "
                                "abort_reason = coalesce(nullif(%s, ''), abort_reason) WHERE mission_id = %s",
                                (to, request.form.get("interceptor_id") or None, request.form.get("abort_reason"),
                                 mid))
            flash("Стан місії оновлено", "ok")
        except psycopg.Error as e:
            db_error(e)
        return redirect(url_for("mission", mid=mid))
    m = row("SELECT m.*, t.track_number, t.identity, t.threat_score, c.call_sign, c.position_id, p.code AS pos_code, "
            "up.full_name AS proposed_name, ua.full_name AS approved_name, i.serial_no, r.assessment "
            "FROM mission m JOIN air_track t USING (track_id) JOIN crew c USING (crew_id) "
            "JOIN position p ON p.position_id = c.position_id "
            "JOIN personnel up ON up.user_id = m.proposed_by LEFT JOIN personnel ua ON ua.user_id = m.approved_by "
            "LEFT JOIN interceptor i ON i.interceptor_id = m.interceptor_id "
            "LEFT JOIN engagement_report r ON r.mission_id = m.mission_id WHERE m.mission_id = %s", mid)
    if not m:
        abort(404)
    trans = [dict(to=r["to_state"], label=TRANSITION_LABEL[r["to_state"]]) for r in
             rows("SELECT to_state::text FROM mission_transition WHERE from_state = %s ORDER BY to_state", m["state"])
             if r["to_state"] != "закрита" and _perm_for(m["state"], r["to_state"]) in g.perms]
    events = rows("SELECT e.event_at, e.event_type, e.payload, u.full_name FROM mission_event e "
                  "LEFT JOIN personnel u ON u.user_id = e.actor_id WHERE e.mission_id = %s ORDER BY e.event_at", mid)
    ints = rows("SELECT interceptor_id, serial_no, im.name AS model FROM interceptor JOIN interceptor_model im "
                "USING (model_id) WHERE position_id = %s AND state = 'готовий' ORDER BY serial_no", m["position_id"])
    tele = rows("SELECT ts, lat, lon, alt_m, ground_speed_mps, battery_pct, link_quality_pct FROM telemetry_frame "
                "WHERE mission_id = %s ORDER BY ts DESC LIMIT 4", mid)
    return render_template("mission.html", m=m, trans=trans, events=events, ints=ints, tele=tele)


def _perm_for(frm, to):
    r = row("SELECT perm FROM mission_transition WHERE from_state = %s AND to_state = %s", frm, to)
    return r["perm"] if r else None


# ------------------------------------------------------------------------------------------ ресурси (CRUD)
@app.route("/resources")
def resources():
    need("resource.read")
    ready = rows("SELECT * FROM v_readiness")
    pos = request.args.get("pos", "")
    ints = rows("SELECT i.interceptor_id, i.serial_no, im.name AS model, i.state, i.flight_count, "
                "i.firmware_version, p.code AS pos FROM interceptor i JOIN interceptor_model im USING (model_id) "
                "LEFT JOIN position p USING (position_id) WHERE %s = '' OR p.code = %s ORDER BY i.serial_no "
                "LIMIT 4", pos, pos)
    return render_template("resources.html", ready=ready, ints=ints, pos=pos)


@app.route("/interceptors/new", methods=["GET", "POST"])
@app.route("/interceptors/<uuid:iid>/edit", methods=["GET", "POST"])
def interceptor_form(iid=None):
    need("interceptor.manage")
    if request.method == "POST":
        f = request.form
        try:
            with tx() as cur:
                if iid:
                    cur.execute("UPDATE interceptor SET model_id = %s, position_id = %s, serial_no = %s, state = %s, "
                                "firmware_version = %s WHERE interceptor_id = %s",
                                (f["model_id"], f["position_id"] or None, f["serial_no"], f["state"],
                                 f["firmware_version"] or None, iid))
                else:
                    cur.execute("INSERT INTO interceptor (model_id, position_id, serial_no, state, firmware_version, "
                                "received_at) VALUES (%s, %s, %s, %s, %s, current_date)",
                                (f["model_id"], f["position_id"] or None, f["serial_no"], f["state"],
                                 f["firmware_version"] or None))
            flash("Перехоплювач збережено", "ok")
            return redirect(url_for("resources"))
        except psycopg.Error as e:
            db_error(e)
    it = row("SELECT * FROM interceptor WHERE interceptor_id = %s", iid) if iid else None
    return render_template("interceptor_form.html", it=it,
                           models=rows("SELECT model_id, name FROM interceptor_model ORDER BY name"),
                           positions=rows("SELECT position_id, code FROM position ORDER BY code"),
                           states=[r["s"] for r in rows("SELECT unnest(enum_range(NULL::interceptor_state))::text "
                                                        "AS s")])


@app.route("/interceptors/<uuid:iid>/delete", methods=["POST"])
def interceptor_delete(iid):
    need("interceptor.manage")
    try:
        with tx() as cur:
            cur.execute("DELETE FROM interceptor WHERE interceptor_id = %s", (iid,))
        flash("Перехоплювач видалено", "ok")
    except psycopg.errors.ForeignKeyViolation:
        flash("Неможливо видалити: перехоплювач використано в місіях (обмеження зовнішнього ключа)", "error")
    except psycopg.Error as e:
        db_error(e)
    return redirect(request.referrer or url_for("resources"))


# ------------------------------------------------------------------------------------------ аналітика, аудит
@app.route("/analytics")
def analytics():
    need("analytics.read")
    to = request.args.get("to") or (datetime.now(timezone.utc) + timedelta(days=1)).date().isoformat()
    frm = request.args.get("from") or (datetime.now(timezone.utc) - timedelta(days=30)).date().isoformat()
    st = row("SELECT * FROM fn_mission_stats(%s::date, %s::date)", frm, to)
    crews = rows("SELECT c.call_sign, count(*) AS n, count(*) FILTER (WHERE r.assessment = 'влучання') AS hits, "
                 "round(avg(extract(epoch FROM m.launched_at - m.approved_at))) AS launch_s FROM mission m "
                 "JOIN crew c USING (crew_id) LEFT JOIN engagement_report r USING (mission_id) "
                 "WHERE m.proposed_at >= %s::date AND m.proposed_at < %s::date GROUP BY c.call_sign "
                 "ORDER BY n DESC, hits DESC LIMIT 6", frm, to)
    return render_template("analytics.html", st=st, crews=crews, frm=frm, to=to)


@app.route("/audit")
def audit():
    need("audit.read")
    ver = row("SELECT * FROM fn_audit_verify()")
    log = rows("SELECT a.entry_id, a.logged_at, a.action, a.entity_id, a.actor_type, u.full_name, a.hash "
               "FROM audit_log a LEFT JOIN personnel u ON u.user_id = a.actor_id ORDER BY a.entry_id DESC LIMIT 9")
    return render_template("audit.html", ver=ver, log=log)


# ------------------------------------------------------------------------------------------ REST API
@app.post("/api/v1/detections")
def api_detection():
    if request.headers.get("X-Gateway-Token") != GATEWAY_TOKEN:
        return jsonify(error="unauthorized"), 401
    d = request.get_json(force=True)
    try:
        with db().transaction():
            r = db().execute("SELECT * FROM fn_ingest_detection(%s, %s, %s::numeric, %s::numeric, %s::numeric, "
                             "%s::numeric, %s::numeric, %s, %s::numeric)",
                             (d["sensor"], d["detected_at"], d.get("lat"), d.get("lon"), d.get("alt"), d.get("speed"),
                              d.get("bearing"), d.get("signature"), d["confidence"])).fetchone()
    except psycopg.Error as e:
        return jsonify(error=e.diag.message_primary), 422
    return jsonify(detection_id=r["detection_id"], track_id=str(r["track_id"]) if r["track_id"] else None,
                   track_number=r["track_number"]), 201


@app.get("/api/v1/threats")
def api_threats():
    if request.headers.get("X-Gateway-Token") != GATEWAY_TOKEN:
        return jsonify(error="unauthorized"), 401
    q = db().execute("SELECT track_number, state::text, identity::text, threat_score::float, eta_s, object_name "
                     "FROM v_threat_queue").fetchall()
    return jsonify(threats=q)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5080)))
