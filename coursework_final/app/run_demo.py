#!/usr/bin/env python3
"""Демонстрація прототипу «Щит-Лінк» для пояснювальної записки курсової роботи.

1) тимчасовий кластер PostgreSQL → db/schema.sql + db/impl.sql → seed;
2) запуск веб-застосунку (Flask) і вимірювання часу обробки виявлення REST API;
3) сценарні знімки екрана всіх екранів прототипу (headless Chrome, 720 px × 3) → ../diagrams/screens/*.png;
4) факти для записки (версії, кількість об’єктів БД і записів, маршрути, стенд) → demo.json.

    .venv/bin/python coursework_final/app/run_demo.py
"""
import json
import logging
import os
import platform
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import timedelta
from importlib.metadata import version
from pathlib import Path

import psycopg
from PIL import Image
from werkzeug.serving import make_server

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(HERE / "db")]
import pgtemp  # noqa: E402
import seed  # noqa: E402

SHOTS = HERE.parent / "diagrams" / "screens"
# робочі екрани ролей, не показані окремими рисунками: (код, логін, сторінка, елемент, по нижній край якого
# обрізається знімок, щоб зріз не проходив крізь текст)
F = "form.inline"
ROLE_SCREENS = [("r03", "an1", "/tracks/{tid}", ".cols"), ("r05", "pilot01", "/missions?state=&crew=&q=&from={d0}&to={d1}",
                 "form.filter"), ("r07", "r07_1", "/sensors", F), ("r09", "r09_1", "/analytics", F),
                ("r10", "r10_1", "/roles", "p.muted"), ("r11", "r11_1", "/audit", F),
                ("r12", "r12_1", "/objects", F), ("r13", "r13_1", "/", ".tiles")]
CROP_JS = "JSON.stringify([0, document.querySelector('%s').getBoundingClientRect().bottom])"
BOX_JS = ("JSON.stringify([document.querySelector('header').getBoundingClientRect().bottom, "
          "document.querySelector('%s').getBoundingClientRect().bottom])")
PORT, WIDTH, SCALE, MIN_CSS_PX = 5097, 720, 3, 16        # найменший шрифт інтерфейсу — 16 px


def layout(png, width_cm=16.5):
    """layout.json для знімка: кегль найменшого шрифту на сторінці при ширині width_cm (≥ 10 pt)."""
    w, h = Image.open(png).size
    width_cm = min(width_cm, 22.5 * w / h)               # знімок разом із підписом має вміститися на сторінці
    pt = MIN_CSS_PX * 0.75 * (width_cm / 2.54 * 96) / WIDTH
    lay = {"file": png.name, "native_px": [w, h], "min_font_px": MIN_CSS_PX * SCALE,
           "portrait": {"width_cm": round(width_cm, 2), "font_pt": round(pt, 1), "dpi": round(w / (width_cm / 2.54))},
           "orientation": "portrait", "width_cm": round(width_cm, 2),
           "legible": pt >= 10 and w / (width_cm / 2.54) >= 300}
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


def loc(path):
    return sum(1 for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip())


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    res = {}
    with pgtemp.TempCluster(port=54397) as pg:
        pg.psql_file(pgtemp.SCHEMA)
        pg.psql_file(pgtemp.IMPL)
        conn = psycopg.connect(pg.dsn, autocommit=True)
        t0 = time.perf_counter()
        with psycopg.connect(pg.dsn) as sc:
            res["seed_outcomes"] = seed.seed(sc)
        res["seed_seconds"] = round(time.perf_counter() - t0, 1)
        one = lambda sql, *a: conn.execute(sql, a or None).fetchone()[0]                   # noqa: E731
        tables = [r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
                                             "ORDER BY tablename")]
        res["counts"] = {t: one(f"SELECT count(*) FROM {t}") for t in tables}
        res["objects"] = {
            "tables": len(tables),
            "functions": one("SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                             "WHERE n.nspname = 'public' AND p.prokind = 'f' AND NOT EXISTS (SELECT 1 FROM pg_depend d "
                             "WHERE d.objid = p.oid AND d.deptype = 'e')"),
            "triggers": one("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal"),
            "views": one("SELECT count(*) FROM pg_views WHERE schemaname = 'public'"),
            "enums": one("SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace "
                         "WHERE n.nspname = 'public' AND t.typtype = 'e'"),
            "db_roles": one("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'shch_%'")}
        res["versions"] = {"postgresql": one("SHOW server_version"), "python": platform.python_version(),
                           **{p: version(p) for p in ("flask", "werkzeug", "jinja2", "psycopg", "pytest")}}

        os.environ["SHCH_DSN"] = pg.dsn.replace("user=postgres", "user=shch_app")
        import app as webapp  # noqa: E402
        webapp.DSN = pg.dsn.replace("user=postgres", "user=shch_app")
        res["routes"] = sorted({(r.rule, ",".join(sorted(m for m in r.methods if m in ("GET", "POST"))), r.endpoint)
                                for r in webapp.app.url_map.iter_rules() if r.endpoint != "static"})
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        srv = make_server("127.0.0.1", PORT, webapp.app, threaded=True)
        threading.Thread(target=srv.serve_forever, daemon=True).start()

        # ------------------------------------------------------------------ REST API і час обробки
        tid = one("SELECT track_id FROM v_threat_queue WHERE active_mission IS NULL AND identity = 'ворожа' "
                  "ORDER BY threat_score DESC LIMIT 1")
        sensor = one("SELECT s.hw_serial FROM detection d JOIN sensor s USING (sensor_id) WHERE d.track_id = %s "
                     "ORDER BY d.detected_at DESC LIMIT 1", tid)
        lat, lon, spd = conn.execute("SELECT lat, lon, speed FROM fn_track_pos(%s)", (tid,)).fetchone()
        t_last = one("SELECT last_update_at FROM air_track WHERE track_id = %s", tid)
        body = {"sensor": sensor, "detected_at": (t_last + timedelta(seconds=2)).isoformat(), "lat": float(lat) + 0.002,
                "lon": float(lon) + 0.003, "alt": 210, "speed": float(spd), "confidence": 0.91,
                "signature": "ударний поршневий"}
        res["api_ok"] = api("/api/v1/detections", body)
        res["api_noauth"] = api("/api/v1/detections", body, token="wrong")[0]
        lat_ms = []
        for k in range(50):
            b = {**body, "detected_at": (t_last + timedelta(seconds=3 + k * 0.2)).isoformat(),
                 "lat": float(lat) + 0.002 + k * 0.0001}
            t1 = time.perf_counter()
            st, _ = api("/api/v1/detections", b)
            lat_ms.append((time.perf_counter() - t1) * 1000)
            assert st == 201, st
        lat_ms.sort()
        res["api_latency_ms"] = {"n": 50, "median": round((lat_ms[24] + lat_ms[25]) / 2, 1),
                                 "p95": round(lat_ms[47], 1), "max": round(lat_ms[-1], 1)}

        # ------------------------------------------------------------------ сценарні знімки екрана
        pw = seed.DEMO_PASSWORD
        crew = conn.execute("SELECT crew_id FROM fn_crew_candidates(%s) LIMIT 1", (tid,)).fetchone()[0]
        cmd = one("SELECT login FROM personnel u JOIN role r USING (role_id) WHERE u.crew_id = %s AND r.code = 'R-04'",
                  crew)
        edit = one("SELECT i.interceptor_id FROM interceptor i JOIN position p USING (position_id) "
                   "WHERE p.code = 'П-01' AND i.state = 'готовий' ORDER BY i.serial_no LIMIT 1")
        used = one("SELECT i.interceptor_id FROM interceptor i JOIN position p USING (position_id) "
                   "WHERE p.code = 'П-01' AND i.flight_count > 0 ORDER BY i.serial_no LIMIT 1")
        off = one("SELECT sensor_id FROM sensor WHERE status = 'поза мережею' ORDER BY hw_serial LIMIT 1")
        mission_no = one("SELECT mission_no FROM mission WHERE state = 'закрита' ORDER BY proposed_at LIMIT 1")
        steps = [{"base": f"http://127.0.0.1:{PORT}"},
                 {"goto": "/logout"}, {"fill": ["#login", "och1"]}, {"eval": CROP_JS % ".login.card", "key": "crop_s01_login"}, {"shot": "s01_login"},
                 {"login": ["och1", pw]}, {"shot": "s02_home_och"},
                 {"login": ["obu1", pw]}, {"goto": "/situation"}, {"eval": CROP_JS % "table tr:nth-of-type(4)", "key": "crop_s03_situation"},
                 {"shot": "s03_situation"},
                 {"goto": f"/tracks/{tid}"}, {"shot": "s04_track"},
                 {"clickText": "Запропонувати місію"}, {"eval": "location.pathname", "key": "mission"},
                 {"shot": "s05_proposed"},
                 {"login": ["och1", pw]}, {"gotoVar": "mission"}, {"clickText": "Санкціонувати"},
                 {"shot": "s06_approved"},
                 {"login": [cmd, pw]}, {"shot": "s07_home_cmd"},
                 {"gotoVar": "mission"}, {"clickText": "Прийняти завдання"}, {"clickText": "Пуск"},
                 {"shot": "s08_launched"},
                 {"clickText": "Доповісти результат"}, {"shot": "s09_closed"},
                 {"login": ["obu1", pw]}, {"goto": f"/missions?state=закрита&crew=&q=&from={(t_last - timedelta(days=30)).date()}&to={t_last.date()}"},
                 {"eval": CROP_JS % "table tr:nth-of-type(7)", "key": "crop_s10_missions_filter"},
                 {"shot": "s10_missions_filter"},
                 {"goto": f"/search?q={mission_no[:6]}"}, {"shot": "s11_search"},
                 {"login": ["r06_1", pw]}, {"goto": "/detections/new"}, {"fill": ["input[name=lat]", "51.705"]},
                 {"fill": ["input[name=lon]", "31.220"]}, {"fill": ["input[name=alt]", "150"]},
                 {"fill": ["input[name=speed]", "45"]}, {"shot": "s12_detection_form"},
                 {"clickText": "Надіслати донесення"}, {"shot": "s13_detection_result"},
                 {"login": ["r08_1", pw]}, {"goto": "/resources?pos=П-01&state="}, {"shot": "s14_resources"},
                 {"goto": f"/interceptors/{edit}/edit"}, {"fill": ["input[name=firmware_version]", "4.3.1"]},
                 {"shot": "s15_interceptor_edit"}, {"clickText": "Зберегти"},
                 {"goto": "/resources?pos=П-01&state="},
                 {"click": f"form[action='/interceptors/{used}/delete'] button"}, {"shot": "s16_delete_refused"},
                 {"login": ["r07_1", pw]}, {"goto": "/sensors?q=&kind=&status=поза+мережею"},
                 {"shot": "s17_sensors_filter"},
                 {"goto": f"/sensors/{off}/edit"}, {"shot": "s18_sensor_edit"},
                 {"login": ["r12_1", pw]}, {"shot": "s19_home_r12"},
                 {"goto": "/objects?cat=I"}, {"shot": "s20_objects"},
                 {"login": ["r09_1", pw]}, {"goto": "/analytics"}, {"shot": "s21_analytics"},
                 {"login": ["r10_1", pw]}, {"shot": "s22_home_admin"},
                 {"goto": "/users?q=&role=R-04&status="}, {"shot": "s23_users"},
                 {"goto": "/users/new"}, {"fill": ["input[name=login]", "an_new"]},
                 {"fill": ["input[name=full_name]", "Новий А. Б."]}, {"fill": ["input[name=rank]", "лейтенант"]},
                 {"select": ["select[name=role_id]", str(one("SELECT role_id FROM role WHERE code = 'R-03'"))]},
                 {"shot": "s24_user_new"},
                 {"goto": "/roles"}, {"shot": "s25_roles"},
                 {"login": ["r11_1", pw]}, {"goto": "/audit?entity=mission"}, {"shot": "s26_audit"},
                 {"login": ["r10_1", pw]}, {"goto": "/situation"}, {"shot": "s27_forbidden"},
                 *[st for code, login, url, sel in ROLE_SCREENS for st in (
                     {"login": [login, pw]},
                     {"goto": url.format(tid=tid, d0=(t_last - timedelta(days=30)).date(), d1=t_last.date())},
                     {"eval": BOX_JS % sel.replace("'", "\\'"), "key": f"box_{code}"},
                     {"shot": f"h_{code}"})]]
        sf = SHOTS / "steps.json"
        sf.write_text(json.dumps(steps, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run(["node", str(HERE / "shots.mjs"), str(sf), str(SHOTS), str(WIDTH), str(SCALE)],
                           capture_output=True, text=True)
        sf.unlink()
        if r.returncode:
            sys.exit("screenshots failed:\n" + r.stderr)
        res["shots"] = {k: v for k, v in json.loads(r.stdout.strip().splitlines()[-1]).items() if isinstance(v, dict)}
        # робочі екрани ролей: заголовок (меню, ПІБ, роль) і верхня частина робочої сторінки; межа заголовка — з DOM
        allout = json.loads(r.stdout.strip().splitlines()[-1])
        # довгі сторінки обрізаються по нижньому краю змістовного елемента (форма, перші рядки таблиці)
        for k in [k for k in allout if k.startswith("crop_")]:
            name, bottom = k[5:], json.loads(allout[k])[1]
            im = Image.open(SHOTS / f"{name}.png")
            im.crop((0, 0, im.width, min(im.height, round((bottom + (16 if "login" in name else 1)) * SCALE)))).save(SHOTS / f"{name}.png")
        strips = {}
        for code, *_ in ROLE_SCREENS:
            box = json.loads(allout[f"box_{code}"])
            im = Image.open(SHOTS / f"h_{code}.png")
            strips[code] = im.crop((0, 0, im.width, min(im.height, round((box[1] + 5) * SCALE))))
            (SHOTS / f"h_{code}.png").unlink()
            res["shots"].pop(f"h_{code}", None)
        for name, codes in (("s28_roles_a", ("r03", "r05", "r07", "r09")), ("s28_roles_b", ("r10", "r11", "r12", "r13"))):
            parts, gap = [strips[c] for c in codes], 6 * SCALE
            comp = Image.new("RGB", (parts[0].width, sum(x.height for x in parts) + gap * (len(parts) - 1)), "#9aa3ad")
            y = 0
            for x in parts:
                comp.paste(x, (0, y)); y += x.height + gap
            comp.save(SHOTS / f"{name}.png")
            res["shots"][name] = {"url": "/ (" + ", ".join(codes) + ")", "cssHeight": comp.height // SCALE}
        for name in res["shots"]:
            lay = layout(SHOTS / f"{name}.png")
            res["shots"][name].update(font_pt=lay["portrait"]["font_pt"], width_cm=lay["width_cm"])
            if not lay["legible"]:
                sys.exit(f"{name}: {lay['portrait']['font_pt']} pt — знімок задовгий, скоротіть сторінку")
        res["demo_mission"] = conn.execute(
            "SELECT m.mission_no, m.state::text, r.assessment::text, c.call_sign, (SELECT count(*) FROM mission_event e "
            "WHERE e.mission_id = m.mission_id), t.state::text FROM mission m JOIN crew c USING (crew_id) "
            "JOIN air_track t USING (track_id) LEFT JOIN engagement_report r USING (mission_id) "
            "WHERE m.track_id = %s", (tid,)).fetchone()
        res["audit_after_demo"] = list(conn.execute("SELECT * FROM fn_audit_verify()").fetchone())
        srv.shutdown()
        conn.close()

    res["loc"] = {str(p.relative_to(HERE)): loc(p) for p in
                  [HERE / "app.py", HERE / "db/schema.sql", HERE / "db/impl.sql", HERE / "db/seed.py",
                   *sorted((HERE / "templates").glob("*.html")), HERE / "static/style.css",
                   *sorted((HERE / "tests").glob("*.py")), HERE / "run_demo.py", HERE / "pgtemp.py",
                   HERE / "shots.mjs"]}
    lscpu = subprocess.run(["lscpu"], capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"}).stdout
    cpu = next((ln.split(":", 1)[1].strip() for ln in lscpu.splitlines() if ln.startswith("Model name")), "")
    mem_kb = int(next(ln.split()[1] for ln in Path("/proc/meminfo").read_text().splitlines()
                      if ln.startswith("MemTotal")))
    res["stand"] = {"cpu": cpu, "logical_cpus": os.cpu_count(), "ram_gb": round(mem_kb / 1024 ** 2),
                    "os": platform.system() + " " + platform.release()}
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(HERE / "tests")],
                       capture_output=True, text=True, cwd=HERE)
    res["pytest"] = {"returncode": t.returncode, "summary": t.stdout.strip().splitlines()[-1]}
    (HERE / "demo.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("objects", "api_latency_ms", "demo_mission", "pytest")}, ensure_ascii=False,
                     default=str))
    if t.returncode:
        sys.exit("tests failed")


if __name__ == "__main__":
    main()
