#!/usr/bin/env python3
"""Титульна сторінка дисципліни «Теорія систем»: копія ПІС-шаблону (оригінал не змінюється) з назвою дисципліни,
номером варіанта (вимога п. 4.1 методичних вказівок) і порожнім рядком для викладача.
    .venv/bin/python ts_work/make_template.py
"""
from pathlib import Path
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Титульна сторінка для лб.docx"
DST = ROOT / "Теорія систем" / "Титульна сторінка для лб.docx"
SUBJECT, VARIANT = "Теорія систем", 8


def set_runs(p, *texts):
    for r, t in zip(p.runs, list(texts) + [""] * len(p.runs)):
        r.text = t


d = Document(SRC)
ps = d.paragraphs
assert ps[6].text.startswith("з дисципліни") and "Перевірив" in ps[14].text and "Гладка" in ps[16].text
set_runs(ps[6], "з дисципліни ", "«", "", SUBJECT, "", "»")
ps[7].runs[0].text = f"Варіант № {VARIANT}\n"
ps[7].runs[0].bold = True
set_runs(ps[16], "___________________________  ")
d.save(DST)
print("→", DST.relative_to(ROOT))

# Практичні роботи: той самий титул, але «Практична робота № __» (build_report шукає саме цей підпис)
assert ps[5].runs[0].text == "Лабораторна робота № "
ps[5].runs[0].text = "Практична робота № "
DST_PR = DST.with_name("Титульна сторінка для практичних.docx")
d.save(DST_PR)
print("→", DST_PR.relative_to(ROOT))
