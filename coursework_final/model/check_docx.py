#!/usr/bin/env python3
"""Автоматична перевірка оформлення пояснювальної записки (REQUIREMENTS.md, розд. D)."""
import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import Cm

DOC = Path(__file__).resolve().parents[1] / "КР_Кравченко_ІР-31.docx"
d = Document(str(DOC))
err = []
for i, s in enumerate(d.sections):
    port = s.page_width < s.page_height
    exp = (3.0, 1.0, 2.0, 2.0) if port else (2.0, 2.0, 3.0, 1.0)
    got = tuple(round(x / Cm(1), 2) for x in (s.left_margin, s.right_margin, s.top_margin, s.bottom_margin))
    if got != exp:
        err.append(f"розділ {i}: поля {got} ≠ {exp}")
    # номер сторінки: на книжкових сторінках — верхній колонтитул (праворуч), на альбомних — нижній (правий нижній
    # кут альбомної сторінки є правим верхнім кутом переплетеного аркуша)
    hf = s.header if port else s.footer
    if i and not any("PAGE" in el.text for el in hf._element.iter() if el.text) and not hf.is_linked_to_previous:
        err.append(f"розділ {i}: немає номера сторінки")
fonts, sizes, body = set(), set(), 0
for p in d.paragraphs:
    for r in p.runs:
        if r.text.strip():
            fonts.add(r.font.name); sizes.add(r.font.size.pt if r.font.size else None)
    t = p.text
    if re.search(r"[ыэъёЫЭЪЁ]", t):
        err.append(f"російські літери: {t[:60]}")
    if p.alignment == 3 and t.strip():          # основний текст за шириною
        body += 1
        pf = p.paragraph_format
        if round(pf.first_line_indent / Cm(1), 2) not in (1.25,) or pf.line_spacing != 1.5:
            err.append(f"абзац: відступ/інтервал — {t[:50]}")
print("шрифти:", fonts, "кеглі:", sorted(x for x in sizes if x))
print("абзаців основного тексту:", body)
bad_fonts = fonts - {"Times New Roman", "Courier New"}
if bad_fonts:
    err.append(f"інші шрифти: {bad_fonts}")
for e in err:
    print("ПОМИЛКА:", e)
print("помилок:", len(err))
sys.exit(1 if err else 0)
