"""Генератори артефактів ЛР1 з model_l1: SQL DDL, ER-діаграми (PlantUML), контекстна діаграма (Mermaid)."""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import model_l1 as M


def flags(c):
    """Прапорці через пробіл; значення DEF:'…' може містити пробіли (лапки зберігаються)."""
    return re.findall(r"DEF:'[^']*'|\S+", c[2])


def fk_of(c):
    return next((f[3:] for f in flags(c) if f.startswith("FK:")), None)


def default_of(c):
    return next((f[4:] for f in flags(c) if f.startswith("DEF:")), None)


def pk_cols(t):
    return t["pk"] or [c[0] for c in t["cols"] if "PK" in flags(c)]


def is_nn(t, c):
    return "NN" in flags(c) or c[0] in pk_cols(t)


def is_unique(t, c):
    return "U" in flags(c) or (pk_cols(t) == [c[0]])


def fks(t):
    return [(c, fk_of(c)) for c in t["cols"] if fk_of(c)]


def parent_pk(name):
    return pk_cols(M.TABLES[name])[0]


def ordered_tables():
    """Топологічне впорядкування: батьківські таблиці створюються раніше дочірніх."""
    done, out = set(), []

    def visit(n):
        if n in done:
            return
        done.add(n)
        for _, p in fks(M.TABLES[n]):
            if p != n:
                visit(p)
        out.append(n)

    for t in M.T:
        visit(t["name"])
    return out


def constraints_text(t, c):
    """Обмеження стовпця для таблиці опису полів."""
    out = []
    if c[0] in pk_cols(t):
        out.append("PK" if len(pk_cols(t)) == 1 else "PK (складений)")
    if fk_of(c):
        out.append(f"FK → {fk_of(c)}")
    if "U" in flags(c):
        out.append("UNIQUE")
    out.append("NOT NULL" if is_nn(t, c) else "NULL")
    if default_of(c):
        out.append(f"DEFAULT {default_of(c)}")
    if c[0] in pk_cols(t) and len(pk_cols(t)) == 1 and not fk_of(c):
        out.append("gen_random_uuid()" if c[1] == "UUID" else "IDENTITY")
    return ", ".join(out)


# ============================================================================================ SQL DDL
def sql():
    L = ["-- Схема бази даних IoT-платформи «Щит-Лінк» (ЛР1, фізична модель).",
         "-- Згенеровано з tspp_work/lab1/model_l1.py; не редагувати вручну.", "",
         "CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid() для версій до 13", ""]
    for e, vals in M.ENUMS.items():
        L.append(f"CREATE TYPE {e} AS ENUM (\n" + ",\n".join(f"    '{v}'" for v in vals) + "\n);")
    L.append("")
    for n in ordered_tables():
        t = M.TABLES[n]
        pk = pk_cols(t)
        body = []
        for c in t["cols"]:
            s = f"    {c[0]} {c[1]}"
            if len(pk) == 1 and c[0] == pk[0]:
                if c[1] == "UUID":
                    s += " PRIMARY KEY DEFAULT gen_random_uuid()"
                else:
                    s += " GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
            else:
                if is_nn(t, c):
                    s += " NOT NULL"
                if default_of(c):
                    s += f" DEFAULT {default_of(c)}"
                if "U" in flags(c):
                    s += " UNIQUE"
                if fk_of(c):
                    s += f"\n        REFERENCES {fk_of(c)} ({parent_pk(fk_of(c))})"
            body.append(s)
        if len(pk) > 1:
            body.append(f"    PRIMARY KEY ({', '.join(pk)})")
        for u in t["uniques"]:
            body.append(f"    UNIQUE ({', '.join(u)})")
        for k in t["checks"]:
            body.append(f"    CHECK ({k})")
        L.append(f"CREATE TABLE {n} (\n" + ",\n".join(body) + "\n);\n")
    for ix, tb, cols, _ in M.INDEXES:
        w = f" WHERE {M.PARTIAL[ix]}" if ix in M.PARTIAL else ""
        L.append(f"CREATE INDEX {ix} ON {tb} ({cols}){w};")
    L.append("")
    for t in M.T:
        L.append(f"COMMENT ON TABLE {t['name']} IS '{t['ua']}: {t['purpose']}';")
    return "\n".join(L) + "\n"


# ============================================================================================ PlantUML ER
HEAD = "@startuml\nhide circle\nhide methods\nskinparam linetype ortho\n"


def _rel(child, c, parent, *, logical):
    pc = "||" if "NN" in flags(c) or "PK" in flags(c) else "|o"
    cc = "o|" if "U" in flags(c) else "o{"
    lab = f" : {M.REL[(child, c[0])]}" if logical else ""
    return f"{parent} {pc}--{cc} {child}{lab}"


def er(group, logical, direction="top to bottom", hidden=()):
    """ER-діаграма групи; таблиці інших груп, на які є посилання, показано скорочено (лише ключ)."""
    own = [t for t in M.T if t["group"] == group]
    names = {t["name"] for t in own}
    stubs = []
    for t in own:
        for _, p in fks(t):
            if p not in names and p not in stubs:
                stubs.append(p)
    L = [HEAD + f"{direction} direction"]
    for t in own:
        L.append(entity(t, logical))
    for s in stubs:
        t = M.TABLES[s]
        title = t["ua"] if logical else t["name"]
        L.append(f'entity "{title}" as {s} <<група {t["group"]}>> {{')
        for k in pk_cols(t):
            c = next(c for c in t["cols"] if c[0] == k)
            L.append("  " + _attr(t, c, logical))
        L.append("}")
    for t in own:
        for c, p in fks(t):
            L.append(_rel(t["name"], c, p, logical=logical))
    for a, b in hidden:
        L.append(f"{a} -[hidden]- {b}")
    L.append("@enduml")
    return "\n".join(L) + "\n"


def entity(t, logical):
    title = t["ua"] if logical else t["name"]
    L = [f'entity "{title}" as {t["name"]} {{']
    pk = pk_cols(t)
    for c in t["cols"]:
        if c[0] in pk:
            L.append("  " + _attr(t, c, logical))
    L.append("  --")
    for c in t["cols"]:
        if c[0] not in pk:
            L.append("  " + _attr(t, c, logical))
    L.append("}")
    return "\n".join(L)


def _attr(t, c, logical):
    mark = "* " if is_nn(t, c) else ""
    tags = []
    if c[0] in pk_cols(t):
        tags.append("PK")
    if fk_of(c):
        tags.append("FK")
    if "U" in flags(c):
        tags.append("U")
    tag = f" «{', '.join(tags)}»" if tags else ""
    if logical:
        return f"{mark}{c[3]}{tag}"
    return "{field} " + f"{mark}{c[0]} : {c[1]}{tag}"


def overview():
    """Узагальнена модель: усі сутності (лише назви) за рівнями таблиць."""
    L = [HEAD + "left to right direction\nhide empty members"]
    for lv, title in M.LEVELS.items():
        L.append(f'package "{title}" {{')
        for t in M.T:
            if t["level"] == lv:
                L.append(f'  entity "{t["ua"]}" as {t["name"]}')
        L.append("}")
    for t in M.T:
        for c, p in fks(t):
            L.append(_rel(t["name"], c, p, logical=False))
    L.append("@enduml")
    return "\n".join(L) + "\n"


# ============================================================================================ контекст
def context_mmd():
    return """flowchart LR
  classDef db fill:#E6E6E6,stroke:#000,stroke-width:2.5px,font-weight:bold;
  classDef ext fill:#FFFFFF,stroke:#000,stroke-width:1.2px;
  classDef hum fill:#F2F2F2,stroke:#000,stroke-width:1.2px;

  SEN["Сенсорні вузли<br/>(через периферійні шлюзи)"]:::ext
  GCS["Наземні станції<br/>розрахунків"]:::ext
  AN["Аналітик<br/>обстановки"]:::hum
  OBU["Офіцер бойового<br/>управління"]:::hum
  CREW["Розрахунки<br/>перехоплювачів"]:::hum

  DB[("База даних<br/>«Щит-Лінк»<br/>(18 таблиць)")]:::db

  LOG["Технік<br/>і логіст"]:::hum
  ADM["Адміністратор,<br/>офіцер кібербезпеки"]:::hum
  NAT["Національна система<br/>ситуаційної обізнаності"]:::ext

  SEN -- "виявлення,<br/>стан вузлів" --> DB
  GCS -- "телеметрія,<br/>підтвердження" --> DB
  DB -- "бойові<br/>завдання" --> GCS
  AN <-- "треки,<br/>класифікація" --> DB
  OBU <-- "місії, санкції,<br/>сектори" --> DB
  CREW <-- "готовність,<br/>звіти" --> DB
  DB <-- "облік<br/>обладнання" --> LOG
  DB <-- "користувачі, ролі,<br/>журнал аудиту" --> ADM
  DB -- "донесення про<br/>треки й результати" --> NAT
"""


# ============================================================================================ перевірка DDL
def verify(sql_text, tests):
    """Виконати DDL і тестові запити в тимчасовому кластері PostgreSQL. tests: [(sql, очікується_помилка)]."""
    td = Path(tempfile.mkdtemp(prefix="pg_l1_"))
    data, sock = td / "data", td / "sock"
    sock.mkdir()
    env = {**os.environ, "LC_ALL": "C.UTF-8"}
    run = lambda *a, **k: subprocess.run(a, capture_output=True, text=True, env=env, **k)  # noqa: E731
    try:
        r = run("initdb", "-D", str(data), "-U", "postgres", "-E", "UTF8", "--locale=C.UTF-8")
        assert r.returncode == 0, r.stderr
        r = run("pg_ctl", "-D", str(data), "-o", f"-k {sock} -c listen_addresses='' -p 54329", "-w", "start",
                "-l", str(td / "log"))
        assert r.returncode == 0, r.stderr + (td / "log").read_text()
        psql = ["psql", "-h", str(sock), "-p", "54329", "-U", "postgres", "-d", "postgres", "-X", "-q"]
        r = run(*psql, "-v", "ON_ERROR_STOP=1", input=sql_text)
        assert r.returncode == 0, "DDL: " + r.stderr
        ver = run(*psql, "-At", "-c", "SHOW server_version").stdout.strip()
        ntab = run(*psql, "-At", "-c", "SELECT count(*) FROM pg_tables WHERE schemaname='public'").stdout.strip()
        nfk = run(*psql, "-At", "-c", "SELECT count(*) FROM pg_constraint WHERE contype='f'").stdout.strip()
        nck = run(*psql, "-At", "-c", "SELECT count(*) FROM pg_constraint WHERE contype='c'").stdout.strip()
        res = []
        for q, expect_err in tests:
            r = run(*psql, "-v", "ON_ERROR_STOP=1", "-c", q)
            ok = (r.returncode != 0) == expect_err
            res.append((q, ok, (r.stderr or r.stdout).strip().splitlines()[-1:] if r.returncode else ""))
        return dict(version=ver, tables=int(ntab), fks=int(nfk), checks=int(nck), tests=res)
    finally:
        run("pg_ctl", "-D", str(data), "-m", "immediate", "stop")
        shutil.rmtree(td, ignore_errors=True)
