#!/usr/bin/env python3
"""Збирання пояснювальної записки курсової роботи (.docx + .pdf) зі специфікації report.yaml.

    .venv/bin/python coursework_final/build_cw.py coursework_final/report.yaml [--pdf]

Оформлення — за методичними вказівками до курсової роботи з ПІС (КНУ, 2026), розд. 4.3 (див. REQUIREMENTS.md, D1–D18):
A4, поля 30/10/20/20 мм; Times New Roman 14 pt, інтервал 1,5, абзац 1,25 см, вирівнювання за шириною, інтервали
0 pt; номер сторінки праворуч угорі без крапки, на титульному аркуші не ставиться; назви структурних елементів —
великими літерами, напівжирно, по центру, кожен розділ — з нової сторінки; підрозділи — з абзацу, напівжирно,
18/12 pt; підпис рисунка «Рисунок 1.1 – Назва» по центру (абзац 1 см, 6/18 pt); підпис таблиці «Таблиця 1.1 –
Назва» праворуч над таблицею (18/6 pt, не відривати від наступного); додатки — «ДОДАТКИ» на окремому аркуші, кожен
додаток з нової сторінки, «Додаток А» праворуч угорі, назва по центру; посилання «[n, с. x]».

Блоки специфікації (кожен — словник з одним ключем):
  title, assignment, toc                      — титульний аркуш, завдання, зміст
  structural: "ВСТУП"                         — ненумерований структурний елемент (нова сторінка)
  chapter: [1, "НАЗВА РОЗДІЛУ"]               — «РОЗДІЛ 1» + назва (нова сторінка)
  h2: "1.1 Назва" / h3: "2.2.1 Назва"
  p: "текст {fig:id} {tab:id} {app:id} {cite:key} {cite:key|с. 8} {cite:a,b}"
  list: [..] (+ style: dash | letter | num)    — переліки за п. 4.3.5
  table: {id, caption, header, rows, widths, font, continue_at}
  figure: {id, src, caption, width_cm}
  code: {text, font}                          — лістинг (моноширинний)
  refs: true                                  — перелік джерел у порядку першого посилання
  appendices: true                            — аркуш «ДОДАТКИ»
  appendix: {id, title}                       — новий додаток
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

import yaml
from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FONT = "Times New Roman"
GEO = dict(w=21.0, h=29.7, left=3.0, right=1.0, top=2.0, bottom=2.0)
# альбомний аркуш: поле підшивки (30 мм) — уздовж верхнього краю повернутого аркуша
GEO_L = dict(w=29.7, h=21.0, left=2.0, right=2.0, top=3.0, bottom=1.0)
TEXT_W = GEO["w"] - GEO["left"] - GEO["right"]                       # 17 см
TEXT_W_L = GEO_L["w"] - GEO_L["left"] - GEO_L["right"]               # 25,7 см
FIG_PT = 10.0                                                        # цільовий кегль тексту на рисунках
APPENDIX_LETTERS = "АБВГДЕЖИКЛМНПРСТУФХЦШЩЮЯ"                         # без Ґ, Є, З, І, Ї, Й, О, Ч, Ь
J, C, L, R = WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.RIGHT


# ----------------------------------------------------------------------------- низькорівневі допоміжні функції
def font(run, size=14, bold=None, italic=None, name=FONT):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor(0, 0, 0)
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), name)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def par_fmt(p, align=J, indent=1.25, spacing=1.5, before=0, after=0, keep=False, left=0.0, hanging=None):
    pf = p.paragraph_format
    p.alignment = align
    pf.first_line_indent = Cm(-hanging) if hanging else Cm(indent)
    pf.left_indent = Cm(left)
    pf.right_indent = Cm(0)
    pf.line_spacing = spacing
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.keep_with_next = keep
    pf.widow_control = True


INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)")


def text(p, s, size=14, bold=False, italic=False, name=FONT):
    """Інлайн-розмітка: **напівжирний**, *курсив*."""
    for part in INLINE.split(s):
        if not part:
            continue
        b, i, t = bold, italic, part
        if part.startswith("**") and part.endswith("**"):
            b, t = True, part[2:-2]
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            i, t = True, part[1:-1]
        font(p.add_run(t), size, b, i, name)


def field(par, instr, size=14):
    for kind, val in (("begin", None), ("instr", instr), ("separate", None), ("text", "1"), ("end", None)):
        r = par.add_run()
        font(r, size)
        if kind == "instr":
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = f" {val} "
        elif kind == "text":
            el = OxmlElement("w:t"); el.text = val
        else:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind)
        r._element.append(el)


def raw_run(parent, kind, val=None, size=14):
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr"); rf = OxmlElement("w:rFonts")
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rf.set(qn(a), FONT)
    rpr.append(rf)
    for tag in ("w:sz", "w:szCs"):
        el = OxmlElement(tag); el.set(qn("w:val"), str(size * 2)); rpr.append(el)
    r.append(rpr)
    if kind == "instr":
        el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = val
    elif kind == "text":
        el = OxmlElement("w:t"); el.set(qn("xml:space"), "preserve"); el.text = val
    elif kind == "tab":
        el = OxmlElement("w:tab")
    else:
        el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind)
    r.append(el)
    parent.append(r)


def borders(table, show=True):
    tbl_pr = table._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{e}")
        el.set(qn("w:val"), "single" if show else "nil"); el.set(qn("w:sz"), "6"); el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        b.append(el)
    tbl_pr.append(b)


def row_flag(row, tag):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement(f"w:{tag}"); el.set(qn("w:val"), "true"); trpr.append(el)


def cell_text(cell, s, size, bold=False, align=L):
    cell.text = ""
    lines = s if isinstance(s, list) else str(s).split("\n")
    for k, line in enumerate(lines):
        p = cell.paragraphs[0] if k == 0 else cell.add_paragraph()
        par_fmt(p, align=align, indent=0, spacing=1.0)
        text(p, str(line), size=size, bold=bold)


def drop_trailing_spacer(doc):
    """Прибрати останній порожній абзац перед примусовим розривом сторінки / розділу (інакше він може залишитися
    сам на сторінці й утворити порожній аркуш)."""
    body = doc.element.body
    last = body[-1] if body[-1].tag != qn("w:sectPr") else body[-2]
    if last.tag == qn("w:p") and not "".join(last.itertext()).strip() and last.find(".//" + qn("w:drawing")) is None \
            and last.find(qn("w:pPr") + "/" + qn("w:sectPr")) is None:
        body.remove(last)


def bookmark(p, name, bid):
    bs = OxmlElement("w:bookmarkStart"); bs.set(qn("w:id"), str(bid)); bs.set(qn("w:name"), name)
    be = OxmlElement("w:bookmarkEnd"); be.set(qn("w:id"), str(bid))
    first = p._p.find(qn("w:r"))
    first.addprevious(bs)
    p._p.append(be)


def geometry(sec, g, orient):
    sec.orientation = orient
    sec.page_width, sec.page_height = Cm(g["w"]), Cm(g["h"])
    sec.left_margin, sec.right_margin = Cm(g["left"]), Cm(g["right"])
    sec.top_margin, sec.bottom_margin = Cm(g["top"]), Cm(g["bottom"])
    sec.header_distance, sec.footer_distance = Cm(1.0), Cm(1.0)


# ----------------------------------------------------------------------------- збирач
class Builder:
    def __init__(self, spec, toc_pages=None, break_tables=frozenset(), auto_cuts=None):
        self.spec = spec
        self.auto_cuts = auto_cuts or {}          # номер таблиці → індекси рядків, з яких починається продовження
        self.toc_pages = toc_pages or {}
        self.break_tables = set(break_tables)
        self.doc = Document()
        self.toc_entries = []          # [(level, text, bookmark)]
        self.table_meta = []           # [(key, probe, last_row_text)]
        self._bm = 0
        self._number()
        self._setup()

    # -- попередня нумерація: розділи, рисунки, таблиці, додатки, джерела (для посилань уперед)
    def _number(self):
        self.ids = {"fig": {}, "tab": {}, "app": {}}
        ch, app, f, t = None, None, 0, 0
        letters = iter(APPENDIX_LETTERS)
        for b in self.spec["blocks"]:
            k = next(iter(b))
            if k == "chapter":
                ch, f, t = str(b[k][0]), 0, 0
            elif k == "appendix":
                app = next(letters)
                ch, f, t = app, 0, 0
                self.ids["app"][b[k]["id"]] = app
            elif k in ("structural", "refs") and app is None:
                ch = None
            elif k == "figure":
                f += 1
                self.ids["fig"][b[k]["id"]] = f"{ch}.{f}"
            elif k == "table":
                t += 1
                self.ids["tab"][b[k]["id"]] = f"{ch}.{t}"
        # джерела — у порядку першого посилання в тексті
        self.sources = {s["key"]: s for s in self.spec["sources"]}
        order = []
        for b in self.spec["blocks"]:
            for m in re.finditer(r"\{cite:([^}|]+)(?:\|[^}]*)?\}", json.dumps(b, ensure_ascii=False)):
                for key in m.group(1).split(","):
                    key = key.strip()
                    if key not in self.sources:
                        sys.exit(f"Невідоме джерело {key}")
                    if key not in order:
                        order.append(key)
        unused = set(self.sources) - set(order)
        if unused:
            sys.exit(f"Джерела без посилань у тексті: {sorted(unused)}")
        self.cite_no = {k: i for i, k in enumerate(order, 1)}

    def resolve(self, s):
        def rep(m):
            kind, body = m.group(1), m.group(2)
            if kind == "cite":
                keys, _, pages = body.partition("|")
                nums = [str(self.cite_no[k.strip()]) for k in keys.split(",")]
                return "[" + ", ".join(nums) + (f", {pages}" if pages else "") + "]"
            if body not in self.ids[kind]:
                sys.exit(f"Невідоме посилання {{{kind}:{body}}}")
            return self.ids[kind][body]
        return re.sub(r"\{(fig|tab|app|cite):([^}]+)\}", rep, str(s))

    def _setup(self):
        st = self.doc.styles["Normal"]
        st.font.name, st.font.size = FONT, Pt(14)
        st.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
        pf = st.paragraph_format
        pf.line_spacing, pf.space_before, pf.space_after = 1.5, Pt(0), Pt(0)
        for lvl in (1, 2, 3):
            hs = self.doc.styles[f"Heading {lvl}"]
            rpr = hs.element.get_or_add_rPr()
            for child in list(rpr):
                rpr.remove(child)
            hs.font.name, hs.font.size, hs.font.bold, hs.font.italic = FONT, Pt(14), True, False
            hs.font.color.rgb = RGBColor(0, 0, 0)
            rpr.get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
        geometry(self.doc.sections[0], GEO, WD_ORIENT.PORTRAIT)
        self.orient, self._fresh = "portrait", False
        cp = self.doc.core_properties
        cp.author, cp.title, cp.language = self.spec["student_short"], self.spec["theme"], "uk-UA"
        cp.subject = "Курсова робота з дисципліни «Проєктування інформаційних систем»"

    def switch(self, orient):
        """Новий розділ документа з іншою орієнтацією; наступний заголовок не додає розриву сторінки."""
        if orient == self.orient:
            return
        drop_trailing_spacer(self.doc)
        sec = self.doc.add_section(WD_SECTION.NEW_PAGE)
        geometry(sec, GEO_L if orient == "landscape" else GEO, WD_ORIENT.LANDSCAPE if orient == "landscape"
                 else WD_ORIENT.PORTRAIT)
        # номер сторінки — у правому верхньому куті переплетеного аркуша: на альбомній сторінці (переплет угорі)
        # це правий нижній кут, тобто нижній колонтитул
        sec.header.is_linked_to_previous = False
        sec.footer.is_linked_to_previous = False
        hp, fp = sec.header.paragraphs[0], sec.footer.paragraphs[0]
        for par in (hp, fp):
            for r in list(par.runs):
                r._r.getparent().remove(r._r)
        tgt = fp if orient == "landscape" else hp
        par_fmt(tgt, align=R, indent=0, spacing=1.0)
        field(tgt, "PAGE")
        self.orient, self._fresh = orient, True

    def page_break(self, par, new_page):
        if new_page and not self._fresh:
            prev = par._p.getprevious()                     # порожній абзац перед розривом — прибрати
            if prev is not None and prev.tag == qn("w:p") and not "".join(prev.itertext()).strip() and \
                    prev.find(".//" + qn("w:drawing")) is None and prev.find(qn("w:pPr") + "/" + qn("w:sectPr")) is None:
                prev.getparent().remove(prev)
        par.paragraph_format.page_break_before = bool(new_page) and not self._fresh
        self._fresh = False

    def p(self, align=J, **kw):
        par = self.doc.add_paragraph()
        par_fmt(par, align=align, **kw)
        return par

    def new_page_par(self, par):
        par.paragraph_format.page_break_before = True

    # -- титульний аркуш (додаток А методичних вказівок)
    def title(self):
        s = self.spec
        for line, sz, b, before in (("МІНІСТЕРСТВО ОСВІТИ І НАУКИ УКРАЇНИ", 14, True, 0),
                                    ("КИЇВСЬКИЙ НАЦІОНАЛЬНИЙ УНІВЕРСИТЕТ ІМ. Т.Г. ШЕВЧЕНКА", 14, True, 12),
                                    ("Кафедра інформаційних систем і технологій", 14, False, 12)):
            text(self.p(C, indent=0, before=before), line, sz, b)
        text(self.p(C, indent=0, before=96), "ПОЯСНЮВАЛЬНА ЗАПИСКА", 16, True)
        text(self.p(C, indent=0, before=6), "до курсової роботи", 14)
        text(self.p(C, indent=0), "з дисципліни «Проєктування інформаційних систем»", 14)
        par = self.p(C, indent=0, before=18)
        text(par, "на тему: ", 14)
        text(par, f"«{s['theme']}»", 14, True)
        tbl = self.doc.add_table(rows=1, cols=2)
        borders(tbl, False)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        left = [f"студент {s['course']} курсу групи {s['group']}", "", s["student_full"],
                "(прізвище, ім’я та по батькові)", "", "_____________   _____________", "(дата здачі)          (підпис)"]
        right = ["Керівник курсової роботи:", "", s["supervisor_degree"], "(науковий ступінь, вчене звання або посада)",
                 "", s["supervisor_name"], "(прізвище, ім’я та по батькові)"]
        for cell, lines in zip(tbl.rows[0].cells, (left, right)):
            cell.width = Cm(TEXT_W / 2)
            cell.text = ""
            for k, ln in enumerate(lines):
                par = cell.paragraphs[0] if k == 0 else cell.add_paragraph()
                par_fmt(par, align=L if cell is tbl.rows[0].cells[0] else L, indent=0, spacing=1.0)
                text(par, ln, 11 if ln.startswith("(") else 14)
        spacer = self.doc.paragraphs[-1]                      # таблицю відсунуто від назви
        spacer.paragraph_format.space_after = Pt(72)
        text(self.p(C, indent=0, before=100), f"Київ – {s['year']}", 14)
        # розрив розділу: титульний аркуш — розділ без номера сторінки
        self.doc.add_section(WD_SECTION.NEW_PAGE)
        body = self.doc.sections[-1]
        body.header.is_linked_to_previous = False
        hp = body.header.paragraphs[0]
        par_fmt(hp, align=R, indent=0, spacing=1.0)
        field(hp, "PAGE")
        first = self.doc.sections[0]
        first.header.is_linked_to_previous = False
        for par in first.header.paragraphs:
            for r in list(par.runs):
                r._r.getparent().remove(r._r)

    # -- завдання на курсову роботу
    def assignment(self):
        a = self.spec["assignment"]
        text(self.p(C, indent=0, spacing=1.0), "КИЇВСЬКИЙ НАЦІОНАЛЬНИЙ УНІВЕРСИТЕТ ІМЕНІ ТАРАСА ШЕВЧЕНКА", 12, True)
        text(self.p(C, indent=0, spacing=1.0), "Факультет інформаційних технологій", 12)
        text(self.p(C, indent=0, spacing=1.0, after=6), "Кафедра інформаційних систем та технологій", 12)
        text(self.p(C, indent=0, spacing=1.0), "ЗАВДАННЯ", 14, True)
        text(self.p(C, indent=0, spacing=1.0, after=6), "на курсову роботу студента", 12, True)
        for label, val in a["fields"]:
            par = self.p(L, indent=0, spacing=1.0, after=2)
            text(par, f"{label} ", 12, True)
            text(par, val, 12)
        text(self.p(L, indent=0, spacing=1.0, before=4, after=2), "Календарний план виконання роботи", 12, True)
        tbl = self.doc.add_table(rows=1 + len(a["plan"]), cols=4)
        borders(tbl)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        w = [1.1, 10.4, 3.0, 2.5]
        for j, h in enumerate(["№", "Етап роботи", "Термін виконання", "Примітка"]):
            cell_text(tbl.rows[0].cells[j], h, 11, True, C)
        for i, (stage, term) in enumerate(a["plan"], 1):
            for j, v in enumerate([str(i), stage, term, ""]):
                cell_text(tbl.rows[i].cells[j], v, 11, align=C if j in (0, 2) else L)
        for row in tbl.rows:
            for j, c in enumerate(row.cells):
                c.width = Cm(w[j])
        for line in a["signatures"]:
            text(self.p(L, indent=0, spacing=1.0, before=6), line, 12)

    # -- зміст
    def toc(self):
        head = self.p(C, indent=0, after=12)
        self.page_break(head, True)
        text(head, "ЗМІСТ", 14, True)
        entries = self._scan_headings()
        for i, (lvl, label, bm) in enumerate(entries):
            par = self.doc.add_paragraph()
            par.style = self.doc.styles[f"toc {min(lvl, 2)}"] if f"toc {min(lvl, 2)}" in \
                [x.name for x in self.doc.styles] else self.doc.styles["Normal"]
            indent = {1: 0, 2: 0.5, 3: 1.0}[lvl]
            par_fmt(par, align=L, indent=0, spacing=1.5, left=indent)
            par.paragraph_format.tab_stops.add_tab_stop(Cm(TEXT_W), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            if i == 0:
                raw_run(par._p, "begin"); raw_run(par._p, "instr", ' TOC \\o "1-3" \\h \\z \\u ')
                raw_run(par._p, "separate")
            link = OxmlElement("w:hyperlink"); link.set(qn("w:anchor"), bm); link.set(qn("w:history"), "1")
            raw_run(link, "text", label); raw_run(link, "tab")
            raw_run(link, "begin"); raw_run(link, "instr", f" PAGEREF {bm} \\h "); raw_run(link, "separate")
            raw_run(link, "text", str(self.toc_pages.get(bm, ""))); raw_run(link, "end")
            par._p.append(link)
            if i == len(entries) - 1:
                raw_run(par._p, "end")

    def _scan_headings(self):
        out, n, letters = [], 0, iter(APPENDIX_LETTERS)
        for b in self.spec["blocks"]:
            k = next(iter(b)); v = b[k]
            if k in ("structural", "chapter", "h2", "h3", "refs", "appendices", "appendix"):
                n += 1
                bm = f"_Toc{n:06d}"
                if k == "structural":
                    out.append((1, v, bm))
                elif k == "chapter":
                    out.append((1, f"РОЗДІЛ {v[0]} {v[1]}", bm))
                elif k == "h2":
                    out.append((2, self.resolve(v), bm))
                elif k == "h3":
                    out.append((3, self.resolve(v), bm))
                elif k == "refs":
                    out.append((1, "ПЕРЕЛІК ВИКОРИСТАНИХ ІНФОРМАЦІЙНИХ ДЖЕРЕЛ", bm))
                elif k == "appendices":
                    out.append((1, "ДОДАТКИ", bm))
                else:
                    out.append((2, f"Додаток {next(letters)}. {v['title']}", bm))
        return [e for e in out if e[0] <= 2]

    # -- заголовки
    def _heading(self, label, level, align, indent, before, after, new_page, lines=None):
        par = self.doc.add_paragraph()
        par.style = self.doc.styles[f"Heading {level}"]
        par_fmt(par, align=align, indent=indent, before=before, after=after, keep=True)
        self.page_break(par, new_page)
        for k, ln in enumerate(lines or [label]):
            if k:
                par.add_run().add_break()
            font(par.add_run(ln), 14, True)
        self._bm += 1
        bm = f"_Toc{self._bm:06d}"
        bookmark(par, bm, self._bm)
        self.toc_entries.append((level, label, bm))
        return par

    def structural(self, label):
        self._heading(label, 1, C, 0, 0, 12, True)

    def chapter(self, num, title):
        self.chapter_no, self.appendix = str(num), None
        self._heading(f"РОЗДІЛ {num} {title}", 1, C, 0, 0, 12, True, [f"РОЗДІЛ {num}", title])

    def h2(self, label):
        self._heading(self.resolve(label), 2, L, 1.25, 18, 12, False)

    def h3(self, label):
        self._heading(self.resolve(label), 3, L, 1.25, 18, 12, False)

    # -- текст, переліки
    def para(self, s):
        for chunk in str(s).strip().split("\n\n"):
            text(self.p(), self.resolve(" ".join(chunk.split())))
        self._fresh = False

    def lst(self, items, style="dash"):
        self._fresh = False
        for k, it in enumerate(items):
            marker = {"dash": "– ", "letter": f"{'абвгдежиклмнпрстуфхцшщюя'[k]}) ", "num": f"{k + 1}) "}[style]
            text(self.p(), marker + self.resolve(it))

    def code(self, c):
        self._fresh = False
        for line in c["text"].rstrip("\n").split("\n"):
            par = self.p(L, indent=0, spacing=1.0)
            font(par.add_run(line if line else " "), c.get("font", 11), name="Courier New")

    # -- таблиці
    def table(self, t):
        num = self.ids["tab"][t["id"]]
        header, rows = t["header"], t["rows"]
        for i, r in enumerate(rows, 1):
            if len(r) != len(header):
                sys.exit(f"Таблиця {num}: рядок {i} має {len(r)} клітинок замість {len(header)}")
        cuts = [0] + sorted(set(t.get("continue_at", [])) | set(self.auto_cuts.get(num, []))) + [len(rows)]
        n = len(cuts) - 1
        for ci, (lo, hi) in enumerate(zip(cuts, cuts[1:])):
            if ci == 0:
                cap = f"Таблиця {num} – {self.resolve(t['caption'])}"
            else:
                cap = f"{'Закінчення' if ci == n - 1 else 'Продовження'} табл. {num}"
            key = f"{num}#{ci}"
            self._table_chunk(t, header, rows[lo:hi], cap, key, ci > 0 or key in self.break_tables, num, lo)

    def _table_chunk(self, t, header, rows, caption, key, new_page, num, offset):
        cap = self.p(R, indent=0, before=18, after=6, keep=True)
        self.page_break(cap, new_page)
        text(cap, caption, 14, True)
        size = t.get("font", 12)
        tbl = self.doc.add_table(rows=1 + len(rows), cols=len(header))
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        borders(tbl)
        widths = t.get("widths") or [1] * len(header)
        widths = [(TEXT_W_L if self.orient == "landscape" else TEXT_W) * w / sum(widths) for w in widths]
        for j, h in enumerate(header):
            cell_text(tbl.rows[0].cells[j], self.resolve(h), size, True, C)
        row_flag(tbl.rows[0], "tblHeader")
        for i, r in enumerate(rows, 1):
            for j, v in enumerate(r):
                val = [self.resolve(x) for x in v] if isinstance(v, list) else self.resolve(v)
                cell_text(tbl.rows[i].cells[j], val, size, align=C if t.get("center_cols") and j in
                          t["center_cols"] else L)
        for row in tbl.rows:
            row_flag(row, "cantSplit")
            for j, c in enumerate(row.cells):
                c.width = Cm(widths[j])
        for row in tbl.rows[:-1]:                     # таблицю (частину) не розривати
            for c in row.cells:
                for par in c.paragraphs:
                    par.paragraph_format.keep_with_next = True
        flat = lambda r: self.resolve(" ".join(" ".join(x) if isinstance(x, list) else str(x) for x in r))  # noqa
        cells = [[self.resolve(" ".join(x) if isinstance(x, list) else str(x)) for x in r] for r in rows]
        self.table_meta.append((key, caption.split(" – ")[0], [flat(r) for r in rows], num, offset,
                                " ".join(self.resolve(h) for h in header), cells, widths,
                                [self.resolve(h) for h in header]))
        self.p(L, indent=0, spacing=1.0)              # порожній абзац після таблиці

    # -- рисунки
    @staticmethod
    def _fig_orient(f):
        if f.get("orientation"):
            return f["orientation"]
        src = (ROOT / f["src"]).resolve()
        lj = (src.with_suffix(".png") if src.suffix in (".mmd", ".bpmn", ".puml") else src).with_suffix(".layout.json")
        return json.loads(lj.read_text(encoding="utf-8")).get("orientation", "portrait") if lj.exists() else "portrait"

    def figure(self, f):
        num = self.ids["fig"][f["id"]]
        src = (ROOT / f["src"]).resolve()
        img, lay = src, {}
        if src.suffix in (".mmd", ".bpmn", ".puml"):
            img = src.with_suffix(".png")
            lj = src.with_suffix(".layout.json")
            tool = {".mmd": "tools/mmd_render.py", ".bpmn": "tools/bpmn_model.py", ".puml": "tools/puml_render.py"}
            if not img.exists() or not lj.exists() or img.stat().st_mtime < src.stat().st_mtime:
                r = subprocess.run([sys.executable, str(ROOT / tool[src.suffix]), str(src)], capture_output=True,
                                   text=True)
                if r.returncode:
                    sys.exit(f"Рисунок {src.name}: помилка рендерингу/читабельності\n{r.stdout}{r.stderr}")
        lj = img.with_suffix(".layout.json")
        if lj.exists():
            lay = json.loads(lj.read_text(encoding="utf-8"))
        orient = f.get("orientation") or lay.get("orientation", "portrait")
        self.switch(orient)
        base = f.get("width_cm") or (lay.get(orient, {}).get("width_cm") or 16.5)
        base_pt = lay.get(orient, {}).get("font_pt")
        width = base
        if base_pt and base_pt > FIG_PT and not f.get("width_cm"):   # не більше, ніж потрібно для ≈ 10,5 pt
            width = base * FIG_PT / base_pt
        from PIL import Image
        wpx, hpx = Image.open(img).size                     # висота рисунка з підписом — у межах сторінки
        max_h = (20.0 if self._after_appendix_title else 22.8) if orient == "portrait" else 15.0
        width = min(width, max_h * wpx / hpx, TEXT_W_L if orient == "landscape" else TEXT_W)
        if base_pt:                                         # але кегль не менше 10 pt
            width = max(width, min(base * 10.0 / base_pt, TEXT_W_L if orient == "landscape" else TEXT_W))
        pt = round(base_pt * width / base, 1) if base_pt else None
        pic = self.p(C, indent=0, spacing=1.0, before=6, keep=True)
        self._fresh = False
        pic.add_run().add_picture(str(img), width=Cm(width))
        cap = self.p(C, indent=1.0, before=6, after=18)
        text(cap, f"Рисунок {num} – {self.resolve(f['caption'])}", 14, True)
        self.figures_used.append((num, str(img.relative_to(ROOT)), orient, round(width, 2), pt))

    # -- джерела, додатки
    def refs(self):
        self._heading("ПЕРЕЛІК ВИКОРИСТАНИХ ІНФОРМАЦІЙНИХ ДЖЕРЕЛ", 1, C, 0, 0, 12, True)
        for key, n in sorted(self.cite_no.items(), key=lambda kv: kv[1]):
            par = self.p(J, indent=1.25)
            text(par, f"{n}. {self.sources[key]['text']}")

    def appendices(self):
        par = self._heading("ДОДАТКИ", 1, C, 0, 0, 0, True)
        par.paragraph_format.space_before = Pt(280)               # посередині чистого аркуша

    _after_appendix_title = False

    def appendix_block(self, a):
        letter = self.ids["app"][a["id"]]
        par = self.p(R, indent=0, keep=True)
        self.page_break(par, True)
        text(par, f"Додаток {letter}", 14, True)
        h = self._heading(f"Додаток {letter}. {a['title']}", 2, C, 0, 6, 12, False, [a["title"]])
        h.paragraph_format.first_line_indent = Cm(0)

    # -- головний цикл
    def build(self, out):
        self.figures_used = []
        for i, b in enumerate(self.spec["blocks"]):
            k = next(iter(b)); v = b[k]
            if k == "appendix":                   # заголовок додатка — на тому ж аркуші, що й перший рисунок
                nb = self.spec["blocks"][i + 1] if i + 1 < len(self.spec["blocks"]) else {}
                self.switch(self._fig_orient(nb["figure"]) if "figure" in nb else "portrait")
            elif k not in ("figure", "title"):
                self.switch(b.get("orientation", "portrait") if k in ("table", "p", "h3") else "portrait")
            if k == "title": self.title()
            elif k == "assignment": self.assignment()
            elif k == "toc": self.toc()
            elif k == "structural": self.structural(v)
            elif k == "chapter": self.chapter(*v)
            elif k == "h2": self.h2(v)
            elif k == "h3": self.h3(v)
            elif k == "p": self.para(v)
            elif k == "list": self.lst(v, b.get("style", "dash"))
            elif k == "table": self.table(v)
            elif k == "figure":
                self._after_appendix_title = i > 0 and "appendix" in self.spec["blocks"][i - 1]
                self.figure(v)
            elif k == "code": self.code(v)
            elif k == "refs": self.refs()
            elif k == "appendices": self.appendices()
            elif k == "appendix": self.appendix_block(v)
            else: sys.exit(f"Невідомий блок {k}")
        self.doc.save(str(out))
        return out


# ----------------------------------------------------------------------------- цикл верстки за PDF
def pdf_pages(pdf, layout=False):
    n = int(subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout.split("Pages:")[1].split()[0])
    args = ["-layout"] if layout else []
    return [subprocess.run(["pdftotext", *args, "-f", str(i), "-l", str(i), str(pdf), "-"], capture_output=True,
                           text=True).stdout for i in range(1, n + 1)]


WORD = re.compile(r"[A-Za-zА-ЯІЇЄҐа-яіїєґ’']{5,}")


TOKEN = re.compile(r"[A-Za-zА-ЯІЇЄҐа-яіїєґ’'\-]{3,}|\d+(?:\.\d+)+")
PT = 72 / 2.54


def pdf_words(pdf):
    """Слова кожної сторінки з координатами (pdftotext -bbox): [(x0, y0, текст)], y — від верху сторінки, pt."""
    html = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True).stdout
    out = []
    for page in html.split("<page ")[1:]:
        out.append([(float(x0), float(y0), w) for x0, y0, w in
                    re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)"[^>]*>([^<]*)</word>', page)])
    return out


def _caption_y(words, probe, after=-1.0):
    toks = probe.split()
    for i in range(len(words) - len(toks) + 1):
        if words[i][1] > after and all(words[i + k][2] == toks[k] for k in range(len(toks))):
            return words[i][1]
    return None


def split_tables(pages, meta, words):
    """Частини таблиць, розірвані між сторінками (OnlyOffice ігнорує keep-with-next у таблицях).
    Для кожної частини знаходимо координату її підпису і шукаємо ключове слово кожного рядка лише в межах
    «ключового» стовпця (за шириною стовпців) нижче підпису і вище наступного підпису, у порядку зростання y.
    Повертає [(key, num, offset, end, перший_рядок_що_не_вмістився або None)]."""
    bad, used = [], {}
    for key, probe, rows, num, offset, header, cells, widths, header_cells in meta:
        start = used.get(probe, 0)
        pg = next((i for i in range(start, len(pages)) if probe in pages[i]), None)
        if pg is None:
            continue
        used[probe] = pg + 1
        w = words[pg]
        y0 = _caption_y(w, probe)
        if y0 is None:
            continue
        y_end = next((w[i][1] for i in range(len(w) - 2) if w[i][1] > y0 + 1 and (
            (w[i][2] in ("Таблиця", "Рисунок") and re.fullmatch(r"[А-ЯA-Z\d]+\.\d+", w[i + 1][2])
             and w[i + 2][2] == "–") or (w[i][2] in ("Продовження", "Закінчення") and w[i + 1][2] == "табл."))),
            1e9)
        ncol = len(cells[0]) if cells else 0
        col = next((c for c in range(ncol) if all(TOKEN.search(r[c]) for r in cells)), None)
        if col is None:
            continue
        x_l = GEO["left"] * PT + sum(widths[:col]) * PT - 2
        x_r = x_l + widths[col] * PT + 4
        last_y, found = y0, 0
        for r in cells:
            tok = TOKEN.search(r[col]).group(0).split("-")[0][:6]   # перенос слова в клітинці — лише префікс
            ys = [y for x, y, t in w if x_l <= x <= x_r and last_y < y < y_end and tok in t]
            if not ys:
                break
            last_y, found = min(ys), found + 1
        if found == len(cells) and y_end == 1e9 and pg + 1 < len(words):
            # частина рядка могла перейти на наступну сторінку (OnlyOffice інколи ігнорує cantSplit):
            # ознака — повтор шапки таблиці вгорі наступної сторінки
            nw = words[pg + 1]
            top = {t for x, y, t in nw if y < 95}
            if top & {"Продовження", "Закінчення", "Таблиця", "Рисунок"}:
                top = set()
            heads = [TOKEN.search(h).group(0) if TOKEN.search(h) else h.split()[0] for h in header_cells]
            if heads and sum(1 for h in heads if any(t.startswith(h[:6]) for t in top)) / len(heads) >= 0.8:
                found = len(cells) - 1
        if found < len(cells):
            bad.append((key, num, offset, offset + len(cells), offset + found if found >= 2 else None))
    return bad


def heading_pages(pages, entries):
    norm = lambda t: " ".join(t.split())                      # noqa: E731
    pg = [norm(t) for t in pages]
    cur = next((i for i, t in enumerate(pg) if t.startswith("ЗМІСТ") or " ЗМІСТ " in t[:40]), 0) + 1
    found = {}
    for _, label, bm in entries:
        key = norm(label.replace("РОЗДІЛ ", "РОЗДІЛ ", 1))[:50]
        if label.startswith("РОЗДІЛ "):
            key = label.split(" ", 2)[0] + " " + label.split(" ", 2)[1]
        elif label.startswith("Додаток "):
            key = label.split(".")[0]
        i = next((i for i in range(cur, len(pg)) if key in pg[i]), None)
        if i is not None:
            found[bm] = i + 1
            cur = i
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--pdf", action="store_true")
    a = ap.parse_args()
    spec_path = Path(a.spec).resolve()
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    out = (ROOT / spec["output"]).resolve()
    pages_map, breaks, cuts, tries, recut = {}, set(), {}, {}, False
    for attempt in range(60):
        b = Builder(spec, pages_map, breaks, cuts)
        b.build(out)
        if not a.pdf:
            break
        pdf = out.with_suffix(".pdf")
        subprocess.run([str(ROOT / "tools/docx2pdf.sh"), str(out), str(pdf)], check=True, capture_output=True)
        pages = pdf_pages(pdf)
        bad = [x for x in split_tables(pages, b.table_meta, pdf_words(pdf)) if x[0] not in breaks
               and tries.get(x[0], 0) < 3]
        if bad:
            # одна зміна за прохід: перша розірвана частина — розрізати на межі сторінки або перенести
            key, tnum, lo, hi, cut = bad[0]
            tries[key] = tries.get(key, 0) + 1
            if cut is not None and cut in cuts.get(tnum, []):   # без зрушення — ще на рядок раніше
                cut = cut - 1 if cut - 1 - lo >= 2 else None
            if cut is not None and hi - cut < 3:               # продовження — не менше трьох рядків
                cut = hi - 3 if hi - 3 - lo >= 2 else None
            if cut is not None:
                # кінець цієї частини переноситься на рядок, що не вмістився (замість додавання нового розрізу)
                cuts[tnum] = sorted((set(cuts.get(tnum, [])) - {hi}) | {cut})
                print(f"прохід {attempt + 1}: таблиця {tnum} продовжується з рядка {cut + 1}")
            else:
                breaks.add(key)
                # частина з’являється на новій сторінці — об’єднуємо її з наступною (розріз на кінці частини
                # був обчислений для старого положення); якщо разом не вмістяться, розріз знайдеться знову
                if hi in cuts.get(tnum, []):
                    cuts[tnum] = [c for c in cuts[tnum] if c != hi]
                print(f"прохід {attempt + 1}: частину {key} перенесено на нову сторінку")
            continue
        new = heading_pages(pages, b.toc_entries)
        if new == pages_map:
            if (cuts or breaks) and not recut:
                # розрізи, знайдені на ранніх проходах, могли застаріти (вміст вище зсунувся): обчислюємо їх
                # заново від першої таблиці, коли решта розмітки вже стабільна
                recut = True
                cuts.clear(), breaks.clear(), tries.clear()
                print(f"прохід {attempt + 1}: повторне розбиття таблиць")
                continue
            break
        print(f"прохід {attempt + 1}: оновлення номерів сторінок у змісті")
        pages_map = new
    meta = {"figures": b.figures_used, "toc": {lbl: pages_map.get(bm) for _, lbl, bm in b.toc_entries},
            "breaks": sorted(breaks), "cuts": cuts}
    (out.parent / "build_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"DOCX: {out}")
    if a.pdf:
        rest = split_tables(pdf_pages(out.with_suffix(".pdf")), b.table_meta, pdf_words(out.with_suffix(".pdf")))
        if rest:
            print(f"УВАГА: частини таблиць {rest} довші за сторінку — додайте continue_at")
        prev = out.parent / "preview"
        prev.mkdir(exist_ok=True)
        for old in prev.glob("page-*.png"):
            old.unlink()
        subprocess.run(["pdftoppm", "-png", "-r", "60", str(out.with_suffix(".pdf")), str(prev / "page")], check=True)
        print(f"PDF: {out.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
