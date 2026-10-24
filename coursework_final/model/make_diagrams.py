#!/usr/bin/env python3
"""Діаграми курсової роботи → coursework_final/diagrams/.

Повторно використані (без змін змісту): структурна схема, послідовність робіт КП, дерево цілей, WBS (ЛР1 —
lab1/make_lab1.py), BPMN-моделі (ЛР2 — lab2/diagrams/*.bpmn), узагальнена архітектура та інформаційні потоки (ЛР7).
Нові, згенеровані з коду прототипу: діаграми класів (db/schema.sql), діаграма станів місії (таблиця
mission_transition у db/impl.sql), карта навігації (маршрути Flask), а також прецеденти (cw_model.UC_*).

    .venv/bin/python coursework_final/model/make_diagrams.py
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CW = HERE.parent
ROOT = CW.parent
DIAG = CW / "diagrams"
APP = CW / "app"
sys.path[:0] = [str(HERE), str(ROOT / "tools"), str(ROOT / "lab1"), str(APP), str(APP / "db")]
import cw_model as M  # noqa: E402
import make_lab1 as L1  # noqa: E402
from idef_model import render  # noqa: E402

# ------------------------------------------------------------------ розбір схеми БД і серверної логіки
SCHEMA = (APP / "db/schema.sql").read_text(encoding="utf-8")
IMPL = (APP / "db/impl.sql").read_text(encoding="utf-8")


def parse_schema():
    """{table: {"cols": [(name, type, nullable)], "fks": [(col, ref_table, nullable, unique)], "pk": [cols]}}"""
    tables = {}
    for name, body in re.findall(r"CREATE TABLE (\w+) \((.*?)\n\);", SCHEMA + IMPL, re.S):
        cols, fks, pk = [], [], []
        lines = [ln.strip().rstrip(",") for ln in body.split("\n") if ln.strip()]
        merged = []
        for ln in lines:                       # «REFERENCES …» на окремому рядку належить попередньому стовпцю
            if ln.startswith("REFERENCES") and merged:
                merged[-1] += " " + ln
            else:
                merged.append(ln)
        for ln in merged:
            if ln.startswith(("CHECK", "UNIQUE")):
                continue
            if ln.startswith("PRIMARY KEY"):
                pk += [c.strip() for c in re.search(r"\((.*?)\)", ln).group(1).split(",")]
                continue
            m = re.match(r"(\w+) ([A-Za-z_]+(?:\(\d+(?:,\d+)?\))?)", ln)
            if not m:
                continue
            col, typ = m.groups()
            nullable = "NOT NULL" not in ln and "PRIMARY KEY" not in ln
            cols.append((col, typ, nullable))
            if "PRIMARY KEY" in ln:
                pk.append(col)
            ref = re.search(r"REFERENCES (\w+)", ln)
            if ref:
                fks.append((col, ref.group(1), nullable, " UNIQUE" in ln))
        tables[name] = {"cols": cols, "fks": fks, "pk": pk}
    return tables


def table_comments():
    return dict(re.findall(r"COMMENT ON TABLE (\w+) IS '([^:']+):", SCHEMA))


def mission_transitions():
    block = re.search(r"INSERT INTO mission_transition VALUES(.*?);", IMPL, re.S).group(1)
    return re.findall(r"\('([^']+)', '([^']+)', '([^']+)'\)", block)


TABLES = parse_schema()
TNAME = table_comments()
TNAME.update(mission_transition="Перехід стану місії", sensor_transition="Перехід стану сенсора")


def cls_name(t):
    """«Об’єкт прикриття» → «Об’єктПрикриття» (UpperCamelCase без зміни літер усередині слів)."""
    return "".join(w[:1].upper() + w[1:] for w in TNAME[t].split())


# ------------------------------------------------------------------ рендеринг
# корисна площа сторінки за методичними вказівками (поля 30/10/20/20 мм): книжкова 17,0 × 25,7 см, альбомна
# 25,7 × 17,0 см; під підпис рисунка лишаємо ≈ 2,5 см
PAGE = {"portrait": (17.0, 23.0), "landscape": (25.7, 14.8)}


def relayout(lay_path):
    """Перерахувати ширину і кегль рисунка під реальну геометрію сторінки (інструменти рахують для 16,5 см)."""
    lay = json.loads(lay_path.read_text())
    w_px, h_px = lay["native_px"]
    for o, (bw, bh) in PAGE.items():
        if o not in lay:
            continue
        old_w, old_pt = lay[o]["width_cm"], lay[o]["font_pt"]
        new_w = min(bw, bh * w_px / h_px, old_w * 13.0 / old_pt if old_pt else bw)
        lay[o].update(width_cm=round(new_w, 2), font_pt=round(old_pt * new_w / old_w, 1),
                      main_pt=round(lay[o].get("main_pt", old_pt) * new_w / old_w, 1))
    best = next((o for o in ("portrait", "landscape") if o in lay and lay[o]["font_pt"] >= 10), None) or \
        max((o for o in ("portrait", "landscape") if o in lay), key=lambda o: lay[o]["font_pt"])
    lay.update(orientation=best, width_cm=lay[best]["width_cm"], legible=lay[best]["font_pt"] >= 10)
    lay_path.write_text(json.dumps(lay, ensure_ascii=False, indent=2))
    return lay


def report(name, lay):
    print(f"{name}: {lay['orientation']} {lay[lay['orientation']]['font_pt']} pt, {lay['width_cm']} см" +
          ("" if lay["legible"] else "  !!! НЕЧИТАБЕЛЬНО"))
    return lay["legible"]


def mmd(name, body):
    p = DIAG / f"{name}.mmd"
    p.write_text(body, encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "tools/mmd_render.py"), str(p)], capture_output=True, text=True)
    return report(name, relayout(p.with_suffix(".layout.json")))


def puml(name, body):
    p = DIAG / f"{name}.puml"
    p.write_text(body, encoding="utf-8")
    r = subprocess.run([sys.executable, str(ROOT / "tools/puml_render.py"), str(p)], capture_output=True, text=True)
    if not p.with_suffix(".layout.json").exists():
        print(r.stdout, r.stderr)
        return False
    return report(name, relayout(p.with_suffix(".layout.json")))


def idef(name, spec):
    render(spec, DIAG / name)
    return report(name, relayout((DIAG / name).with_suffix(".layout.json")))


# ------------------------------------------------------------------ розділ 1
INTERACTION = {"kind": "flowchart", "colw": 228, "rowh": 70, "bw": 200, "nodes": [
    {"id": "RECON", "kind": "proc", "col": 0, "row": 0, "text": "Відділ розвідки повітряного простору"},
    {"id": "IT", "kind": "proc", "col": 0, "row": 1, "text": "Служба зв’язку та ІТ"},
    {"id": "TECH", "kind": "proc", "col": 0, "row": 2, "text": "Технічна служба"},
    {"id": "LOG", "kind": "proc", "col": 0, "row": 3, "text": "Служба логістики"},
    {"id": "TRN", "kind": "proc", "col": 0, "row": 4, "text": "Навчально-тренувальний відділ"},
    {"id": "COOP", "kind": "proc", "col": 0, "row": 5, "text": "Сектор взаємодії (ПС ЗСУ, суміжні центри)"},
    {"id": "KP", "kind": "proc", "col": 1, "row": 2.5, "text": "Командний пункт (оперативний черговий центр)"},
    {"id": "INT", "kind": "proc", "col": 2, "row": 1.5, "text": "Підрозділ дронів-перехоплювачів"},
    {"id": "ANL", "kind": "proc", "col": 2, "row": 3.5, "text": "Відділ аналітики, планування та звітності"}],
  "edges": [(u, "KP", {"exit": "r", "enter": "l", "via": [(0.5, r), (0.5, 2.5)]}) for u, r in
            (("RECON", 0), ("IT", 1), ("TECH", 2), ("LOG", 3), ("TRN", 4), ("COOP", 5))] +
           [("KP", "INT", {"exit": "r", "enter": "l", "via": [(1.5, 2.35), (1.5, 1.5)]}),
            ("INT", "KP", {"exit": "b", "enter": "r", "via": [(2, 2.5)]}),
            ("KP", "ANL", {"exit": "r", "enter": "l", "via": [(1.5, 2.65), (1.5, 3.5)]})]}


def section1():
    shutil.copy(ROOT / "lab1/diagrams/01_org_structure.mmd", DIAG / "01_org_structure.mmd")
    ok = mmd("01_org_structure", (DIAG / "01_org_structure.mmd").read_text(encoding="utf-8"))
    ok &= idef("02_interaction", INTERACTION)
    ok &= idef("04_goal_tree", L1.GOAL_TREE)              # те саме дерево, що й у ЛР1 (один аркуш)
    wbs = {"kind": "goaltree", "cols": (128, 178, 0), "sep1": " ", "split": 2, "root": L1.PROJECT,
           "goals": [(sp[0], sp[1], [(bc, bn, []) for bc, bn, _ws in sp[3]]) for sp in L1.WBS]}
    ok &= idef("05_wbs", wbs)                                  # WBS: рівні 1–3 (пакети — у таблиці записки)
    return ok


# ------------------------------------------------------------------ розділ 2: BPMN (ЛР2) і UML
BPMN = ["00_interaction_map", "01_p1_monitoring", "02_p2_assignment_a", "03_p2_assignment_b", "04_p3_mission_a",
        "05_p3_mission_b", "06_p4_assessment", "07_p5_readiness"]


def bpmn():
    ok = True
    for n in BPMN:
        src = ROOT / f"lab2/diagrams/{n}.bpmn"
        dst = DIAG / f"bpmn_{n}.bpmn"
        # назви доріжок висотою в один ряд переносяться на два рядки, щоб не виходити за межі доріжки
        dst.write_text(src.read_text(encoding="utf-8").replace('name="Офіцер взаємодії"', 'name="Офіцер&#10;взаємодії"')
,
                       encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "tools/bpmn_model.py"), str(dst)], capture_output=True, text=True)
        ok &= report(f"bpmn_{n}", relayout(dst.with_suffix(".layout.json")))
    return ok


ACTIVITY = """@startuml
skinparam conditionStyle diamond
|ОБУ|
start
:Обрати
розрахунок;
|БД|
:fn_propose_mission;
|ОЧ|
if (пуск?) then ([так])
  :Санкціо-
  нувати;
else ([ні])
  :Відхи-
  лити;
endif
|БД|
:trg_mission_guard,
CHECK;
if (відхилено?) then ([так])
  stop
endif
|Командир|
while (відмова?) is ([так])
  |ОЧ|
  :Перепризначити;
  :Санкціонує інший ОЧ;
  |БД|
  :trg_mission_guard;
  |Командир|
endwhile ([ні])
:Прийняти,
здійснити пуск;
if (скасувати?) then ([так])
  :Скасувати
  (або ОЧ, ОБУ);
  stop
else ([ні])
  :Доповісти
  результат;
  stop
endif
@enduml
"""

SEQUENCE = """@startuml
hide footbox
actor "ОБУ" as FCO
actor "ОЧ" as OC
participant "Flask-застосунок" as APP
database "PostgreSQL" as DB
FCO -> APP : GET /tracks/{id}
activate APP
APP -> DB : set_config('app.user_id')
APP -> DB : fn_crew_candidates()
DB --> APP : кандидати
APP --> FCO : сторінка з кандидатами
deactivate APP
FCO -> APP : POST /tracks/{id}
activate APP
APP -> DB : set_config('app.user_id')
APP -> DB : fn_propose_mission()
note right of DB : trg_mission_after, trg_audit
APP --> FCO : 302 /missions/{id}
deactivate APP
OC -> APP : POST /missions/{id}
activate APP
APP -> DB : set_config('app.user_id')
APP -> DB : UPDATE mission
note right of DB : trg_mission_guard
alt дозволено
  APP -> DB : COMMIT
  APP --> OC : стан оновлено
else відмова
  DB --> APP : помилка тригера
  APP -> DB : ROLLBACK
  APP --> OC : причина відмови
end
deactivate APP
@enduml
"""

# основні атрибути для діаграм класів і операції (функції БД, що обробляють сутність)
CLASS_ATTRS = {
    "sector": ["code", "name", "zone_type"],
    "protected_object": ["name", "category", "lat", "lon"],
    "sensor": ["hw_serial", "kind", "status", "last_heartbeat_at"],
    "detection": ["detected_at", "confidence", "lat", "lon", "speed_mps"],
    "air_track": ["track_number", "state", "identity", "threat_score", "eta_s"],
    "mission": ["mission_no", "state", "proposed_at", "approved_at", "abort_reason"],
    "mission_event": ["event_type", "event_at", "payload"],
    "telemetry_frame": ["ts", "lat", "lon", "battery_pct"],
    "engagement_report": ["assessment", "submitted_at"],
    "position": ["code", "status", "engagement_radius_m"],
    "crew": ["call_sign", "status"],
    "interceptor": ["serial_no", "state", "flight_count"],
    "interceptor_model": ["name", "range_km", "reusable"],
    "personnel": ["login", "full_name", "status", "failed_logins"],
    "role": ["code", "name", "combat_rights"],
    "permission": ["code", "description"],
    "audit_log": ["logged_at", "action", "prev_hash", "hash"],
}
CLASS_OPS = {
    "sensor": ["trg_sensor_guard()"],
    "detection": ["fn_ingest_detection()"],
    "air_track": ["fn_classify_track()", "fn_eval_threat()", "fn_crew_candidates()"],
    "mission": ["fn_propose_mission()", "trg_mission_guard()", "trg_mission_after()"],
    "engagement_report": ["trg_report_after()"],
    "personnel": ["fn_has_perm()"],
    "audit_log": ["fn_audit_verify()"],
}
CLASS_ATTRS_ALL = {"protected_object": ["name", "category"], "sensor": ["hw_serial", "kind", "status"],
                   "detection": ["detected_at", "confidence"],
                   "air_track": ["track_number", "state", "identity", "threat_score"],
                   "mission": ["mission_no", "state", "approved_at"], "mission_event": ["event_type"],
                   "engagement_report": ["assessment"], "crew": ["call_sign", "status"], "position": ["code"],
                   "interceptor": ["serial_no", "state"], "personnel": ["login", "status"], "role": ["code"]}
CLASS_OPS_ALL = {"sensor": ["trg_sensor_guard()"], "detection": ["fn_ingest_detection()"],
                 "air_track": ["fn_classify_track()"], "mission": ["fn_propose_mission()", "trg_mission_guard()"],
                 "engagement_report": ["trg_report_after()"], "personnel": ["fn_has_perm()"]}
CLASS_ALL = ["protected_object", "sensor", "detection", "air_track", "mission", "mission_event",
             "engagement_report", "crew", "interceptor", "personnel"]
FRAG = {
    "class_ops": ["sector", "protected_object", "sensor", "detection", "air_track", "mission", "mission_event",
                  "telemetry_frame", "engagement_report"],
    "class_res": ["mission", "position", "crew", "interceptor", "interceptor_model", "personnel", "role",
                  "permission", "audit_log"],
}
COMPOSITION = {("mission_event", "mission"), ("telemetry_frame", "mission")}


FK_ROLE = {"proposed_by": "запропонував", "approved_by": "санкціонував", "classified_by": "класифікував",
           "submitted_by": "доповів", "predicted_object_id": "під загрозою"}


FK_HIDDEN = {("air_track", "classified_by"), ("mission_event", "actor_id"), ("engagement_report", "submitted_by")}


def associations(tables):
    """Асоціації діаграми класів з зовнішніх ключів: (батьківська, дочірня, кратність біля батьківської,
    кратність біля дочірньої, підпис, композиція). Кратність біля батьківської — обов’язковість FK (1 / 0..1),
    біля дочірньої — «*», а для унікального FK — «0..1» (1 : 0..1). Кожен FK — окрема асоціація; якщо до тієї
    самої таблиці веде кілька FK, кожна підписується роллю (FK_ROLE)."""
    shown, out = set(tables), []
    for t in tables:
        fks = [f for f in TABLES[t]["fks"] if f[1] in shown and (t, f[0]) not in FK_HIDDEN]
        for col, ref, nullable, unique in fks:
            many = sum(1 for f in fks if f[1] == ref) > 1
            label = FK_ROLE.get(col, "") if (many or col in FK_ROLE) else ""
            out.append((ref, t, "0..1" if nullable else "1", "0..1" if unique else "*", label,
                        (t, ref) in COMPOSITION))
    return out


def class_diagram(tables, attrs=None, ops=None):
    attrs, ops = attrs or CLASS_ATTRS, ops if ops is not None else CLASS_OPS
    lines = ["@startuml", "skinparam classAttributeIconSize 0", "hide circle", "skinparam nodesep 14",
             "skinparam ranksep 34"]
    for t in tables:
        types = {c: typ for c, typ, _ in TABLES[t]["cols"]}
        lines.append(f'class {t} as "{cls_name(t)}" {{')
        for a in attrs[t]:
            lines.append(f"  {{field}} {a} : {types[a].lower()}")
        if t in ops:
            lines.append("  --")
            lines += [f"  {{method}} {o}" for o in ops[t]]
        lines.append("}")
    for ref, t, m1, m2, label, comp in associations(tables):
        lines.append(f'{ref} "{m1}" {"*--" if comp else "--"} "{m2}" {t}' + (f" : {label}" if label else ""))
    if "role" in tables and "permission" in tables:   # асоціативна таблиця role_permission
        lines.append('role "*" -- "*" permission : role_permission')
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def state_diagram():
    names = {}
    lines = ["@startuml", "hide empty description"]
    for frm, to, _ in mission_transitions():
        for s in (frm, to):
            names.setdefault(s, f"S{len(names)}")
    for s, sid in names.items():
        lines.append(f'state "{s}" as {sid}')
    lines.append(f"[*] --> {names['запропонована']} : fn_propose_mission")
    for frm, to, perm in mission_transitions():
        lines.append(f"{names[frm]} --> {names[to]} : {perm}")
    for end in ("відхилена", "скасована", "закрита"):
        lines.append(f"{names[end]} --> [*]")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def section2():
    ok = bpmn()
    ok &= idef("20_uc_combat", M.UC_COMBAT)
    ok &= idef("21_uc_support", M.UC_SUPPORT)
    ok &= puml("22_activity", ACTIVITY)
    ok &= puml("23_sequence", SEQUENCE)
    ok &= puml("24_class_all", class_diagram(CLASS_ALL, CLASS_ATTRS_ALL, CLASS_OPS_ALL))
    ok &= puml("26_state_mission", state_diagram())
    return ok


# ------------------------------------------------------------------ розділ 3
COMPONENTS = {
    "kind": "columns", "colw": 168, "bw": 128, "rh": 78, "gap": 18,
    "columns": [
        {"title": "Рівень користувача", "layer": "HTTPS", "items": [
            {"id": "ARM", "name": "АРМ КП (браузер)", "row": 0},
            {"id": "TAB", "name": "Застосунок розрахунку", "row": 1},
            {"id": "ADM", "name": "Консоль адміністратора", "row": 2}]},
        {"title": "Периферійний рівень", "layer": "REST", "items": [
            {"id": "EDGE", "name": "Брокер MQTT, адаптери, буфер", "row": 3}]},
        {"title": "Оброблення: ядро в ЦОД", "layer": "застосунки", "items": [
            {"id": "INT", "name": "Шлюз інтеграції із зовнішніми системами", "row": 0},
            {"id": "WEB", "name": "Веб-застосунок і REST API (прототип)", "row": 1, "span": 1.4, "bold": True,
             "fill": "#E6E6E6"},
            {"id": "MIS", "name": "Сервіс місій і правил", "row": 2.6},
            {"id": "FUS", "name": "Сервіс злиття треків", "row": 3.6}]},
        {"title": "Зберігання", "layer": "дані (SQL)", "items": [
            {"id": "PG", "name": "PostgreSQL: функції, тригери (прототип)", "row": 1, "span": 1.4, "bold": True,
             "fill": "#E6E6E6"},
            {"id": "TS", "name": "Сховище телеметрії", "row": 3.6}]},
    ],
    "links": [("ARM", "WEB", {"ty": -28}), ("TAB", "WEB"), ("ADM", "WEB", {"ty": 22}),
              ("EDGE", "WEB", {"ty": 40}), ("INT", "WEB"), ("WEB", "PG"),
              ("MIS", "PG", {"ty": 22}), ("FUS", "PG", {"ty": 40, "mx": 18}), ("FUS", "TS")],
}

DEPLOYMENT = """@startuml
left to right direction
node "Сенсори" as SEN
node "Дрон" as UAV
node "Позиція (× 9)" as POS {
  node "НСУ" as GCS
  node "Шлюз" as GW
  node "Планшет" as TAB
}
node "АРМ КП" as WS
node "Основний ЦОД" as DC1 {
  artifact "Flask (WSGI)" as A1
  database "PostgreSQL 18" as D1
}
node "Резервний ЦОД" as DC2 {
  database "Репліка PostgreSQL" as D2
}
SEN --> GW : MQTT/TLS, ASTERIX
GCS <-left-> UAV : MAVLink 2
GCS <--> GW : телеметрія, команди
GW <--> A1 : HTTPS, VPN
TAB --> A1 : HTTPS, VPN
WS --> A1 : HTTPS
A1 --> D1 : SQL/TLS
D1 -right-> D2 : реплікація
@enduml
"""

NETWORK = {"kind": "flowchart", "colw": 168, "rowh": 96, "bw": 146, "nodes": [
    {"id": "SEN", "kind": "proc", "col": 0, "row": 0.25, "text": "Акустичні вузли (LoRaWAN, LTE-M)"},
    {"id": "RAD", "kind": "proc", "col": 0, "row": 1.5, "text": "РЛС, оптико-електронні пости"},
    {"id": "TAB", "kind": "proc", "col": 1, "row": 0.25, "text": "Планшет розрахунку"},
    {"id": "GW", "kind": "proc", "col": 1, "row": 1.5, "text": "Периферійний шлюз"},
    {"id": "ARM", "kind": "proc", "col": 2, "row": 0.25, "text": "АРМ КП (ЛОМ КП)"},
    {"id": "VPN", "kind": "proc", "col": 2, "row": 1.5, "text": "Тунель WireGuard: меш-радіо, LTE, супутник"},
    {"id": "FW", "kind": "proc", "col": 3, "row": 1.5, "text": "Міжмережевий екран, проксі TLS"},
    {"id": "APP", "kind": "proc", "col": 3, "row": 2.6, "text": "Сервер застосунку"},
    {"id": "DB", "kind": "db", "col": 3, "row": 3.65, "text": "Сервер БД"}],
  "edges": [("SEN", "GW", {"exit": "r", "enter": "l", "via": [(0.5, 0.25), (0.5, 1.5)]}),
            ("RAD", "GW", {"exit": "r", "enter": "l"}),
            ("TAB", "GW", {"exit": "b", "enter": "t", "label": "Wi-Fi"}),
            ("GW", "VPN", {"exit": "r", "enter": "l"}), ("VPN", "FW", {"exit": "r", "enter": "l"}),
            ("ARM", "FW", {"exit": "r", "enter": "t", "via": [(3, 0.25)], "label": "HTTPS"}),
            ("FW", "APP", {"exit": "b", "enter": "t"}), ("APP", "DB", {"exit": "b", "enter": "t", "label": "SQL/TLS"})],
  "groups": [{"title": "Сенсори", "c0": 0, "r0": -0.12, "c1": 1, "r1": 2.62},
             {"title": "ЛОМ позиції", "c0": 1, "r0": -0.12, "c1": 2, "r1": 2.62},
             {"title": "Мережа ЦОД", "c0": 3, "r0": 1.0, "c1": 4, "r1": 4.45}]}

INTERACT = """@startuml
skinparam componentStyle rectangle
actor "Користувач" as U
component "Шлюз (імітатор)" as GW
package "app.py" {
  [Сеанс, CSRF; need()] as AUTH
  [Обробники сторінок] as VIEWS
  [REST API] as API
}
package "PostgreSQL" {
  [Функції PL/pgSQL] as FN
  [Тригери] as TRG
  [Представлення] as VW
  database "Таблиці" as T
}
U --> AUTH : 1 HTTPS
AUTH --> VIEWS : 2
VIEWS --> FN : 3 виклик
FN --> T
TRG --> T : 4 перевірка, аудит
VIEWS --> VW : 5 вибірка
GW --> API : 6 POST
API --> FN : 7
@enduml
"""


def section3():
    ok = True
    for n in ("01_architecture", "02_flows"):
        for ext in (".png", ".layout.json"):
            shutil.copy(ROOT / f"lab7/diagrams/{n}{ext}", DIAG / f"lab7_{n}{ext}")
        ok &= report(f"lab7_{n}", relayout(DIAG / f"lab7_{n}.layout.json"))
    ok &= idef("31_components", COMPONENTS)
    ok &= puml("32_deployment", DEPLOYMENT)
    ok &= idef("33_network", NETWORK)
    ok &= puml("34_interaction", INTERACT)
    return ok


# ------------------------------------------------------------------ розділ 4: карта навігації з маршрутів Flask
# (кінцева точка, підпис, звідки переходять); ролі обчислюються з матриці прав seed.ROLES
NAV_NODES = [
    ("login", "Вхід до системи", None), ("index", "Головна сторінка", "login"), ("search", "Пошук", "index"),
    ("situation", "Обстановка<br/>(мнемосхема, черга загроз)", "index"), ("track", "Картка треку", "situation"),
    ("detection_new", "Ручне донесення", "situation"), ("missions", "Місії (фільтри)", "index"),
    ("mission", "Картка місії", "missions"), ("resources", "Ресурси", "index"),
    ("interceptor_form", "Форма перехоплювача", "resources"), ("sensors", "Сенсори", "index"),
    ("sensor_form", "Форма сенсора", "sensors"), ("objects", "Об’єкти прикриття", "index"),
    ("object_form", "Форма об’єкта", "objects"), ("analytics", "Аналітика", "index"),
    ("users", "Користувачі", "index"), ("user_form", "Форма облікового запису", "users"),
    ("roles", "Ролі та права", "index"), ("audit", "Журнал аудиту", "index"),
]
ENDPOINT_PERMS = {  # права, з якими відкривається сторінка (функція need() у app.py)
    "situation": ("track.read",), "track": ("track.read",), "detection_new": ("detection.write",),
    "missions": ("mission.read",), "mission": ("mission.read",), "resources": ("resource.read",),
    "interceptor_form": ("interceptor.manage",), "sensors": ("sensor.manage",), "sensor_form": ("sensor.manage",),
    "objects": ("sector.manage",), "object_form": ("sector.manage",), "analytics": ("analytics.read",),
    "users": ("user.manage", "user.block"), "user_form": ("user.manage",), "roles": ("role.manage",),
    "audit": ("audit.read",),
}


def roles_for(ep):
    import seed
    if ep not in ENDPOINT_PERMS:
        return "усі ролі"
    codes = [c for c, _n, _b, perms in seed.ROLES if set(perms.split()) & set(ENDPOINT_PERMS[ep])]
    nums = [int(c[2:]) for c in codes]
    out, i = [], 0
    while i < len(nums):                       # послідовні коди стискаються: R-01…R-05
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(f"R-{nums[i]:02d}" if j - i < 2 else f"R-{nums[i]:02d}…R-{nums[j]:02d}")
        if 0 < j - i < 2:
            out += [f"R-{n:02d}" for n in nums[i + 1:j + 1]]
        i = j + 1
    return ", ".join(out)


NAV_GRID = {"login": (0, 2.5), "index": (0, 4.5), "search": (1, 10), "detection_new": (2, 0), "situation": (1, 1),
            "track": (2, 1), "missions": (1, 2), "mission": (2, 2), "resources": (1, 3), "interceptor_form": (2, 3),
            "sensors": (1, 4), "sensor_form": (2, 4), "objects": (1, 5), "object_form": (2, 5),
            "analytics": (1, 6), "users": (1, 7), "user_form": (2, 7), "roles": (1, 8), "audit": (1, 9)}


def navmap():
    nodes, edges = [], []
    for ep, label, frm in NAV_NODES:
        c, r = NAV_GRID[ep]
        nodes.append({"id": ep, "kind": "term" if ep == "login" else "proc", "col": c, "row": r,
                      "text": f"{label.replace('<br/>', ' ')} ({roles_for(ep)})"})
        if not frm:
            continue
        fc, fr = NAV_GRID[frm]
        if frm == "login":
            edges.append((frm, ep, {"exit": "b", "enter": "t"}))
        elif fr == r:
            edges.append((frm, ep, {"exit": "r", "enter": "l"}))
        else:
            edges.append((frm, ep, {"exit": "r", "enter": "l", "via": [(fc + 0.5, fr), (fc + 0.5, r)]}))
    edges.append(("track", "mission", {"exit": "b", "enter": "t"}))
    return {"kind": "flowchart", "colw": 228, "rowh": 72, "bw": 204, "nodes": nodes, "edges": edges}


def section4():
    return idef("40_navmap", navmap())


if __name__ == "__main__":
    DIAG.mkdir(exist_ok=True)
    parts = sys.argv[1:] or ["1", "2", "3", "4"]
    ok = True
    for part in parts:
        ok &= {"1": section1, "2": section2, "3": section3, "4": section4}[part]()
    sys.exit(0 if ok else 3)
