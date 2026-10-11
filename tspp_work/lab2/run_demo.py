#!/usr/bin/env python3
"""Розгортання, наповнення, демонстрація та перевірка програмної реалізації БД «Щит-Лінк» (ЛР2).

1) тимчасовий кластер PostgreSQL → schema.sql (ЛР1) + impl.sql → seed (ФВ-БД-01, 02);
2) запуск веб-застосунку (Flask) і виклик REST API шлюзу (ФВ-БД-04);
3) сценарні знімки екрана (headless Chrome, 720 px × 3) → diagrams/scr_*.png + layout.json;
4) автоматична перевірка ФВ-БД-01 … ФВ-БД-13 → demo.json (дані для звіту).

    .venv/bin/python tspp_work/lab2/run_demo.py
"""
import json
import subprocess
import sys
import threading
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
from PIL import Image
from werkzeug.serving import make_server

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(HERE / "db"), str(HERE / "app")]
import pgtemp  # noqa: E402
import seed  # noqa: E402

DIAG = HERE / "diagrams"
PORT, WIDTH, SCALE, MIN_CSS_PX = 5087, 720, 3, 16


def layout(png, width_cm=16.5):
    """layout.json для знімка: кегль найменшого шрифту (16 css px) на сторінці при ширині width_cm."""
    w, h = Image.open(png).size
    width_cm = min(width_cm, 21.5 * w / h)          # знімок разом із підписом має вміститися на сторінці
    pt = MIN_CSS_PX * 0.75 * (width_cm / 2.54 * 96) / WIDTH
    lay = {"file": png.name, "native_px": [w, h], "min_font_px": MIN_CSS_PX * SCALE,
           "portrait": {"width_cm": width_cm, "font_pt": round(pt, 1), "dpi": round(w / (width_cm / 2.54))},
           "orientation": "portrait", "width_cm": width_cm, "legible": pt >= 10 and w / (width_cm / 2.54) >= 300}
    png.with_suffix(".layout.json").write_text(json.dumps(lay, ensure_ascii=False, indent=2), encoding="utf-8")
    return lay


def api(path, body=None, token="demo-gateway-token"):
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", method="POST" if body else "GET",
                                 data=json.dumps(body).encode() if body else None,
                                 headers={"Content-Type": "application/json", "X-Gateway-Token": token})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def expect_error(conn, sql, args=(), user=None):
    try:
        with conn.transaction():
            if user:
                conn.execute("SELECT set_config('app.user_id', %s, true)", (str(user),))
            conn.execute(sql, args or None)
    except psycopg.Error as e:
        return e.diag.message_primary
    return None


def main():
    DIAG.mkdir(exist_ok=True)
    res = {"fr": {}}
    with pgtemp.TempCluster() as pg:
        pg.psql_file(pgtemp.SCHEMA)
        pg.psql_file(pgtemp.IMPL)
        conn = psycopg.connect(pg.dsn, autocommit=True)
        t0 = datetime.now(timezone.utc)
        with psycopg.connect(pg.dsn) as sc:
            res["seed_outcomes"] = seed.seed(sc)
        res["seed_seconds"] = round((datetime.now(timezone.utc) - t0).total_seconds(), 1)
        one = lambda sql, *a: conn.execute(sql, a or None).fetchone()[0]                   # noqa: E731
        res["version"] = one("SHOW server_version")
        tables = [r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
                                             "ORDER BY tablename")]
        res["counts"] = {t: one(f"SELECT count(*) FROM {t}") for t in tables}
        res["objects"] = {
            "functions": one("SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                             "WHERE n.nspname = 'public'"),
            "triggers": one("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal"),
            "views": one("SELECT count(*) FROM pg_views WHERE schemaname = 'public'"),
            "roles": one("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'shch_%'"),
            "tables": len(tables)}

        # ------------------------------------------------------------------ застосунок і REST API
        import os
        os.environ["SHCH_DSN"] = pg.dsn
        import app as webapp  # noqa: E402
        srv = make_server("127.0.0.1", PORT, webapp.app, threaded=True)
        threading.Thread(target=srv.serve_forever, daemon=True).start()

        tid = one("SELECT track_id FROM v_threat_queue WHERE active_mission IS NULL AND identity = 'ворожа' "
                  "ORDER BY threat_score DESC LIMIT 1")
        live_sensor = one("SELECT d_s.hw_serial FROM detection d JOIN sensor d_s USING (sensor_id) "
                          "WHERE d.track_id = %s ORDER BY d.detected_at DESC LIMIT 1", tid)
        lat, lon, spd = conn.execute("SELECT lat, lon, speed FROM fn_track_pos(%s)", (tid,)).fetchone()
        t_last = one("SELECT last_update_at FROM air_track WHERE track_id = %s", tid)
        body = {"sensor": live_sensor, "detected_at": (t_last + timedelta(seconds=4)).isoformat(timespec="milliseconds"),
                "lat": float(lat) + 0.002, "lon": float(lon) + 0.003, "alt": 210, "speed": float(spd),
                "bearing": 187.5, "signature": "ударний поршневий", "confidence": 0.91}
        res["api_ok"] = (body, *api("/api/v1/detections", body))
        off = one("SELECT hw_serial FROM sensor WHERE status = 'поза мережею' LIMIT 1")
        res["api_off"] = (off, *api("/api/v1/detections", {**body, "sensor": off}))
        res["api_noauth"] = api("/api/v1/detections", body, token="wrong")
        res["api_threats"] = api("/api/v1/threats")
        import time                                  # час обробки виявлення сервером (30 послідовних запитів)
        lat_ms = []
        for k in range(30):
            b = {**body, "detected_at": (t_last + timedelta(seconds=5 + k * 0.5)).isoformat(),
                 "lat": float(lat) + 0.002 + k * 0.0001}
            t1 = time.perf_counter(); api("/api/v1/detections", b); lat_ms.append((time.perf_counter() - t1) * 1000)
        lat_ms.sort()
        res["api_latency_ms"] = {"median": round(lat_ms[15], 1), "p95": round(lat_ms[28], 1), "max": round(lat_ms[-1], 1)}

        # ------------------------------------------------------------------ сценарні знімки екрана
        crew = conn.execute("SELECT crew_id, call_sign FROM fn_crew_candidates(%s) LIMIT 1", (tid,)).fetchone()
        cmd = one("SELECT login FROM personnel u JOIN role r USING (role_id) WHERE u.crew_id = %s AND r.code = 'R-04'",
                  crew[0])
        used = one("SELECT i.interceptor_id FROM interceptor i JOIN position p USING (position_id) "
                   "WHERE p.code = 'П-01' AND i.flight_count > 0 ORDER BY i.serial_no LIMIT 1")
        edit = one("SELECT i.interceptor_id FROM interceptor i JOIN position p USING (position_id) "
                   "WHERE p.code = 'П-01' AND i.state = 'готовий' ORDER BY i.serial_no LIMIT 1")
        steps = [{"base": f"http://127.0.0.1:{PORT}"},
                 {"goto": "/login"}, {"shot": "scr_01_login"},
                 {"login": "obu1"}, {"goto": "/situation"}, {"shot": "scr_02_situation"},
                 {"goto": f"/tracks/{tid}"}, {"shot": "scr_03_track"},
                 {"clickText": "Запропонувати місію"}, {"eval": "location.pathname", "key": "mission"},
                 {"shot": "scr_04_proposed"},
                 {"login": "och1"}, {"gotoVar": "mission"}, {"clickText": "Санкціонувати"},
                 {"shot": "scr_05_approved"},
                 {"goto": "/missions"}, {"shot": "scr_06_missions"},
                 {"login": cmd}, {"gotoVar": "mission"}, {"clickText": "Прийняти завдання"},
                 {"shot": "scr_07_accepted"},
                 {"clickText": "Пуск"}, {"clickText": "Доповісти результат"}, {"shot": "scr_08_closed"},
                 {"login": "r08_1"}, {"goto": "/resources?pos=П-01"}, {"shot": "scr_09_resources"},
                 {"goto": f"/interceptors/{edit}/edit"}, {"fill": ["input[name=firmware_version]", "4.3.1"]},
                 {"shot": "scr_10_edit"}, {"clickText": "Зберегти"},
                 {"goto": "/resources?pos=П-01"}, {"click": f"form[action='/interceptors/{used}/delete'] button"},
                 {"shot": "scr_11_delete_refused"},
                 {"login": "r09_1"}, {"goto": "/analytics"}, {"shot": "scr_12_analytics"},
                 {"login": "r11_1"}, {"goto": "/audit"}, {"shot": "scr_13_audit"}]
        sf = DIAG / "steps.json"
        sf.write_text(json.dumps(steps, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run(["node", str(ROOT / "tools/bpmn/shots.mjs"), str(sf), str(DIAG), str(WIDTH), str(SCALE)],
                           capture_output=True, text=True)
        sf.unlink()
        if r.returncode:
            sys.exit("screenshots failed:\n" + r.stderr)
        res["shots"] = json.loads(r.stdout.strip().splitlines()[-1])
        for name in [k for k in res["shots"] if k.startswith("scr_")]:
            lay = layout(DIAG / f"{name}.png")
            res["shots"][name]["font_pt"] = lay["portrait"]["font_pt"]
            if not lay["legible"]:
                sys.exit(f"{name}: {lay['portrait']['font_pt']} pt — знімок задовгий, скоротіть сторінку")
        res["demo_mission"] = conn.execute(
            "SELECT m.mission_no, m.state, r.assessment, c.call_sign, (SELECT count(*) FROM mission_event e "
            "WHERE e.mission_id = m.mission_id) FROM mission m JOIN crew c USING (crew_id) "
            "LEFT JOIN engagement_report r USING (mission_id) WHERE m.track_id = %s", (tid,)).fetchone()
        srv.shutdown()

        # ------------------------------------------------------------------ перевірка ФВ-БД
        fr = res["fr"]
        o = res["objects"]
        fr["01"] = (o["tables"] == 19 and o["functions"] >= 15,
                    f"{o['tables']} таблиць (18 + mission_transition), {o['functions']} функцій, "
                    f"{o['triggers']} тригерів, {o['views']} представлення")
        c = res["counts"]
        dicts, mains = ("role", "permission", "role_permission", "sector", "interceptor_model"), \
            ("protected_object", "sensor", "position", "crew", "personnel", "interceptor")
        opers = ("air_track", "detection", "mission", "mission_event", "telemetry_frame", "engagement_report",
                 "audit_log")
        fr["02"] = (all(c[t] >= 10 for t in mains) and all(c[t] >= 20 for t in opers),
                    f"основні: {min(c[t] for t in mains)}–{max(c[t] for t in mains)} записів; операційні: "
                    f"{min(c[t] for t in opers)}–{max(c[t] for t in opers)}")
        e = expect_error(conn, "DELETE FROM interceptor WHERE interceptor_id = %s", (used,))
        n_before = c["interceptor"]
        with conn.transaction():
            iid = one("INSERT INTO interceptor (model_id, serial_no, received_at) SELECT model_id, 'ПХ-TEST', "
                      "current_date FROM interceptor_model LIMIT 1 RETURNING interceptor_id")
            conn.execute("UPDATE interceptor SET firmware_version = '9.9.9' WHERE interceptor_id = %s", (iid,))
            conn.execute("DELETE FROM interceptor WHERE interceptor_id = %s", (iid,))
        fr["03"] = (e is not None and one("SELECT count(*) FROM interceptor") == n_before,
                    "створення, зміна, видалення перехоплювача виконано; видалення використаного відхилено: " + str(e))
        ok_api = res["api_ok"][1] == 201 and res["api_ok"][2]["track_number"] is not None
        fr["04"] = (ok_api and res["api_off"][1] == 422 and res["api_noauth"][0] == 401,
                    f"201 → трек {res['api_ok'][2].get('track_number')}; сенсор поза мережею → 422; "
                    f"невірний ключ → 401")
        sc = [float(x[0]) for x in conn.execute("SELECT threat_score FROM v_threat_queue")]
        fr["05"] = (sc == sorted(sc, reverse=True) and len(sc) > 0, f"{len(sc)} треків, впорядковано за спаданням")
        # ФВ-БД-06: правило двох осіб і повний цикл через застосунок
        m_new = one("SELECT mission_id FROM mission WHERE state = 'санкціонована' LIMIT 1")
        e2 = expect_error(conn, "UPDATE mission SET approved_by = proposed_by WHERE mission_id = %s", (m_new,))
        dm = res["demo_mission"]
        fr["06"] = (e2 is not None and dm[1] == "закрита",
                    f"місія {dm[0]} пройшла цикл через інтерфейс ({dm[4]} подій); санкція автором відхилена")
        och = one("SELECT user_id FROM personnel WHERE login = 'och1'")
        e3 = expect_error(conn, "UPDATE mission SET state = 'виконується' WHERE mission_id = %s", (m_new,), och)
        e3b = expect_error(conn, "UPDATE mission SET state = 'прийнята' WHERE mission_id = %s", (m_new,), och)
        fr["07"] = (e3 is not None and e3b is not None, f"перехід «санкціонована → виконується»: {e3}; "
                    f"«прийнята» від ОЧ: {e3b}")
        res["transition_errors"] = [e3, e3b]
        rep_m = one("SELECT mission_id FROM engagement_report LIMIT 1")
        e4 = expect_error(conn, "INSERT INTO engagement_report (mission_id, assessment, submitted_by) SELECT "
                          "mission_id, 'промах', submitted_by FROM engagement_report WHERE mission_id = %s", (rep_m,))
        fc = one("SELECT sum(flight_count) FROM interceptor")
        launched = one("SELECT count(*) FROM mission WHERE launched_at IS NOT NULL")
        fr["08"] = (e4 is not None and fc == launched, f"повторний звіт відхилено; сума вильотів {fc} = кількості "
                    f"пусків {launched}")
        rd = conn.execute("SELECT count(*), sum(interceptors_ready) FROM v_readiness").fetchone()
        fr["09"] = (rd[0] == c["position"], f"{rd[0]} позицій, готових перехоплювачів {rd[1]}")
        st = conn.execute("SELECT * FROM fn_mission_stats(now() - interval '31 days', now() + interval '1 day')"
                          ).fetchone()
        res["stats"] = [str(x) for x in st]
        fr["10"] = (st[0] == one("SELECT count(*) FROM mission"), f"місій {st[0]}, влучань {st[1]} ({st[5]} %), "
                    f"пропозиція → санкція {st[6]} с, санкція → пуск {st[7]} с")
        dump = pg.dir / "shchit.dump"
        pg.tool("pg_dump", "-d", "shchit", "-Fc", "-f", str(dump))
        pg.psql("CREATE DATABASE shchit_restore", db="postgres")
        pg.tool("pg_restore", "-d", "shchit_restore", str(dump))
        with psycopg.connect(pg.dsn.replace("dbname=shchit", "dbname=shchit_restore")) as rc:
            same = all(rc.execute(f"SELECT count(*) FROM {t}").fetchone()[0] ==
                       one(f"SELECT count(*) FROM {t}") for t in tables)
            vr = rc.execute("SELECT * FROM fn_audit_verify()").fetchone()
        fr["13"] = (same, f"копія {dump.stat().st_size // 1024} КБ; відновлено {len(tables)} таблиць, кількість "
                    f"записів збігається; перевірка аудиту у копії: порушень {vr[1]}")
        res["dump_kb"] = dump.stat().st_size // 1024
        v0 = conn.execute("SELECT * FROM fn_audit_verify()").fetchone()
        e5 = expect_error(conn, "UPDATE audit_log SET action = 'x' WHERE entry_id = 5")
        e6 = expect_error(conn, "DELETE FROM audit_log WHERE entry_id = 5")
        with conn.transaction():                      # імітація зловмисника з правами суперкористувача
            conn.execute("ALTER TABLE audit_log DISABLE TRIGGER audit_immutable")
            conn.execute("UPDATE audit_log SET details = details || '{\"підроблено\": true}' WHERE entry_id = 40")
            conn.execute("ALTER TABLE audit_log ENABLE TRIGGER audit_immutable")
        v1 = conn.execute("SELECT * FROM fn_audit_verify()").fetchone()
        res["audit"] = dict(before=list(v0), after=list(v1), update_err=e5, delete_err=e6)
        fr["11"] = (v0[1] == 0 and e5 and e6 and v1[1] >= 1 and v1[2] == 40,
                    f"ланцюжок {v0[0]} записів цілий; UPDATE/DELETE заборонено; підробку запису № 40 виявлено")
        e7 = expect_error(conn, "SET LOCAL ROLE shch_analyst; INSERT INTO mission (mission_no, track_id, crew_id, "
                          "proposed_by) SELECT 'X', track_id, crew_id, proposed_by FROM mission LIMIT 1")
        e8 = expect_error(conn, "SET LOCAL ROLE shch_officer; SELECT count(*) FROM audit_log")
        with conn.transaction():
            conn.execute("SET LOCAL ROLE shch_security")
            sec_n = one("SELECT count(*) FROM audit_log")
        fr["12"] = (bool(e7) and bool(e8) and sec_n > 0, f"аналітик: {e7}; офіцер → audit_log: {e8}; офіцер "
                    f"кібербезпеки читає {sec_n} записів")
        res["roles_err"] = [e7, e8]
        conn.close()

    for k, (ok, msg) in sorted(fr.items()):
        print(f"ФВ-БД-{k}: {'OK ' if ok else 'FAIL'} {msg}")
    res["fr"] = {k: [bool(ok), msg] for k, (ok, msg) in fr.items()}
    (HERE / "demo.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if not all(ok for ok, _ in fr.values()):
        sys.exit("some FR checks failed")


if __name__ == "__main__":
    main()
