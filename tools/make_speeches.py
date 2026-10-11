#!/usr/bin/env python3
"""Defence prompters («СУФЛЕР») for every work of every subject → Суфлери/<дисципліна>/<робота>/NN_<назва>_СУФЛЕР.docx.

Works are listed in WORKS (subject, folder, label, title, content file, kind):
* kind "drawio" (ПІС labs) — one prompter per draw.io file, order = tools/drawio_export.py MANIFEST;
* kind "report" (other subjects) — one prompter per defence topic; each speech names the figures/tables to show.
Content file: SPEECHES = [ {id, title, notation, role, opening, walk, traps, defense, [show]} ... ]; for "drawio"
`id` is the draw.io stem (key "drawio" is accepted too). Inline markup: **жирний**.

    .venv/bin/python tools/make_speeches.py              # all works
    .venv/bin/python tools/make_speeches.py tspp cyb     # selected subjects (pis, tspp, cyb, tau)
"""
import importlib.util
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drawio_export import MANIFEST  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FONT = "Times New Roman"
OUT = ROOT / "Суфлери"
SUBJECTS = {"pis": "Проєктування інформаційних систем", "tspp": "Технології створення програмних продуктів",
            "cyb": "Кібернетична безпека підприємства", "tau": "Теорія автоматичного управління"}
LAB_TITLE = {1: "Вибір об’єкта дослідження, дерево цілей і WBS", 2: "Моделювання бізнес-процесів у нотації BPMN",
             3: "Функціональне моделювання IDEF0 / IDEF3", 4: "Моделювання DFD і вартісний аналіз (ABC)",
             5: "Об’єктно-орієнтоване моделювання UML", 7: "Концепція архітектури IoT-системи"}
# (subject, folder, label, title, content file, kind, report file)
WORKS = [("pis", f"ЛР{n}", f"ЛР {n}", t, f"lab{n}/speech/content_lab{n}.py", "drawio", f"lab{n}/ЛР{n}_Кравченко_ІР-31.docx")
         for n, t in LAB_TITLE.items()] + [
    ("tspp", "ПР1", "ПР 1", "Збір та документування вимог для програмного продукту", "tspp_work/speech/content_pr1.py",
     "report", "tspp_work/pract1/ПР1_Кравченко_ІР-31.docx"),
    ("tspp", "ПР2", "ПР 2", "Архітектура IoT екосистеми", "tspp_work/speech/content_pr2.py", "report",
     "tspp_work/pract2/ПР2_Кравченко_ІР-31.docx"),
    ("tspp", "ПР3", "ПР 3", "Опис існуючих програмних та апаратних рішень", "tspp_work/speech/content_pr3.py",
     "report", "tspp_work/pract3/ПР3_Кравченко_ІР-31.docx"),
    ("tspp", "ПР4", "ПР 4", "Проектування системи", "tspp_work/speech/content_pr4.py", "report",
     "tspp_work/pract4/ПР4_Кравченко_ІР-31.docx"),
    ("tspp", "ЛР1", "ЛР 1", "Опис бази даних", "tspp_work/speech/content_lr1.py", "report",
     "tspp_work/lab1/ЛР1_Кравченко_ІР-31.docx"),
    ("tspp", "ЛР2", "ЛР 2", "Опис програмної реалізації системи", "tspp_work/speech/content_lr2.py", "report",
     "tspp_work/lab2/ЛР2_Кравченко_ІР-31.docx"),
    ("cyb", "ЛР1", "ЛР 1", "Структура системи управління кібербезпекою підприємства та стандарти",
     "cybersec_work/speech/content_lab1.py", "report", "cybersec_work/lab1/ЛР1_Кравченко_ІР-31.docx"),
] + [("tau", f"ПЗ{n}", f"ПЗ {n}", t, f"tau_work/speech/content_pz{n}.py", "report",
      f"ТАУ/ПЗ{n}_Кравченко_ІР-31_варіант8.docx")
     for n, t in ((1, "Передатні функції елементів САУ"), (2, "Часові характеристики ланок САУ"),
                  (3, "Перетворення структурних схем і передатні функції САУ"))]


def _runs(par, text, size=None, bold=False, italic=False, color=None):
    for i, chunk in enumerate(re.split(r"\*\*", text)):
        if not chunk:
            continue
        r = par.add_run(chunk)
        r.bold = bold or (i % 2 == 1)
        r.italic = italic
        r.font.name = FONT
        r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)


def _shade(cell, fill):
    tcPr = cell._element.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill)
    tcPr.append(sh)


def _para(doc, text="", size=13, bold=False, italic=False, align=None, before=0, after=4, indent=None, color=None,
          style=None):
    p = doc.add_paragraph(style=style)
    pf = p.paragraph_format
    pf.space_before = Pt(before); pf.space_after = Pt(after); pf.line_spacing = 1.12
    if indent is not None:
        pf.left_indent = Cm(indent)
    if align:
        p.alignment = align
    _runs(p, text, size, bold, italic, color)
    return p


def _heading(doc, text, num):
    p = _para(doc, f"{num}. {text}", size=14, bold=True, before=10, after=4, color="1F3864")
    p.paragraph_format.keep_with_next = True
    # bottom rule
    pPr = p._element.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr"); b = OxmlElement("w:bottom")
    for k, v in (("val", "single"), ("sz", "6"), ("space", "1"), ("color", "1F3864")):
        b.set(qn(f"w:{k}"), v)
    bdr.append(b); pPr.append(bdr)


def build(work, idx, total, sp, out):
    subj, folder, label, title, _content, kind, report = work
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2); sec.top_margin = sec.bottom_margin = Cm(1.8)
    st = doc.styles["Normal"]; st.font.name = FONT; st.font.size = Pt(13)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

    _para(doc, f"СУФЛЕР ДО ЗАХИСТУ · {label} · {title}", size=10.5, italic=True, color="595959", after=2)
    _para(doc, sp["title"], size=17, bold=True, after=6)

    t = doc.add_table(rows=0, cols=2)
    t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    rows = [("Дисципліна", SUBJECTS[subj])]
    if kind == "drawio":
        rows += [("Нотація", sp["notation"]), ("Файл draw.io", f"{folder.replace('ЛР', 'lab')}/drawio/{sp['id']}.drawio"),
                 ("Порядок показу", f"{idx} з {total}"), ("Роль у системі", sp["role"])]
    else:
        rows += [("Тема відповіді", sp["notation"]), ("Що показати у звіті", sp.get("show", "—")),
                 ("Звіт", report), ("Порядок показу", f"{idx} з {total}"), ("Роль у роботі", sp["role"])]
    for k, v in rows:
        c0, c1 = t.add_row().cells
        c0.width, c1.width = Cm(4.2), Cm(12.8)
        _shade(c0, "E8EEF7")
        c0.paragraphs[0].text = ""; _runs(c0.paragraphs[0], k, 11.5, bold=True)
        c1.paragraphs[0].text = ""; _runs(c1.paragraphs[0], v, 11.5)

    _heading(doc, "З чого почати відповідь", 1)
    for s in (sp["opening"] if isinstance(sp["opening"], list) else [sp["opening"]]):
        p = _para(doc, s, size=13.5, after=4)
        p.paragraph_format.left_indent = Cm(0.4)

    _heading(doc, "Покрокова екскурсія по схемі" if kind == "drawio" else "Покрокова відповідь", 2)
    for i, step in enumerate(sp["walk"], 1):
        p = _para(doc, "", size=13, after=4, indent=0.9)
        p.paragraph_format.first_line_indent = Cm(-0.9)
        _runs(p, f"{i}. ", 13, bold=True, color="1F3864")
        _runs(p, step, 13)

    _heading(doc, "Підводні камені та типові питання викладача", 3)
    for q, a in sp["traps"]:
        p = _para(doc, "", size=13, before=4, after=1)
        p.paragraph_format.keep_with_next = True
        _runs(p, "Питання: ", 13, bold=True, color="C00000")
        _runs(p, q, 13, bold=True)
        p = _para(doc, "", size=13, after=4, indent=0.6)
        _runs(p, "Відповідь: ", 13, bold=True, color="1F6F3C")
        _runs(p, a, 13)

    _heading(doc, "Що відповісти, якщо придереться", 4)
    for d in sp["defense"]:
        p = _para(doc, "", size=13, after=3, indent=0.6)
        p.paragraph_format.first_line_indent = Cm(-0.5)
        _runs(p, "▸ ", 13, color="1F3864")
        _runs(p, d, 13)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)


def load(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, ROOT / path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    out = mod.SPEECHES
    for sp in out:
        sp.setdefault("id", sp.get("drawio"))
    return out


def slug(s):
    return re.sub(r"[^\w\-.]+", "_", s, flags=re.U).strip("_")


def main(argv):
    subjects = [a for a in argv if a in SUBJECTS] or list(SUBJECTS)
    index = {}
    for work in WORKS:
        subj, folder, label, title, content, kind, report = work
        if subj not in subjects:
            continue
        speeches = load(content)
        if kind == "drawio":
            names = [m[1] for m in MANIFEST[int(folder[2:])]]
            got = [s["id"] for s in speeches]
            assert got == names, f"{folder}: speech order/names {got} != draw.io manifest {names}"
        for i, sp in enumerate(speeches, 1):
            for k in ("id", "title", "notation", "role", "opening", "walk", "traps", "defense"):
                assert sp.get(k), f"{subj} {folder} {sp.get('id')}: empty {k}"
            assert 3 <= len(sp["traps"]) <= 5, f"{subj} {folder} {sp['id']}: need 3–5 traps"
            name = sp["id"] if kind == "drawio" else f"{i:02d}_{slug(sp['id'])}"
            safe = title.replace(" / ", " і ").replace("/", "-")
            out = OUT / SUBJECTS[subj] / f"{folder} {safe}" / f"{name}_СУФЛЕР.docx"
            build(work, i, len(speeches), sp, out)
            index.setdefault(SUBJECTS[subj], []).append((folder, title, out.relative_to(OUT), sp["title"]))
        print(f"{SUBJECTS[subj]} / {folder}: {len(speeches)}")
    if set(subjects) == set(SUBJECTS):
        lines = ["# Суфлери до захисту", "", "Згенеровано `tools/make_speeches.py`; зміст — у файлах content_*.py "
                 "відповідних робіт.", ""]
        for subj, items in index.items():
            lines += [f"## {subj}", ""]
            for folder, title, rel, t in items:
                lines.append(f"- **{folder}** — [{t}]({str(rel).replace(' ', '%20')})")
            lines.append("")
        (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
