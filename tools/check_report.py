#!/usr/bin/env python3
"""Automated compliance checks for a built ПІС lab report (.docx).

Usage: .venv/bin/python tools/check_report.py <report.docx> [--lab N] [--spec labN/report.yaml]

Checks (FAIL = must fix, WARN = review):
  * title page filled (no "__" placeholders, lab number, theme, current year)
  * required sections present: Мета роботи, Короткі теоретичні відомості, Хід виконання роботи,
    Графічна частина (or figures inside Хід виконання), Висновки
  * body font Times New Roman, 14 pt for paragraphs; tables 12–14 pt
  * figures and tables numbered consecutively "Рис. N.k — ", "Таблиця N.k — "
  * every figure/table is referenced in text at least once ("рис. N.k" / "табл. N.k" / "таблиці N.k")
  * no Latin-only placeholder words (User, Manager, Item1, ProcessData, TODO, Lorem)
  * no Russian-specific letters (ы, э, ъ, ё) in body text
  * every embedded diagram (from spec) passed the legibility gate (layout.json legible = true, font_pt >= 10)
"""
import argparse, datetime, json, re, sys
from pathlib import Path

import yaml
from docx import Document

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["МЕТА РОБОТИ", "КОРОТКІ ТЕОРЕТИЧНІ ВІДОМОСТІ", "ХІД ВИКОНАННЯ РОБОТИ", "ВИСНОВКИ"]
PLACEHOLDERS = re.compile(r"\b(User|Manager|Item\d*|ProcessData|TODO|TBD|Lorem|Foo|Bar|XXX)\b")
RUSSIAN = re.compile(r"[ыэъёЫЭЪЁ]")

fails, warns = [], []


def fail(m): fails.append(m)
def warn(m): warns.append(m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx")
    ap.add_argument("--lab", type=int)
    ap.add_argument("--spec")
    a = ap.parse_args()
    doc = Document(a.docx)
    paras = doc.paragraphs
    texts = [p.text for p in paras]
    full = "\n".join(texts)

    # --- title page
    title_zone = "\n".join(texts[:25])
    if re.search(r"№\s*_+|«_+»", title_zone):   # signature line "____" is legitimate
        fail("Title page still contains lab-number/theme placeholders")
    year = datetime.date.today().year
    if f"Київ-{year}" not in title_zone:
        warn(f"Title page year is not Київ-{year}")
    m = re.search(r"Лабораторна робота №\s*(\d+)", title_zone)
    lab = a.lab or (int(m.group(1)) if m else None)
    if not m:
        fail("Lab number missing on title page")
    theme = (ROOT / "My_theme.txt").read_text(encoding="utf-8").strip().splitlines()[0]
    if a.spec:
        theme = yaml.safe_load(Path(a.spec).read_text(encoding="utf-8")).get("theme") or theme
    if " ".join(theme.split()) not in " ".join(title_zone.split()):
        fail("Expected «Тема» text not found on title page")
    if "гіпотетичн" not in full and "умовн" not in full:
        fail("No hypothetical-organisation disclaimer (умовна/гіпотетична організація) in the report")

    # --- sections
    upper = [t.strip().upper() for t in texts]
    for sec in REQUIRED:
        if sec not in upper:
            fail(f"Missing section heading: {sec}")
    if "ГРАФІЧНА ЧАСТИНА" not in upper:
        warn("No 'ГРАФІЧНА ЧАСТИНА' heading (OK only if all figures are inside 'Хід виконання роботи')")

    # --- fonts (body after title page)
    body_start = next((i for i, t in enumerate(upper) if t == "МЕТА РОБОТИ"), 25)
    bad_font = set()
    for p in paras[body_start:]:
        for r in p.runs:
            if r.text.strip() and r.font.name not in (None, "Times New Roman"):
                bad_font.add(r.font.name)
    if bad_font:
        fail(f"Non-Times fonts in body: {sorted(bad_font)}")
    small = [p.text[:40] for p in paras[body_start:]
             if p.runs and p.text.strip() and not p.text.startswith(("Рис.",))
             and any(r.font.size and r.font.size.pt < 14 for r in p.runs if r.text.strip())
             and p.style.name != "Footer"]
    if small:
        warn(f"{len(small)} body paragraph(s) below 14 pt, e.g. {small[:2]}")

    # --- figure/table numbering & references
    figs = re.findall(r"^Рис\. (\d+)\.(\d+) — ", full, re.M)
    tabs = re.findall(r"^Таблиця (\d+)\.(\d+) — ", full, re.M)
    for kind, items in (("Рис.", figs), ("Таблиця", tabs)):
        nums = [int(k) for _, k in items]
        if nums != list(range(1, len(nums) + 1)):
            fail(f"{kind} numbering not consecutive: {nums}")
        if lab and any(int(l) != lab for l, _ in items):
            fail(f"{kind} chapter number differs from lab {lab}")
    body_text = "\n".join(t for t in texts if not re.match(r"^(Рис\.|Таблиця) \d", t))
    ranged = set()                      # "рис. 1.4–1.8" references every figure in the range
    for l1, n1, l2, n2 in re.findall(r"(?:рис\.|рисунк\w*)\s*(\d+)\.(\d+)\s*[–-]\s*(\d+)\.(\d+)", body_text, re.I):
        ranged.update((l1, str(x)) for x in range(int(n1), int(n2) + 1))
    for grp in re.findall(r"(?:рис\.|рисунк\w*)\s*((?:\d+\.\d+(?:\s*,\s*|\s+і\s+)?)+)", body_text, re.I):
        ranged.update(tuple(x.split(".")) for x in re.findall(r"\d+\.\d+", grp))
    for l, k in figs:
        if (l, k) not in ranged and not re.search(rf"(рис\.|рисунк\w*)\s*{l}\.{k}\b", body_text, re.I):
            warn(f"Рис. {l}.{k} is never referenced in the text")
    for l, k in tabs:
        if not re.search(rf"(табл\.|таблиц\w*)\s*{l}\.{k}\b", body_text, re.I):
            warn(f"Таблиця {l}.{k} is never referenced in the text")

    # --- language hygiene
    table_text = "\n".join(c.text for t in doc.tables for row in t.rows for c in row.cells)
    for name, txt in (("body", full), ("tables", table_text)):
        ph = sorted(set(PLACEHOLDERS.findall(txt)))
        if ph:
            fail(f"Generic placeholder words in {name}: {ph}")
        ru = RUSSIAN.findall(txt)
        if ru:
            fail(f"Russian-specific letters in {name}: {sorted(set(ru))}")

    # --- figures legibility (from spec)
    if a.spec:
        spec = yaml.safe_load(Path(a.spec).read_text(encoding="utf-8"))
        for b in spec["blocks"]:
            f = b.get("figure")
            if not f or not str(f["src"]).endswith((".mmd", ".bpmn")):
                continue
            lj = (ROOT / f["src"]).with_suffix(".layout.json")
            if not lj.exists():
                fail(f"No layout.json for {f['src']} (diagram not rendered through tools/mmd_render.py)")
                continue
            L = json.loads(lj.read_text(encoding="utf-8"))
            o = f.get("orientation", "auto")
            o = L["orientation"] if o == "auto" else o
            if L[o]["font_pt"] < 10:
                fail(f"{f['src']}: text would be {L[o]['font_pt']} pt in {o}")
            if L[o]["dpi"] < 300:
                warn(f"{f['src']}: {L[o]['dpi']} dpi in {o}")

    # --- heading numbering: "N." / "N.M." with a dot (department rule)
    from docx.oxml.ns import qn
    for par in paras[body_start:]:
        t = par.text.strip()
        if par.runs and all(r.bold for r in par.runs if r.text.strip()) and re.match(r"^\d+(\.\d+)*\s", t):
            fail(f"Heading number without dot: '{t[:40]}'")
    # --- major sections start on a new page
    for par in paras[body_start:]:
        t = par.text.strip()
        bold = par.runs and all(r.bold for r in par.runs if r.text.strip())
        major = t in ("ХІД ВИКОНАННЯ РОБОТИ", "ВИСНОВКИ", "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ") or (bold and re.match(r"^([2-9]|1\d)\.\s", t))
        if major and not par.paragraph_format.page_break_before:
            fail(f"Major section not on a new page: '{t[:40]}'")
    # --- tables: every row cantSplit, header repeated
    for ti, tb in enumerate(doc.tables, 1):
        rows = tb.rows
        hdr = rows[0]._tr.trPr if rows else None
        if hdr is None or hdr.find(qn("w:tblHeader")) is None:
            fail(f"Table {ti}: header row not marked <w:tblHeader/>")
        for r in rows:
            if r._tr.trPr is None or r._tr.trPr.find(qn("w:cantSplit")) is None:
                fail(f"Table {ti}: row without <w:cantSplit/>"); break

    # --- table of contents: native TOC field + headings carry Heading styles (indexed by the field)
    body_xml = doc.element.body.xml
    if 'TOC \\o "1-3"' not in body_xml:
        fail("No native TOC field (ЗМІСТ) found")
    if "ЗМІСТ" not in texts[:40]:
        fail("No 'ЗМІСТ' page after the title page")
    for par in paras[body_start:]:
        t = par.text.strip()
        if t in REQUIRED or re.match(r"^\d+\.\s", t) and par.runs and all(r.bold for r in par.runs if r.text.strip()):
            if not par.style.name.startswith("Heading"):
                fail(f"Heading not in a Heading style (missing from TOC): '{t[:40]}'")

    # --- title page: Different First Page, no page number in any of its headers/footers; body numbered
    t_sec, b_sec = doc.sections[0], (doc.sections[1] if len(doc.sections) > 1 else None)
    if not t_sec.different_first_page_header_footer:
        fail("Title section lacks 'Different First Page'")
    for hf in (t_sec.first_page_footer, t_sec.footer, t_sec.first_page_header, t_sec.header):
        if not hf.is_linked_to_previous and "PAGE" in hf._element.xml:
            fail("Page number field on the title page")
    if b_sec is None or "PAGE" not in b_sec.footer._element.xml:
        fail("Body footer has no PAGE field")

    # --- inline images count vs captions
    n_img = len(doc.inline_shapes)
    if n_img != len(figs):
        warn(f"{n_img} images but {len(figs)} figure captions")

    print(f"Checked {a.docx}: {len(figs)} figures, {len(tabs)} tables, {len(paras)} paragraphs")
    for w in warns: print("WARN:", w)
    for f in fails: print("FAIL:", f)
    print("RESULT:", "PASS" if not fails else "FAIL")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
