#!/usr/bin/env python3
"""Перевірка відповідності діаграм і таблиць пояснювальної записки коду прототипу.

  1) діаграми класів: кожен клас — таблиця schema.sql, кожен атрибут — стовпець з тим самим типом, кожна асоціація —
     зовнішній ключ, кожна операція — функція з impl.sql;
  2) діаграма станів місії = таблиця mission_transition;
  3) прецеденти: право існує в матриці seed.ROLES, кінцева точка — у маршрутах Flask, ролі акторів мають право;
  4) карта навігації: кожна сторінка — маршрут Flask, ролі = ролі з правом відкрити сторінку;
  5) діаграма послідовності: усі згадані функції/тригери існують у impl.sql, маршрути — у Flask.

    .venv/bin/python coursework_final/model/consistency.py      (код повернення 0 — розбіжностей немає)
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CW = HERE.parent
sys.path[:0] = [str(HERE), str(CW / "app"), str(CW / "app/db")]
import cw_model as M  # noqa: E402
import make_diagrams as D  # noqa: E402
import seed  # noqa: E402

IMPL = (CW / "app/db/impl.sql").read_text(encoding="utf-8")
FUNCS = set(re.findall(r"CREATE FUNCTION (\w+)", IMPL))
PERMS = {code: set(p.split()) for code, _n, _c, p in seed.ROLES}
ALL_PERMS = set(seed.PERMS)


def routes():
    import app as webapp
    return {r.endpoint: r.rule for r in webapp.app.url_map.iter_rules()}


def check():
    errors, checks = [], 0
    R = routes()
    # 1) діаграми класів
    for frag in ("24_class_all",):
        text = (CW / f"diagrams/{frag}.puml").read_text(encoding="utf-8")
        for t, body in re.findall(r'class (\w+) as "[^"]+" \{(.*?)\n\}', text, re.S):
            checks += 1
            if t not in D.TABLES:
                errors.append(f"{frag}: клас {t} не є таблицею БД")
                continue
            types = {c: typ.lower() for c, typ, _ in D.TABLES[t]["cols"]}
            for a, typ in re.findall(r"\{field\} (\w+) : (\S+)", body):
                checks += 1
                if types.get(a) != typ:
                    errors.append(f"{frag}: {t}.{a} : {typ} ≠ схемі ({types.get(a)})")
            for op in re.findall(r"\{method\} (\w+)\(\)", body):
                checks += 1
                if op not in FUNCS:
                    errors.append(f"{frag}: операція {op} відсутня в impl.sql")
        # асоціації: кожна має відповідний FK з тією самою кратністю (1/0..1 — обов’язковість, 0..1 — UNIQUE)
        fk = {}
        for t in D.TABLES:
            for col, ref, nullable, unique in D.TABLES[t]["fks"]:
                fk.setdefault((ref, t), []).append(("0..1" if nullable else "1", "0..1" if unique else "*",
                                                     D.FK_ROLE.get(col, "")))
        for a, m1, m2, b, lab in re.findall(r'^(\w+) "([^"]+)" [-*]+ "([^"]+)" (\w+)(?: : (.+))?$', text, re.M):
            checks += 1
            if {a, b} == {"role", "permission"}:
                continue
            opts = fk.get((a, b), [])
            if not any(o[0] == m1 and o[1] == m2 and (not lab or o[2] == lab) for o in opts):
                errors.append(f"{frag}: асоціація {a} «{m1}» — «{m2}» {b} {lab} не відповідає FK {opts}")
    # 2) діаграма станів
    st = (CW / "diagrams/26_state_mission.puml").read_text(encoding="utf-8")
    ids = dict((sid, name) for name, sid in re.findall(r'state "([^"]+)" as (\w+)', st))
    drawn = {(ids[a], ids[b], p) for a, b, p in re.findall(r"^(S\d+) --> (S\d+) : (\S+)", st, re.M)}
    checks += 1
    if drawn != set(D.mission_transitions()):
        errors.append(f"діаграма станів ≠ mission_transition: {drawn ^ set(D.mission_transitions())}")
    # 3) прецеденти
    for spec in (M.UC_COMBAT, M.UC_SUPPORT):
        for u in spec["usecases"]:
            name, perm, ep = M.UC[u["id"]]
            checks += 1
            if ep not in R:
                errors.append(f"{u['id']} «{name}»: кінцевої точки {ep} немає у Flask")
            if perm and perm not in ALL_PERMS:
                errors.append(f"{u['id']}: права {perm} немає в матриці")
        for actor, uc in spec["assoc"]:
            perm = M.UC[uc][1]
            role = M.ACTOR_ROLE.get(actor)
            checks += 1
            if role and perm and perm not in PERMS[role]:
                errors.append(f"актор {actor} ({role}) пов’язаний з {uc}, але не має права {perm}")
            if actor == "KP":                                    # абстрактний актор: усі нащадки мають право
                for child, par in spec.get("generalize", []):
                    if par == "KP" and perm not in PERMS[M.ACTOR_ROLE[child]]:
                        errors.append(f"нащадок {child} актора KP не має права {perm}")
    # 4) карта навігації
    for ep, _label, _frm in D.NAV_NODES:
        checks += 1
        if ep not in R:
            errors.append(f"карта навігації: сторінки {ep} немає у Flask")
    src = (CW / "app/app.py").read_text(encoding="utf-8")
    for ep, perms in D.ENDPOINT_PERMS.items():
        checks += 1
        body = re.search(rf"def {ep}\(.*?\n(?=@app|\Z|def )", src, re.S)
        found = set(re.findall(r'need\(([^)]*)\)', body.group(0))[0].replace('"', "").replace(" ", "").split(","))
        if found != set(perms):
            errors.append(f"карта навігації: {ep} — права {perms}, у коді {found}")
    # 5) діаграма послідовності / діяльності
    for name in ("23_sequence", "22_activity"):
        text = (CW / f"diagrams/{name}.puml").read_text(encoding="utf-8")
        for fn in set(re.findall(r"\b((?:fn|trg)_\w+)", text)):
            checks += 1
            if fn not in FUNCS:
                errors.append(f"{name}: {fn} відсутня в impl.sql")
        for rule in set(re.findall(r"(?:GET|POST) (/[\w/{}]+)", text)):
            checks += 1
            flask_rule = re.sub(r"\{id\}", "<", rule)
            if not any(r.startswith(flask_rule.split("<")[0]) for r in R.values()):
                errors.append(f"{name}: маршруту {rule} немає у Flask")
    # 6) покриття вимог: усі FR з ТСПП ПР1 мають оцінку
    sys.path.insert(0, str(CW.parent / "tspp_work/pract1"))
    import model_p1
    checks += 1
    if {f[0] for f in model_p1.FR} != set(M.FR_COVERAGE):
        errors.append("FR_COVERAGE не збігається з переліком FR")
    return checks, errors


if __name__ == "__main__":
    n, errs = check()
    for e in errs:
        print("РОЗБІЖНІСТЬ:", e)
    print(f"перевірок: {n}, розбіжностей: {len(errs)}")
    sys.exit(1 if errs else 0)
