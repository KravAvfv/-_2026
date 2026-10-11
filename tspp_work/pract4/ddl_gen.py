"""Пряме проектування (forward engineering): фізична діаграма класів PlantUML → SQL DDL для PostgreSQL.

Клас зі стереотипом «table» → CREATE TABLE; атрибут «PK …» → PRIMARY KEY, «FK …» → REFERENCES (цільова таблиця —
за збігом імені з первинним ключем або за асоціацією діаграми); тип ENUM → CREATE TYPE (значення стану місії —
з діаграми станів, решта — model_p4.ENUMS); кратність «0..1» на боці таблиці-посилання → стовпець допускає NULL,
кратність «0..1» на боці таблиці з FK (зв’язок 1 : 0..1) → UNIQUE; стовпці з model_p4.NULLABLE допускають NULL.
"""
import re
from pathlib import Path

CLS = re.compile(r'class\s+"(\w+)\s+«table»"\s+as\s+(\w+)\s*\{\n(.*?)\n\}', re.S)
ATTR = re.compile(r'^(?:(PK|FK)\s+)?(?:\{field\}\s*)?(\w+)\s*:\s*(.+)$')
ASSOC = re.compile(r'^(\w+)\s+"([\d.*]+)"\s+--\s+"([\d.*]+)"\s+(\w+)')
STATE = re.compile(r'^(?:\[\*\]|\w+)\s+-->\s+(?:\[\*\]|(\w+))', re.M)


def parse(puml):
    text = Path(puml).read_text(encoding="utf-8")
    tables, alias = {}, {}
    for name, al, body in CLS.findall(text):
        alias[al] = name
        cols = []
        for ln in body.strip().splitlines():
            m = ATTR.match(ln.strip())
            if m:
                cols.append(dict(key=m[1], name=m[2], type=m[3].strip()))
        tables[name] = cols
    assoc = [(alias[a], ma, mb, alias[b]) for a, ma, mb, b in
             (m.groups() for m in map(ASSOC.match, text.splitlines()) if m)]
    return tables, assoc


def states(puml):
    """Стани діаграми станів у порядку першої появи (без псевдостанів [*])."""
    seen = []
    for ln in Path(puml).read_text(encoding="utf-8").splitlines():
        for s in re.findall(r'(?<![\[\w])([А-ЯІЇЄҐа-яіїєґ’]+)(?![\w\]])', ln.split(":")[0]):
            if s not in seen:
                seen.append(s)
    return [s.lower() for s in seen]


def generate(class_puml, state_puml, enums, nullable=()):
    tables, assoc = parse(class_puml)
    pk = {t: next(c["name"] for c in cols if c["key"] == "PK") for t, cols in tables.items()}
    by_pk = {v: t for t, v in pk.items()}
    enums = dict(enums)
    enums[("mission", "state")] = states(state_puml)
    out = ["-- Схема БД IoT-платформи «Щит-Лінк» (фрагмент).",
           "-- Згенеровано з діаграми класів фізичного рівня;",
           "-- не редагувати вручну.", ""]
    for (t, c), vals in enums.items():
        head, items = f"CREATE TYPE {t}_{c} AS ENUM (", ", ".join(f"'{v}'" for v in vals)
        if len(head + items) > 70:   # довгий перелік — по рядках
            items = "\n    " + ",\n    ".join(f"'{v}'" for v in vals) + "\n"
        out.append(f"{head}{items});")
    out.append("")
    target, linked = {}, {}
    for t, cols in tables.items():
        linked[t] = {a if b == t else b: (mb if b == t else ma, ma if b == t else mb)   # (своя, чужа) кратність
                     for a, ma, mb, b in assoc if t in (a, b)}
        for c in cols:
            if c["key"] == "FK":
                target[t, c["name"]] = by_pk.get(c["name"])
        for c in cols:   # FK з іншим іменем — ціль визначає асоціація, ще не покрита іменем
            if c["key"] == "FK" and target[t, c["name"]] is None:
                used = set(target[t, x["name"]] for x in cols if x["key"] == "FK")
                target[t, c["name"]] = next((o for o, (own, other) in linked[t].items()   # t — бік «багато»
                                             if o not in used and other in ("1", "0..1") and "*" in own), None)
    order = []
    while len(order) < len(tables):   # топологічний порядок: таблиця-ціль створюється раніше
        ready = [t for t in tables if t not in order and
                 {target[k] for k in target if k[0] == t and target[k] not in (None, t)} <= set(order)]
        if not ready:
            raise SystemExit("ddl_gen: циклічні зовнішні ключі")
        order += ready
    later = []
    for t in order:
        lines = []
        for c in tables[t]:
            typ = f"{t}_{c['name']}" if c["type"] == "ENUM" else c["type"]
            ref = target.get((t, c["name"]))
            own, other = linked[t].get(ref, ("", ""))
            s = f"    {c['name']} {typ}"
            if c["key"] == "PK":
                s += " PRIMARY KEY DEFAULT gen_random_uuid()"
            elif other != "0..1" and (t, c["name"]) not in nullable:
                s += " NOT NULL"
            if ref:
                tail = f"REFERENCES {ref} ({pk[ref]})" + (" UNIQUE" if own == "0..1" else "")
                s += f"\n        {tail}" if len(s + tail) > 56 else f" {tail}"
            elif c["key"] == "FK":
                later.append(f"-- {t}.{c['name']}: таблиця-ціль поза фрагментом діаграми")
            lines.append(s)
        out += [f"CREATE TABLE {t} (", ",\n".join(lines), ");", ""]
    return "\n".join(out + later) + "\n"


def code_figure(sql, out_png, width_cm=16.5, font_px=64):
    """Фрагмент коду → PNG у рамці + layout.json (для контролю читабельності build_report/check_report)."""
    import json
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype("/usr/share/fonts/liberation/LiberationMono-Regular.ttf", font_px)
    lines = sql.rstrip("\n").splitlines()
    cw, lh, pad = f.getlength("M"), int(font_px * 1.3), font_px
    w = int(max(len(ln) for ln in lines) * cw + 2 * pad)
    h = len(lines) * lh + 2 * pad
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, w - 2, h - 2], outline="black", width=3)
    for i, ln in enumerate(lines):
        d.text((pad, pad + i * lh), ln, font=f, fill=(90, 90, 90) if ln.lstrip().startswith("--") else "black")
    out_png = Path(out_png)
    img.save(out_png, dpi=(300, 300))
    pt = font_px * 0.75 * (width_cm / 2.54 * 96) / w   # кегль у документі при ширині width_cm
    dpi = w / (width_cm / 2.54)
    lay = {"file": out_png.name, "native_px": [w, h], "min_font_px": font_px,
           "portrait": {"width_cm": width_cm, "font_pt": round(pt, 1), "dpi": round(dpi)},
           "orientation": "portrait", "width_cm": width_cm, "legible": pt >= 10 and dpi >= 300}
    out_png.with_suffix(".layout.json").write_text(json.dumps(lay, ensure_ascii=False, indent=2), encoding="utf-8")
    return lay
