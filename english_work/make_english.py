#!/usr/bin/env python3
"""Job Getting Course (ICT-31): builds the homework portfolio, the final résumé, the cover letter and the pitch
script from content.py → Англійська/Готово/*.docx + *.pdf, then verifies them (page counts, ATS keywords,
no leftover placeholders).

    .venv/bin/python english_work/make_english.py
"""
import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import content as C  # noqa: E402

SRC = ROOT / "Англійська"
OUT = SRC / "Готово"
FONT = "Arial"
NAVY, GREY, LIGHT = "1F3A68", "595959", "E9EEF5"
PHOTO = HERE / "photo_round.png"
IPA_FONT = "Calibri"  # the PDF converter misplaces Arial's stress mark ˈ (renders it as a dot over the next letter)


# ─────────────────────────────────────────── docx helpers ───────────────────────────────────────────
def new_doc(margin=2.0, size=11):
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.left_margin = s.right_margin = s.top_margin = s.bottom_margin = Cm(margin)
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(size)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st.element.rPr.rFonts.set(qn("w:cs"), FONT)
    st.paragraph_format.space_after = Pt(4)
    st.paragraph_format.line_spacing = 1.15
    doc.core_properties.author = C.STUDENT
    doc.core_properties.language = "en-GB"
    return doc


def runs(par, text, size=None, bold=False, italic=False, color=None):
    """Inline markup: **bold**, *italic*."""
    for tok in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not tok:
            continue
        b, i = bold, italic
        if tok.startswith("**"):
            tok, b = tok[2:-2], True
        elif tok.startswith("*") and len(tok) > 2:
            tok, i = tok[1:-1], True
        r = par.add_run(tok)
        r.bold, r.italic = b, i
        r.font.name = IPA_FONT if re.search("[ˈˌːəɪʊʌæɑɒɔʃʒθðŋɜ]", tok) else FONT
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
    return par


def para(doc, text="", size=None, bold=False, italic=False, color=None, align=None, before=0, after=4,
         indent=None, keep=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    if indent is not None:
        pf.left_indent = Cm(indent)
    if align:
        p.alignment = align
    if keep:
        pf.keep_with_next = True
    return runs(p, text, size, bold, italic, color)


def rule(p, color=NAVY, sz=8):
    pPr = p._element.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    for k, v in (("val", "single"), ("sz", str(sz)), ("space", "1"), ("color", color)):
        b.set(qn(f"w:{k}"), v)
    bdr.append(b)
    pPr.append(bdr)


def shade(cell, fill):
    tcPr = cell._element.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill)
    tcPr.append(sh)


def no_borders(table):
    tblPr = table._element.tblPr
    b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        x = OxmlElement(f"w:{e}"); x.set(qn("w:val"), "nil"); b.append(x)
    tblPr.append(b)


def cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    x = OxmlElement("w:cantSplit"); x.set(qn("w:val"), "true"); trPr.append(x)


def table(doc, header, rows, widths, size=10):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c, h, w in zip(t.rows[0].cells, header, widths):
        c.width = Cm(w)
        shade(c, NAVY)
        runs(c.paragraphs[0], h, size, bold=True, color="FFFFFF")
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trPr.append(th)
    for i, row in enumerate(rows):
        r = t.add_row()
        cant_split(r)
        for c, v, w in zip(r.cells, row, widths):
            c.width = Cm(w)
            if i % 2:
                shade(c, "F5F7FA")
            c.paragraphs[0].paragraph_format.space_after = Pt(0)
            runs(c.paragraphs[0], str(v), size)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def bullets(doc, items, numbered=False, size=None, indent=0.6):
    for i, it in enumerate(items, 1):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent, pf.first_line_indent = Cm(indent), Cm(-indent + 0.1)
        pf.space_after = Pt(2)
        pf.tab_stops.add_tab_stop(Cm(indent))
        runs(p, f"{i}.\t" if numbered else "•\t", size, bold=numbered, color=NAVY)
        runs(p, it, size)


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def hyperlink(par, url, text, size=None, color=NAVY):
    rid = par.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                             is_external=True)
    h = OxmlElement("w:hyperlink"); h.set(qn("r:id"), rid)
    r = OxmlElement("w:r"); rPr = OxmlElement("w:rPr")
    f = OxmlElement("w:rFonts"); f.set(qn("w:ascii"), FONT); f.set(qn("w:hAnsi"), FONT); rPr.append(f)
    c = OxmlElement("w:color"); c.set(qn("w:val"), color); rPr.append(c)
    if size:
        s = OxmlElement("w:sz"); s.set(qn("w:val"), str(int(size * 2))); rPr.append(s)
    r.append(rPr)
    t = OxmlElement("w:t"); t.text = text; t.set(qn("xml:space"), "preserve"); r.append(t)
    h.append(r)
    par._p.append(h)


def to_pdf(docx):
    subprocess.run(["bash", str(ROOT / "tools/docx2pdf.sh"), str(docx), str(docx.with_suffix(".pdf"))],
                   check=True, capture_output=True)
    return docx.with_suffix(".pdf")


def pages(pdf):
    return len(PdfReader(pdf).pages)


# ─────────────────────────────────────────────── photo ───────────────────────────────────────────────
def make_photo():
    """Round headshot cut from the photo embedded in the student's own Canva résumé."""
    if PHOTO.exists():
        return
    tmp = HERE / "_photo_src"
    tmp.mkdir(exist_ok=True)
    subprocess.run(["pdfimages", "-png", "-f", "1", "-l", "1", str(SRC / "Resume.pdf"), str(tmp / "i")], check=True)
    src = tmp / "i-000.png"
    subprocess.run(["magick", str(src), "-crop", "230x230+262+150", "+repage", "-resize", "460x460",
                    "(", "-size", "460x460", "xc:black", "-fill", "white", "-draw", "circle 230,230 230,2", ")",
                    "-alpha", "off", "-compose", "CopyOpacity", "-composite",
                    "-background", "white", "-compose", "Over", "-flatten", str(PHOTO)], check=True)
    for f in tmp.iterdir():
        f.unlink()
    tmp.rmdir()


# ─────────────────────────────────────────────── résumé ───────────────────────────────────────────────
def r_heading(doc, text):
    p = para(doc, text.upper(), size=13, bold=True, color=NAVY, before=5, after=2, keep=True)
    rule(p, NAVY, 8)


def build_resume():
    R = C.RESUME
    doc = new_doc(margin=1.6, size=10)
    doc.sections[0].top_margin = doc.sections[0].bottom_margin = Cm(1.3)
    doc.core_properties.title = f"{C.STUDENT} — Résumé"
    head = doc.add_table(rows=1, cols=2)
    no_borders(head)
    a, b = head.rows[0].cells
    a.width, b.width = Cm(3.6), Cm(14.2)
    a.paragraphs[0].add_run().add_picture(str(PHOTO), width=Cm(2.9))
    p = b.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    runs(p, R["name"], 24, bold=True, color="333333")
    p = b.add_paragraph(); p.paragraph_format.space_after = Pt(4)
    runs(p, R["title"], 14, bold=True, color=NAVY)
    p = b.add_paragraph(); p.paragraph_format.space_after = Pt(0)
    runs(p, f"{C.CITY}  •  {C.EMAIL}  •  {C.PHONE}", 10, color=GREY)
    p = b.add_paragraph(); p.paragraph_format.space_after = Pt(0)
    hyperlink(p, "https://www." + C.LINKEDIN, C.LINKEDIN, 10)
    for c in (a, b):
        c.vertical_alignment = 1  # center

    r_heading(doc, "Profile")
    para(doc, R["profile"], size=10, after=2).alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    r_heading(doc, "Experience & Projects")
    for e in R["experience"]:
        t = doc.add_table(rows=1, cols=2)
        no_borders(t)
        l, rr = t.rows[0].cells
        l.width, rr.width = Cm(14.4), Cm(3.4)
        l.paragraphs[0].paragraph_format.space_after = Pt(0)
        runs(l.paragraphs[0], e["head"], 11, bold=True, color="222222")
        runs(l.paragraphs[0], f"  |  {e['org']}", 10.5, color=GREY)
        rr.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        rr.paragraphs[0].paragraph_format.space_after = Pt(0)
        runs(rr.paragraphs[0], e["dates"], 10, bold=True, color=NAVY)
        bullets(doc, e["bullets"], size=10, indent=0.5)

    r_heading(doc, "Technical Skills")
    for k, v in R["skills"]:
        p = para(doc, "", size=10, after=1)
        runs(p, f"{k}: ", 10, bold=True, color=NAVY)
        runs(p, v, 10)

    r_heading(doc, "Education & Certifications")
    for deg, where in R["education"]:
        para(doc, deg, size=10.5, bold=True, after=0)
        para(doc, where, size=10, color=GREY, after=3)
    bullets(doc, R["certs"], size=10, indent=0.5)

    r_heading(doc, "Languages")
    p = para(doc, "", size=10, after=0)
    for i, (lang, lvl) in enumerate(R["languages"]):
        runs(p, ("   •   " if i else "") + f"{lang}: ", 10, bold=True)
        runs(p, lvl, 10)
    out = OUT / "Resume_Petro_Kravchenko.docx"
    doc.save(out)
    return out


# ───────────────────────────────────────────── cover letter ─────────────────────────────────────────────
def build_cover():
    L = C.COVER
    doc = new_doc(margin=2.5, size=11)
    doc.core_properties.title = f"{C.STUDENT} — Cover letter"
    para(doc, C.STUDENT, size=16, bold=True, color=NAVY, after=0)
    para(doc, f"{C.CITY}  •  {C.EMAIL}  •  {C.PHONE}", size=9.5, color=GREY, after=0)
    p = para(doc, C.LINKEDIN, size=9.5, color=GREY, after=10)
    rule(p, NAVY, 6)
    para(doc, L["date"], after=8)
    for line in L["to"]:
        para(doc, line, after=0)
    para(doc, f"**Re:** {L['re']}", before=8, after=10)
    para(doc, L["greeting"], after=8)
    for t in L["paras"]:
        p = para(doc, t, after=8)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.2
    para(doc, L["closing"], before=4, after=18)
    para(doc, C.STUDENT, bold=True, after=0)
    para(doc, "Enclosure: résumé", size=9.5, color=GREY, before=10)
    out = OUT / "Cover_letter_Petro_Kravchenko.docx"
    doc.save(out)
    return out


# ─────────────────────────────────────────────── pitch ───────────────────────────────────────────────
def words(text):
    return len(re.findall(r"[A-Za-z0-9'’+-]+", text))


def build_pitch():
    doc = new_doc(margin=2.5, size=13)
    doc.core_properties.title = f"{C.STUDENT} — Elevator pitch"
    para(doc, "Elevator pitch — video script", size=18, bold=True, color=NAVY, after=0)
    n = sum(words(t) for _, t in C.PITCH)
    p = para(doc, f"{C.STUDENT} · {C.GROUP} · Job Getting Course · {n} words ≈ "
                  f"{round(n / 130 * 60)}–{round(n / 115 * 60)} seconds", size=10, color=GREY, after=10)
    rule(p)
    for head, text in C.PITCH:
        para(doc, head, size=11, bold=True, color=NAVY, before=6, after=2, keep=True)
        p = para(doc, text, size=13, after=6)
        p.paragraph_format.line_spacing = 1.4
    para(doc, "Before you record", size=13, bold=True, color=NAVY, before=12, after=4, keep=True)
    bullets(doc, [
        "Camera at eye level, a plain background, light in front of you (a window or a lamp).",
        "Look into the camera, not at the screen; smile at the start and at the end.",
        "Speak slowly and make a short pause after each part (1 → 5).",
        "Stress the key words: **seven hundred** users, **Docker**, **Linux**, **Nginx**, **ISO 27001**.",
        "Pronunciation: faculty /ˈfæk.əl.ti/, Python /ˈpaɪ.θən/, architecture /ˈɑː.kɪ.tek.tʃə/.",
        "Record two or three takes and choose the best one; keep it under 90 seconds.",
    ], size=11)
    out = OUT / "Pitch_script_Petro_Kravchenko.docx"
    doc.save(out)
    return out, n


# ─────────────────────────────────────────────── workbook ───────────────────────────────────────────────
def resume_text(path):
    d = Document(path)
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            parts += [c.text for c in row.cells]
    return "\n".join(parts)


def ats_rows(text):
    rows = []
    for kw in C.ATS_KEYWORDS:
        hit = re.search(r"(?<![A-Za-z])" + re.escape(kw) + r"(?![A-Za-z])", text, re.I)
        rows.append((kw, bool(hit)))
    return rows


def build_workbook(resume_path):
    doc = new_doc(margin=2.0, size=11)
    doc.core_properties.title = f"{C.GROUP} Job Getting Course — Homework"
    # title page
    para(doc, "", after=90)
    para(doc, "JOB GETTING COURSE", size=13, bold=True, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER, after=6)
    para(doc, "Homework Portfolio", size=28, bold=True, color=NAVY, align=WD_ALIGN_PARAGRAPH.CENTER, after=6)
    p = para(doc, "Lessons 09/09/2026 – 28/10/2026", size=14, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER,
             after=60)
    for k, v in (("Student", C.STUDENT), ("Group", C.GROUP), ("Academic year", "2026–2027"),
                 ("Attached files", "Résumé · Cover letter · Pitch script")):
        p = para(doc, "", size=13, align=WD_ALIGN_PARAGRAPH.CENTER, after=4)
        runs(p, f"{k}: ", 13, bold=True, color=NAVY)
        runs(p, v, 13)
    page_break(doc)

    # contents + legend
    para(doc, "Contents", size=18, bold=True, color=NAVY, after=8)
    for i, (date, title, _) in enumerate(C.LESSONS, 1):
        p = para(doc, "", size=12, after=3)
        runs(p, f"Lesson {i}  ", 12, bold=True, color=NAVY)
        runs(p, f"{date} — {title}", 12)
    for t in ("Appendix A — Vocabulary bank with my examples", "Appendix B — Sources"):
        para(doc, t, size=12, bold=True, after=3)
    para(doc, "How to read this portfolio", size=13, bold=True, color=NAVY, before=14, after=4)
    bullets(doc, [
        "Grey boxes quote the teacher's task; my answer follows.",
        "**TO DO** boxes mark the few things that only I can do personally (a quiz, a form, the video, "
        "sending files).",
        "Video answers are based on what the speakers actually say in the videos; vacancies were checked on "
        f"Djinni on {C.ACCESSED}.",
    ])

    resume_txt = resume_text(resume_path)
    todo_count = 0
    for i, (date, title, blocks) in enumerate(C.LESSONS, 1):
        page_break(doc)
        p = para(doc, f"LESSON {i}  ·  {date}", size=10.5, bold=True, color=GREY, after=0)
        p = para(doc, title, size=18, bold=True, color=NAVY, after=8)
        rule(p, NAVY, 12)
        for kind, *rest in blocks:
            val = rest[0] if rest else None
            if kind == "h2":
                para(doc, val, size=13, bold=True, color=NAVY, before=10, after=4, keep=True)
            elif kind == "task":
                t = doc.add_table(rows=1, cols=1)
                c = t.rows[0].cells[0]
                shade(c, "EEEEEE")
                no_borders(t)
                c.paragraphs[0].paragraph_format.space_after = Pt(0)
                runs(c.paragraphs[0], "Task: ", 10, bold=True, color=GREY)
                runs(c.paragraphs[0], val, 10, italic=True, color=GREY)
                doc.add_paragraph().paragraph_format.space_after = Pt(0)
            elif kind == "p":
                para(doc, val, keep=val.rstrip("*").endswith(":"))
            elif kind in ("bullets", "num"):
                bullets(doc, val, numbered=kind == "num", indent=0.85 if len(val) > 9 else 0.6)
            elif kind == "table":
                table(doc, val, rest[1], rest[2])
            elif kind == "note":
                para(doc, "→ " + val, size=10, italic=True, color=GREY, after=4)
            elif kind == "todo":
                todo_count += 1
                t = doc.add_table(rows=1, cols=1)
                c = t.rows[0].cells[0]
                shade(c, "FFF4E5")
                c.paragraphs[0].paragraph_format.space_after = Pt(0)
                runs(c.paragraphs[0], "TO DO: ", 10.5, bold=True, color="B45309")
                runs(c.paragraphs[0], val, 10.5)
                doc.add_paragraph().paragraph_format.space_after = Pt(0)
            elif kind == "blank":
                for _ in range(val):
                    p = para(doc, "", after=10)
                    rule(p, "A6A6A6", 4)
            elif kind == "pitch":
                for head, text in C.PITCH:
                    p = para(doc, "", after=4, indent=0.3)
                    runs(p, head + "  ", bold=True, color=NAVY)
                    runs(p, text)
            elif kind == "ats":
                rows = ats_rows(resume_txt)
                found = [k for k, h in rows if h]
                miss = [k for k, h in rows if not h]
                half = (len(rows) + 1) // 2
                tbl = []
                for j in range(half):
                    a = rows[j]
                    b = rows[j + half] if j + half < len(rows) else ("", None)
                    tbl.append([a[0], "✓ yes" if a[1] else "✗ no", b[0],
                                "" if b[1] is None else ("✓ yes" if b[1] else "✗ no")])
                table(doc, ["Keyword", "In my résumé", "Keyword", "In my résumé"], tbl, [4.2, 3.8, 4.2, 3.8])
                para(doc, f"**Result:** {len(found)} of {len(rows)} keywords ({round(100 * len(found) / len(rows))}%). "
                          f"Missing: {', '.join(miss)}. I did not add the missing words artificially "
                          "(“keyword stuffing”): they are exactly the skills I am still learning — cloud, CI/CD "
                          "tools and infrastructure as code. Other ATS rules are met: one column, standard "
                          "headings, a readable font (Arial), PDF format and no images except the photo.")
            elif kind == "changes":
                table(doc, ["What", "Before", "After"], C.RESUME_CHANGES, [2.6, 6.0, 7.4], size=9.5)
            elif kind == "linkedin":
                for head, text in C.LINKEDIN_TALK:
                    p = para(doc, "", after=5)
                    runs(p, head + ("" if head.endswith("?") else ".") + " ", bold=True, color=NAVY)
                    runs(p, text)
                para(doc, "Words from 28/10 used in the talk: get the ball rolling, endorse, come rain or "
                          "shine, eager to learn.", size=10, italic=True, color=GREY)
            else:
                raise ValueError(kind)

    # Appendix A
    page_break(doc)
    p = para(doc, "Appendix A — Vocabulary bank with my examples", size=18, bold=True, color=NAVY, after=8)
    rule(p, NAVY, 12)
    for date, items in C.VOCAB:
        para(doc, f"Lesson of {date}", size=12, bold=True, color=NAVY, before=6, after=3, keep=True)
        table(doc, ["Word / phrase", "Meaning", "My example"], [[f"**{w}**", m, e] for w, m, e in items],
              [3.8, 4.4, 7.8], size=9.5)
    para(doc, "Pronunciation (Cambridge Dictionary)", size=12, bold=True, color=NAVY, before=6, after=3, keep=True)
    half = (len(C.PRONUNCIATION) + 1) // 2
    rows = []
    for j in range(half):
        a = C.PRONUNCIATION[j]
        b = C.PRONUNCIATION[j + half] if j + half < len(C.PRONUNCIATION) else ("", "")
        rows.append([f"**{a[0]}**", a[1], f"**{b[0]}**" if b[0] else "", b[1]])
    table(doc, ["Word", "IPA", "Word", "IPA"], rows, [3.0, 5.0, 3.0, 5.0], size=10)

    # Appendix B
    para(doc, "Appendix B — Sources", size=18, bold=True, color=NAVY, before=14, after=8, keep=True)
    for j, (name, url) in enumerate(C.SOURCES, 1):
        p = para(doc, f"{j}. {name}. ", size=10, after=2)
        hyperlink(p, url, url, 10)
        runs(p, f" (accessed {C.ACCESSED}).", 10)

    # footer page numbers
    sec = doc.sections[0]
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    runs(fp, f"{C.STUDENT} · {C.GROUP} · Job Getting Course · page ", 8.5, color=GREY)
    r = fp.add_run()
    for tag, txt in (("begin", None), (None, " PAGE "), ("end", None)):
        if tag:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), tag); r._r.append(e)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; r._r.append(e)
    r.font.size = Pt(8.5)
    out = OUT / "Homework_ICT-31_Petro_Kravchenko.docx"
    doc.save(out)
    return out, todo_count, ats_rows(resume_txt)


# ─────────────────────────────────────────────── checks ───────────────────────────────────────────────
BANNED = [r"\bTODO\b", r"\bXXX\b", r"lorem", r"\[\s*\]", r"\bteh\b", r"\s,", r"\.\.(?!\.)", r"[A-Za-z,.;]  +[a-z]",
          r"\bi\b(?!\.)"]


def lint(path):
    d = Document(path)
    texts = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            texts += [c.text for c in row.cells]
    bad = []
    for t in texts:
        for pat in BANNED:
            if re.search(pat, t):
                bad.append((pat, t[:90]))
        if re.search(r"[А-Яа-яЇїІіЄєҐґ]", t):
            bad.append(("cyrillic", t[:90]))
    return bad


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    make_photo()
    resume = build_resume()
    cover = build_cover()
    pitch, n_words = build_pitch()
    book, todos, ats = build_workbook(resume)
    problems = []
    for f in (resume, cover, pitch, book):
        pdf = to_pdf(f)
        bad = lint(f)
        if bad:
            problems += [f"{f.name}: {b}" for b in bad]
        print(f"{f.name}: {pages(pdf)} pages")
    for f, limit in ((resume, 1), (cover, 1), (pitch, 1)):
        if pages(f.with_suffix(".pdf")) > limit:
            problems.append(f"{f.name}: more than {limit} page(s)")
    if not 110 <= n_words <= 190:
        problems.append(f"pitch has {n_words} words — keep it 60–90 s")
    hit = sum(h for _, h in ats)
    print(f"pitch: {n_words} words; ATS keywords: {hit}/{len(ats)}; TO DO items: {todos}")
    if problems:
        raise SystemExit("PROBLEMS:\n  " + "\n  ".join(map(str, problems)))
    print("OK →", OUT)


if __name__ == "__main__":
    main()
