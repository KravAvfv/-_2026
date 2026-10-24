"""АРМ IoT-платформи «Щит-Лінк» — прототип інформаційної системи курсової роботи (Flask + PostgreSQL).

Основа — веб-застосунок tspp_work/lab2/app/app.py. Для курсової роботи додано: вхід за логіном і паролем з
блокуванням після 5 невдалих спроб, тайм-аут сеансу 15 хв, захист форм від CSRF, головну сторінку з віджетами
для кожної ролі, мнемосхему обстановки, глобальний пошук і фільтри, модулі «Сенсори», «Об’єкти прикриття»,
«Ручне донесення», «Користувачі», «Ролі та права».

Бізнес-правила (переходи станів, правило двох осіб, межі розрахунку, журнал аудиту) виконуються в БД функціями й
тригерами (db/impl.sql); застосунок відповідає за автентифікацію, подання даних і передавання користувача в БД
через set_config('app.user_id', …, true).

    SHCH_DSN="host=… dbname=shchit user=shch_app" python app.py   (роль без прав суперкористувача)
"""
import os
import secrets
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import psycopg
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from psycopg.rows import dict_row
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SHCH_SECRET", secrets.token_hex(16))
DSN = os.environ.get("SHCH_DSN", "dbname=shchit")
GATEWAY_TOKEN = os.environ.get("SHCH_GATEWAY_TOKEN", "demo-gateway-token")
IDLE_TIMEOUT_S = 15 * 60                         # DOMAIN_KNOWLEDGE_BASE §6.6: тайм-аут бездіяльності АРМ
MAX_FAILED_LOGINS = 5
PAGE = 12                                        # рядків у списках
MAP_H = 340                                      # висота мнемосхеми, px

STATE_CLASS = {"запропонована": "s-new", "санкціонована": "s-ok", "прийнята": "s-ok", "виконується": "s-run",
               "перепризначена": "s-warn", "відхилена": "s-off", "скасована": "s-off", "закрита": "s-done"}
TRANSITION_LABEL = {"санкціонована": "Санкціонувати", "відхилена": "Відхилити", "перепризначена": "Перепризначити",
                    "запропонована": "Запропонувати повторно", "прийнята": "Прийняти завдання",
                    "виконується": "Пуск", "скасована": "Скасувати", "закрита": "Закрити"}
# Модулі головного меню: (право, кінцева точка, назва, кінцеві точки, що підсвічують пункт)
MODULES = [("track.read", "situation", "Обстановка", ("situation", "track", "detection_new")),
           ("mission.read", "missions", "Місії", ("missions", "mission")),
           ("resource.read", "resources", "Ресурси", ("resources", "interceptor_form")),
           ("sensor.manage", "sensors", "Сенсори", ("sensors", "sensor_form")),
           ("sector.manage", "objects", "Об’єкти", ("objects", "object_form")),
           ("analytics.read", "analytics", "Аналітика", ("analytics",)),
           ("user.manage", "users", "Користувачі", ("users", "user_form")),
           ("user.block", "users", "Користувачі", ("users",)),
           ("role.manage", "roles", "Ролі та права", ("roles",)),
           ("audit.read", "audit", "Аудит", ("audit",))]
COMBAT_PERMS = ("mission.propose", "mission.reassign", "mission.approve", "mission.accept", "mission.launch", "mission.abort",
                "mission.report")


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


def enum_values(name):
    return [r["s"] for r in rows(f"SELECT unnest(enum_range(NULL::{name}))::text AS s")]


# ------------------------------------------------------------------------------------------ автентифікація
@app.before_request
def load_user():
    g.user, g.perms = None, set()
    if request.endpoint == "static" or request.path.startswith("/api/"):
        return None
    if request.method == "POST" and request.form.get("csrf") != session.get("csrf"):
        abort(400, "Недійсний маркер форми (CSRF)")
    if request.endpoint == "login":
        return None
    uid = session.get("uid")
    if uid and time.time() - session.get("seen", 0) > IDLE_TIMEOUT_S:
        session.clear()
        flash("Сеанс завершено через 15 хв бездіяльності — увійдіть знову", "error")
        return redirect(url_for("login"))
    if uid:
        g.user = row("SELECT u.user_id, u.full_name, u.login, u.rank, u.crew_id, r.code AS role_code, "
                     "r.name AS role_name, c.call_sign FROM personnel u JOIN role r USING (role_id) "
                     "LEFT JOIN crew c USING (crew_id) WHERE u.user_id = %s AND u.status = 'активний'", uid)
    if not g.user:
        session.pop("uid", None)
        return redirect(url_for("login"))
    session["seen"] = time.time()
    g.perms = {r["code"] for r in rows("SELECT p.code FROM personnel u JOIN role_permission rp USING (role_id) "
                                       "JOIN permission p USING (permission_id) WHERE u.user_id = %s", uid)}
    return None


def need(*perms):
    """Доступ, якщо користувач має хоча б одне з прав."""
    if not g.perms.intersection(perms):
        abort(403)


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(16)
    return session["csrf"]


def plural(n, one, few, many):
    """Узгодження з числівником: 1 місія, 2 місії, 5 місій."""
    n = abs(int(n))
    return one if n % 10 == 1 and n % 100 != 11 else few if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else many


def pager(total):
    """Сторінка списку (?page=N): номер, межі показаних рядків і OFFSET для запиту."""
    pages = max(1, -(-total // PAGE))
    try:
        page = min(pages, max(1, int(request.args.get("page", 1))))
    except ValueError:
        page = 1
    return dict(total=total, page=page, pages=pages, offset=(page - 1) * PAGE, first=min(total, (page - 1) * PAGE + 1),
                last=min(total, page * PAGE))


def page_url(page):
    return url_for(request.endpoint, **request.view_args, **{**request.args.to_dict(), "page": page})


@app.context_processor
def helpers():
    menu, seen = [], set()
    for perm, ep, title, eps in MODULES:
        if perm in g.perms and ep not in seen:
            seen.add(ep)
            menu.append((ep, title, eps))
    return dict(can=lambda p: p in g.perms, state_class=STATE_CLASS, menu=menu, csrf_token=csrf_token, pl=plural, page_url=page_url,
                fmt_dt=lambda d: d.astimezone().strftime("%d.%m %H:%M:%S") if d else "—",
                fmt_date=lambda d: d.strftime("%d.%m.%Y") if d else "—",
                fmt_eta=lambda s: f"{s // 60}:{s % 60:02d}" if s is not None else "—")


@app.errorhandler(403)
def forbidden(_e):
    return render_template("error.html", code=403, text="Недостатньо прав для цього розділу або дії."), 403


@app.errorhandler(404)
def not_found(_e):
    return render_template("error.html", code=404, text="Сторінку або запис не знайдено."), 404


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_ = request.form.get("login", "").strip()
        u = row("SELECT user_id, status, password_hash, failed_logins FROM personnel WHERE login = %s", login_)
        if u and u["status"] == "активний" and u["password_hash"] and \
                check_password_hash(u["password_hash"], request.form.get("password", "")):
            if u["failed_logins"]:
                with tx() as cur:
                    cur.execute("UPDATE personnel SET failed_logins = 0 WHERE user_id = %s", (u["user_id"],))
            session.clear()
            session.update(uid=str(u["user_id"]), seen=time.time(), csrf=secrets.token_urlsafe(16))
            return redirect(url_for("index"))
        if u and u["status"] == "активний":
            n = u["failed_logins"] + 1
            with tx() as cur:
                cur.execute("UPDATE personnel SET failed_logins = %s, status = CASE WHEN %s >= %s "
                            "THEN 'призупинений'::personnel_status ELSE status END WHERE user_id = %s",
                            (n, n, MAX_FAILED_LOGINS, u["user_id"]))
            if n >= MAX_FAILED_LOGINS:
                flash(f"Обліковий запис заблоковано після {MAX_FAILED_LOGINS} невдалих спроб — зверніться до "
                      "офіцера кібербезпеки", "error")
                return render_template("login.html", login=login_), 401
        flash("Неправильний логін або пароль, або обліковий запис заблоковано", "error")
        return render_template("login.html", login=login_), 401
    return render_template("login.html", login="")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------------------------------------ головна сторінка
@app.route("/")
def index():
    """Головна сторінка: модулі, доступні ролі, і віджети з даними, що стосуються саме цієї ролі."""
    w = {}
    if "track.read" in g.perms:
        w["threats"] = rows("SELECT track_id, track_number, identity, threat_score, eta_s, object_name "
                            "FROM v_threat_queue LIMIT 3")
    if "mission.approve" in g.perms:
        w["to_approve"] = rows("SELECT m.mission_id, m.mission_no, t.track_number, c.call_sign, m.proposed_at "
                               "FROM mission m JOIN air_track t USING (track_id) JOIN crew c USING (crew_id) "
                               "WHERE m.state = 'запропонована' ORDER BY m.proposed_at")
    if g.user["crew_id"]:
        w["my_missions"] = rows("SELECT m.mission_id, m.mission_no, m.state, t.track_number FROM mission m "
                                "JOIN air_track t USING (track_id) WHERE m.crew_id = %s AND m.state IN "
                                "('санкціонована', 'прийнята', 'виконується') ORDER BY m.proposed_at",
                                g.user["crew_id"])
        w["crew"] = row("SELECT c.call_sign, c.status, p.code FROM crew c JOIN position p USING (position_id) "
                        "WHERE c.crew_id = %s", g.user["crew_id"])
    if "resource.read" in g.perms:
        w["ready"] = row("SELECT sum(crews_ready) AS crews, sum(crews_total) AS crews_total, "
                         "sum(interceptors_ready) AS ints, sum(interceptors_total) AS ints_total FROM v_readiness")
    if "sensor.manage" in g.perms:
        w["sensors"] = rows("SELECT status::text, count(*) AS n FROM sensor GROUP BY status ORDER BY status")
    if g.perms.intersection(("user.manage", "user.block")):
        w["users"] = rows("SELECT status::text, count(*) AS n FROM personnel GROUP BY status ORDER BY status")
    if "audit.read" in g.perms:
        w["audit"] = row("SELECT * FROM fn_audit_verify()")
    if "analytics.read" in g.perms:
        w["stats"] = row("SELECT * FROM fn_mission_stats(now() - interval '30 days', now() + interval '1 day')")
    return render_template("index.html", w=w)


# ------------------------------------------------------------------------------------------ пошук
@app.route("/search")
def search():
    """Глобальний пошук (fn_search) — результати фільтруються за правами на відповідні розділи."""
    q = request.args.get("q", "").strip()
    allowed = {"трек": "track.read", "місія": "mission.read", "перехоплювач": "resource.read",
               "сенсор": "sensor.manage", "розрахунок": "resource.read"}
    found = [r for r in rows("SELECT * FROM fn_search(%s)", q) if allowed[r["kind"]] in g.perms] if len(q) >= 2 else []
    return render_template("search.html", q=q, found=found)


# ------------------------------------------------------------------------------------------ обстановка
def map_points():
    """Точки мнемосхеми: об’єкти прикриття, позиції, активні треки (лінійне масштабування координат району)."""
    pts = rows("SELECT 'об’єкт' AS kind, name AS label, category::text AS info, lat, lon FROM protected_object "
               "UNION ALL SELECT 'позиція', code, status::text, lat, lon FROM position "
               "UNION ALL SELECT 'трек', q.track_number, q.identity::text, p.lat, p.lon FROM v_threat_queue q, "
               "fn_track_pos(q.track_id) p WHERE p.lat IS NOT NULL")
    if not pts:
        return []
    for p in pts:
        p["lat"], p["lon"] = float(p["lat"]), float(p["lon"])
    lat0, lat1 = min(p["lat"] for p in pts) - 0.05, max(p["lat"] for p in pts) + 0.05
    lon0, lon1 = min(p["lon"] for p in pts) - 0.08, max(p["lon"] for p in pts) + 0.08
    boxes = []
    for p in pts:
        p["x"] = round((p["lon"] - lon0) / (lon1 - lon0) * 660 + 20, 1)
        p["y"] = round((lat1 - p["lat"]) / (lat1 - lat0) * (MAP_H - 30) + 15, 1)
        boxes.append((p["x"] - 8, p["y"] - 8, p["x"] + 8, p["y"] + 8))
    # підписи: найближче вільне місце навколо знака (8 напрямків, віддалення до 46 px), у межах схеми;
    # далекий підпис з’єднується зі знаком виносною лінією; спершу — треки (вони важливіші)
    for p in sorted(pts, key=lambda p: p["kind"] != "трек"):
        if p["kind"] == "об’єкт":
            continue
        w = len(p["label"]) * (10.4 if p["kind"] == "трек" else 9.4)
        best = None
        for r in (0, 8, 16, 26, 36, 46):
            for dx, dy, anchor in ((10, 5, "start"), (-10, 5, "end"), (10, -9, "start"), (10, 19, "start"),
                                   (-10, -9, "end"), (-10, 19, "end"), (-w / 2, -13, "start"), (-w / 2, 23, "start")):
                ux, uy = (1 if dx > 0 else -1 if anchor == "end" else 0), (1 if dy > 10 else -1 if dy < 0 else 0)
                lx, ly = p["x"] + dx + ux * r, p["y"] + dy + uy * r
                x0 = lx if anchor == "start" else lx - w
                box = (x0, ly - 14, x0 + w, ly + 3)
                if box[0] < 2 or box[2] > 698 or box[1] < 2 or box[3] > MAP_H - 2:
                    continue
                hit = sum(box[0] < b[2] and b[0] < box[2] and box[1] < b[3] and b[1] < box[3] for b in boxes)
                if best is None or hit < best[0]:
                    best = (hit, lx, ly, anchor, box, r)
                if hit == 0:
                    break
            if best and best[0] == 0:
                break
        _, p["lx"], p["ly"], p["anchor"], box, r = best
        if r >= 16:                                 # виносна лінія від знака до найближчої точки підпису
            p["leader"] = (min(max(p["x"], box[0]), box[2]), min(max(p["y"], box[1]), box[3]))
        boxes.append(box)
    return pts


@app.route("/situation")
def situation():
    need("track.read")
    queue = rows("SELECT * FROM v_threat_queue")
    kpi = row("SELECT (SELECT count(*) FROM v_threat_queue) AS threats, "
              "(SELECT count(*) FROM mission WHERE state IN ('санкціонована', 'прийнята', 'виконується')) AS active, "
              "(SELECT count(*) FROM crew WHERE status = 'готовий') AS crews, "
              "(SELECT count(*) FROM sensor WHERE status IN ('у мережі', 'деградований')) AS sensors_on, "
              "(SELECT count(*) FROM sensor) AS sensors")
    return render_template("situation.html", queue=queue, kpi=kpi, pts=map_points(), map_h=MAP_H)


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
                "ORDER BY d.detected_at DESC LIMIT 5", tid)
    cands = rows("SELECT * FROM fn_crew_candidates(%s) LIMIT 5", tid)
    active = row("SELECT mission_id, mission_no, state FROM mission WHERE track_id = %s "
                 "AND state NOT IN ('відхилена', 'скасована', 'закрита')", tid)
    return render_template("track.html", t=t, dets=dets, cands=cands, active=active,
                           identities=enum_values("air_track_identity"))


@app.route("/detections/new", methods=["GET", "POST"])
def detection_new():
    """Ручне донесення оператора поста спостереження — той самий шлях, що й REST API шлюзу (fn_ingest_detection)."""
    need("detection.write")
    f = request.form
    if request.method == "POST":
        try:
            with tx() as cur:
                r = cur.execute("SELECT * FROM fn_ingest_detection(%s, now(), %s::numeric, %s::numeric, %s::numeric, "
                                "%s::numeric, NULL, %s, %s::numeric)",
                                (f["sensor"], f["lat"], f["lon"], f.get("alt") or None, f.get("speed") or None,
                                 f["signature"], f["confidence"])).fetchone()
            flash(f"Донесення прийнято: трек {r['track_number']}", "ok")
            return redirect(url_for("track", tid=r["track_id"]))
        except (psycopg.Error, KeyError) as e:
            db_error(e)
    posts = rows("SELECT hw_serial, lat, lon FROM sensor WHERE kind = 'пост спостереження' "
                 "AND status IN ('у мережі', 'деградований') ORDER BY hw_serial")
    return render_template("detection_form.html", posts=posts, f=f)


# ------------------------------------------------------------------------------------------ місії
@app.route("/missions")
def missions():
    need("mission.read")
    a = request.args
    st, crew, q = a.get("state", ""), a.get("crew", ""), a.get("q", "").strip()
    frm, to = a.get("from") or "2000-01-01", a.get("to") or "2100-01-01"
    src = ("FROM mission m JOIN air_track t USING (track_id) JOIN crew c USING (crew_id) "
           "LEFT JOIN engagement_report r USING (mission_id) WHERE (%s = '' OR m.state::text = %s) "
           "AND (%s = '' OR c.call_sign = %s) AND (%s = '' OR m.mission_no ILIKE %s OR t.track_number ILIKE %s) "
           "AND m.proposed_at >= %s::date AND m.proposed_at < %s::date + 1 ")
    args = (st, st, crew, crew, q, f"%{q}%", f"%{q}%", frm, to)
    pg = pager(row("SELECT count(*) AS n " + src, *args)["n"])
    ms = rows("SELECT m.mission_id, m.mission_no, m.state, m.proposed_at, m.closed_at, t.track_number, "
              "c.call_sign, r.assessment " + src + "ORDER BY m.proposed_at DESC LIMIT %s OFFSET %s",
              *args, PAGE, pg["offset"])
    total = row("SELECT count(*) AS n FROM mission")["n"]
    crews = [r["call_sign"] for r in rows("SELECT call_sign FROM crew ORDER BY call_sign")]
    return render_template("missions.html", ms=ms, states=enum_values("mission_state"), crews=crews, a=a,
                           total=total, pg=pg)


def _perm_for(frm, to):
    r = row("SELECT perm FROM mission_transition WHERE from_state = %s AND to_state = %s", frm, to)
    return r["perm"] if r else None


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
    # дії розрахунку доступні лише розрахунку, якому призначено місію (те саме перевіряє тригер БД)
    own = g.user["crew_id"] is None or g.user["crew_id"] == m["crew_id"]
    trans = [dict(to=r["to_state"], label=TRANSITION_LABEL[r["to_state"]]) for r in
             rows("SELECT to_state::text FROM mission_transition WHERE from_state = %s ORDER BY to_state", m["state"])
             if r["to_state"] != "закрита" and _perm_for(m["state"], r["to_state"]) in g.perms and own]
    events = rows("SELECT e.event_at, e.event_type, e.payload, u.full_name FROM mission_event e "
                  "LEFT JOIN personnel u ON u.user_id = e.actor_id WHERE e.mission_id = %s ORDER BY e.event_at", mid)
    ints = rows("SELECT interceptor_id, serial_no, im.name AS model FROM interceptor JOIN interceptor_model im "
                "USING (model_id) WHERE position_id = %s AND state = 'готовий' ORDER BY serial_no", m["position_id"])
    tele = rows("SELECT ts, lat, lon, alt_m, ground_speed_mps, battery_pct, link_quality_pct FROM telemetry_frame "
                "WHERE mission_id = %s ORDER BY ts DESC LIMIT 3", mid)
    return render_template("mission.html", m=m, trans=trans, events=events, ints=ints, tele=tele,
                           can_report=m["state"] == "виконується" and "mission.report" in g.perms and own)


# ------------------------------------------------------------------------------------------ ресурси (CRUD)
@app.route("/resources")
def resources():
    need("resource.read")
    ready = rows("SELECT * FROM v_readiness")
    pos, st = request.args.get("pos", ""), request.args.get("state", "")
    src = ("FROM interceptor i JOIN interceptor_model im USING (model_id) LEFT JOIN position p USING (position_id) "
           "WHERE (%s = '' OR p.code = %s) AND (%s = '' OR i.state::text = %s) ")
    pg = pager(row("SELECT count(*) AS n " + src, pos, pos, st, st)["n"])
    ints = rows("SELECT i.interceptor_id, i.serial_no, im.name AS model, i.state, i.flight_count, "
                "i.firmware_version, p.code AS pos " + src + "ORDER BY i.serial_no LIMIT %s OFFSET %s",
                pos, pos, st, st, PAGE, pg["offset"])
    return render_template("resources.html", ready=ready, ints=ints, pos=pos, st=st, pg=pg,
                           states=enum_values("interceptor_state"))


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
    if iid and not it:
        abort(404)
    return render_template("interceptor_form.html", it=it,
                           models=rows("SELECT model_id, name FROM interceptor_model ORDER BY name"),
                           positions=rows("SELECT position_id, code FROM position ORDER BY code"),
                           states=enum_values("interceptor_state"))


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


# ------------------------------------------------------------------------------------------ сенсори
@app.route("/sensors")
def sensors():
    need("sensor.manage")
    a = request.args
    kind, st, q = a.get("kind", ""), a.get("status", ""), a.get("q", "").strip()
    total = row("SELECT count(*) AS n FROM sensor WHERE (%s = '' OR kind::text = %s) AND (%s = '' OR status::text = %s) "
                "AND (%s = '' OR hw_serial ILIKE %s)", kind, kind, st, st, q, f"%{q}%")["n"]
    pg = pager(total)
    ss = rows("SELECT s.sensor_id, s.hw_serial, s.kind, s.status, s.lat, s.lon, s.height_m, s.last_heartbeat_at, "
              "sc.code AS sector FROM sensor s JOIN sector sc USING (sector_id) WHERE (%s = '' OR s.kind::text = %s) "
              "AND (%s = '' OR s.status::text = %s) AND (%s = '' OR s.hw_serial ILIKE %s) ORDER BY s.hw_serial "
              "LIMIT %s OFFSET %s", kind, kind, st, st, q, f"%{q}%", PAGE, pg["offset"])
    return render_template("sensors.html", ss=ss, a=a, total=total, pg=pg, kinds=enum_values("sensor_kind"),
                           statuses=enum_values("sensor_status"))


@app.route("/sensors/new", methods=["GET", "POST"])
@app.route("/sensors/<uuid:sid>/edit", methods=["GET", "POST"])
def sensor_form(sid=None):
    need("sensor.manage")
    s = row("SELECT * FROM sensor WHERE sensor_id = %s", sid) if sid else None
    if sid and not s:
        abort(404)
    if request.method == "POST":
        f = request.form
        try:
            with tx() as cur:
                if sid:
                    cur.execute("UPDATE sensor SET status = %s, lat = %s, lon = %s, height_m = %s, sector_id = %s "
                                "WHERE sensor_id = %s",
                                (f["status"], f["lat"], f["lon"], f["height_m"], f["sector_id"], sid))
                else:
                    cur.execute("INSERT INTO sensor (sector_id, hw_serial, kind, lat, lon, height_m) VALUES "
                                "(%s, %s, %s, %s, %s, %s)",
                                (f["sector_id"], f["hw_serial"], f["kind"], f["lat"], f["lon"], f["height_m"]))
            flash("Сенсор збережено", "ok")
            return redirect(url_for("sensors"))
        except psycopg.Error as e:
            db_error(e)
            s = {**(s or {}), **f.to_dict()}
    nxt = [r["to_state"] for r in rows("SELECT to_state::text FROM sensor_transition WHERE from_state = %s "
                                       "ORDER BY to_state", s["status"])] if sid else []
    return render_template("sensor_form.html", s=s, sid=sid, kinds=enum_values("sensor_kind"), nxt=nxt,
                           sectors=rows("SELECT sector_id, code, name FROM sector ORDER BY code"))


# ------------------------------------------------------------------------------------------ об’єкти прикриття
@app.route("/objects")
def objects():
    need("sector.manage")
    cat = request.args.get("cat", "")
    obs = rows("SELECT o.object_id, o.name, o.category, o.lat, o.lon, s.code AS sector, "
               "(SELECT count(*) FROM air_track t WHERE t.predicted_object_id = o.object_id) AS threats "
               "FROM protected_object o JOIN sector s USING (sector_id) WHERE %s = '' OR o.category::text = %s "
               "ORDER BY o.category, o.name", cat, cat)
    return render_template("objects.html", obs=obs, cat=cat)


@app.route("/objects/<uuid:oid>/edit", methods=["GET", "POST"])
def object_form(oid):
    need("sector.manage")
    o = row("SELECT * FROM protected_object WHERE object_id = %s", oid)
    if not o:
        abort(404)
    if request.method == "POST":
        f = request.form
        try:
            with tx() as cur:
                cur.execute("UPDATE protected_object SET name = %s, category = %s, lat = %s, lon = %s "
                            "WHERE object_id = %s", (f["name"], f["category"], f["lat"], f["lon"], oid))
            flash("Об’єкт прикриття збережено", "ok")
            return redirect(url_for("objects"))
        except psycopg.Error as e:
            db_error(e)
    return render_template("object_form.html", o=o, cats=enum_values("object_category"))


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
                 "ORDER BY n DESC, hits DESC", frm, to)
    return render_template("analytics.html", st=st, crews=crews, frm=frm, to=to)


@app.route("/audit")
def audit():
    need("audit.read")
    ent = request.args.get("entity", "")
    ver = row("SELECT * FROM fn_audit_verify()")
    pg = pager(row("SELECT count(*) AS n FROM audit_log WHERE %s = '' OR entity = %s", ent, ent)["n"])
    log = rows("SELECT a.entry_id, a.logged_at, a.action, a.entity_id, a.actor_type, u.full_name, a.hash "
               "FROM audit_log a LEFT JOIN personnel u ON u.user_id = a.actor_id WHERE %s = '' OR a.entity = %s "
               "ORDER BY a.entry_id DESC LIMIT %s OFFSET %s", ent, ent, PAGE, pg["offset"])
    ents = [r["entity"] for r in rows("SELECT DISTINCT entity FROM audit_log ORDER BY entity")]
    return render_template("audit.html", ver=ver, log=log, ent=ent, ents=ents, pg=pg)


# ------------------------------------------------------------------------------------------ користувачі, ролі
@app.route("/users")
def users():
    need("user.manage", "user.block")
    a = request.args
    role, st, q = a.get("role", ""), a.get("status", ""), a.get("q", "").strip()
    src = ("FROM personnel u JOIN role r USING (role_id) LEFT JOIN crew c USING (crew_id) "
           "WHERE (%s = '' OR r.code = %s) AND (%s = '' OR u.status::text = %s) "
           "AND (%s = '' OR u.full_name ILIKE %s OR u.login ILIKE %s) ")
    args = (role, role, st, st, q, f"%{q}%", f"%{q}%")
    pg = pager(row("SELECT count(*) AS n " + src, *args)["n"])
    us = rows("SELECT u.user_id, u.full_name, u.login, u.rank, u.status, u.mfa_enabled, u.admission_valid_to, "
              "r.code, r.name AS role, c.call_sign " + src + "ORDER BY r.code, u.login LIMIT %s OFFSET %s",
              *args, PAGE, pg["offset"])
    roles_ = rows("SELECT code, name FROM role ORDER BY code")
    return render_template("users.html", us=us, a=a, roles=roles_, pg=pg, statuses=enum_values("personnel_status"))


@app.route("/users/new", methods=["GET", "POST"])
@app.route("/users/<uuid:uid>/edit", methods=["GET", "POST"])
def user_form(uid=None):
    need("user.manage")
    u = row("SELECT * FROM personnel WHERE user_id = %s", uid) if uid else None
    if uid and not u:
        abort(404)
    if request.method == "POST":
        f = request.form
        pw = f.get("password", "")
        try:
            if not uid and len(pw) < 8:
                raise ValueError("Пароль нового користувача — щонайменше 8 символів")
            if pw and len(pw) < 8:
                raise ValueError("Пароль — щонайменше 8 символів")
            with tx() as cur:
                vals = (f["full_name"], f["rank"] or None, f["role_id"], f["crew_id"] or None,
                        f["admission_valid_to"] or None, "mfa_enabled" in f)
                if uid:
                    cur.execute("UPDATE personnel SET full_name = %s, rank = %s, role_id = %s, crew_id = %s, "
                                "admission_valid_to = %s, mfa_enabled = %s WHERE user_id = %s", (*vals, uid))
                    if pw:
                        cur.execute("UPDATE personnel SET password_hash = %s WHERE user_id = %s",
                                    (generate_password_hash(pw), uid))
                else:
                    cur.execute("INSERT INTO personnel (full_name, rank, role_id, crew_id, admission_valid_to, "
                                "mfa_enabled, login, password_hash) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                                (*vals, f["login"], generate_password_hash(pw)))
            flash("Обліковий запис збережено", "ok")
            return redirect(url_for("users"))
        except ValueError as e:
            flash(str(e), "error")
        except psycopg.Error as e:
            db_error(e)
        u = {**(u or {}), **f.to_dict(), "mfa_enabled": "mfa_enabled" in f}
    return render_template("user_form.html", u=u, uid=uid,
                           roles=rows("SELECT role_id, code, name FROM role ORDER BY code"),
                           crews=rows("SELECT crew_id, call_sign FROM crew ORDER BY call_sign"))


@app.route("/users/<uuid:uid>/status", methods=["POST"])
def user_status(uid):
    """Блокування / розблокування облікового запису (офіцер кібербезпеки або адміністратор)."""
    need("user.block", "user.manage")
    to = request.form["status"]
    if str(uid) == session["uid"]:
        flash("Неможливо змінити стан власного облікового запису", "error")
    else:
        try:
            with tx() as cur:
                cur.execute("UPDATE personnel SET status = %s, failed_logins = 0 WHERE user_id = %s", (to, uid))
            flash(f"Стан облікового запису: {to}", "ok")
        except psycopg.Error as e:
            db_error(e)
    return redirect(request.referrer or url_for("users"))


@app.route("/roles", methods=["GET", "POST"])
def roles():
    """Матриця «роль — право» (RBAC) з можливістю надати або відкликати право."""
    need("role.manage")
    if request.method == "POST":
        role_id, perm_id, grant = request.form["role_id"], request.form["permission_id"], request.form["grant"] == "1"
        try:
            with tx() as cur:                     # обмеження матриці перевіряє тригер role_permission_guard
                if grant:
                    cur.execute("INSERT INTO role_permission (role_id, permission_id) VALUES (%s, %s) "
                                "ON CONFLICT DO NOTHING", (role_id, perm_id))
                else:
                    cur.execute("DELETE FROM role_permission WHERE role_id = %s AND permission_id = %s",
                                (role_id, perm_id))
            flash("Матрицю прав оновлено", "ok")
        except psycopg.Error as e:
            db_error(e)
        return redirect(url_for("roles"))
    rs = rows("SELECT role_id, code, name, combat_rights FROM role ORDER BY code")
    ps = rows("SELECT permission_id, code, description FROM permission ORDER BY permission_id")
    has = {(r["role_id"], r["permission_id"]) for r in rows("SELECT role_id, permission_id FROM role_permission")}
    return render_template("roles.html", rs=rs, ps=ps, has=has, combat=COMBAT_PERMS)


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
    except KeyError as e:
        return jsonify(error=f"missing field {e}"), 422
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
