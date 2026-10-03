---
name: academic-report-builder
description: Builds a complete ПІС laboratory report (.docx, formal Ukrainian, ДСТУ 3008:2015 styling) from the official title page template and a YAML content spec — fills the title page (lab number, theme from My_theme.txt, year), appends Мета роботи / Короткі теоретичні відомості / Хід виконання роботи / Графічна частина / Висновки, auto-numbers figures and tables, embeds diagrams at legible size with automatic landscape sections, renders a PDF preview for visual QA. Use for every lab deliverable.
allowed-tools: Bash, Read, Write, Edit
---

# Academic Report Builder

All report assembly is programmatic (`python-docx`) — the user never touches the .docx.

## 1. Inputs
- `Титульна сторінка для лб.docx` — official title page. **Never modify the template file itself.** The builder
  opens it as the base document, so margins (L 3 cm, R 1.5 cm, T/B 2 cm), Times New Roman 14 pt, paragraph geometry
  and student/teacher block are preserved byte-for-byte except the three placeholders:
  - `Лабораторна робота № __` → lab number (bold);
  - `Тема: «___»` → **the lab assignment title** from `лбN.docx` (user decision 2026-10-03), set via `theme:` in
    the spec; the project theme from `My_theme.txt` appears in the body (Мета роботи, 3.1);
  - `Київ-2025` → `Київ-<current year>`.
- `labN/report.yaml` — content spec you write (Ukrainian text).
- `labN/diagrams/*.mmd` — diagram sources (see skill `diagram-generator`).
- `DOMAIN_KNOWLEDGE_BASE.md` — the only source of domain facts/names. Lecture PDFs — source of theory and terminology.

## 2. Build command
```bash
.venv/bin/python tools/build_report.py labN/report.yaml --pdf
.venv/bin/python tools/check_report.py labN/<output>.docx --spec labN/report.yaml
```
`--pdf` converts via OnlyOffice `x2t` (`tools/docx2pdf.sh`, no LibreOffice installed) and writes
`labN/preview/page-*.png` at 70 dpi. **Always look at every preview page** with `Read` before declaring done:
check title page unchanged except placeholders, no orphan headings, figures not cut, captions under figures,
landscape pages correct, tables not overflowing, page numbers from page 2.

## 3. YAML spec reference
```yaml
lab_number: 1
theme: "Вибір об’єкту дослідження. …"           # lab title → title-page «Тема»
output: lab1/ЛР1_Кравченко_ІР-31.docx      # relative to project root
year: 2026                                  # optional
blocks:
  - h1: Мета роботи                         # rendered UPPERCASE, bold, centred
  - p: |                                    # paragraph(s); blank line = new paragraph
      Текст з **жирним**, *курсивом* і посиланням на рис. {fig:goal_tree} та табл. {tab:functions}.
  - h2: "3. Загальні відомості про підприємство"   # bold, left; a dot after the number is enforced
    new_page: true                          # major numbered sections + Висновки start on a new page
  - h3: Підпункт                            # bold italic
  - bullets: [пункт; , пункт.]              # rendered "– пункт"
  - numbered: [пункт, пункт]                # rendered "1) пункт"
  - table:
      id: functions                         # for {tab:functions}
      caption: Задачі та функції підрозділів РЦПДО «Щит-Північ»
      header: [№, Підрозділ, Задачі, Функції]
      widths: [1, 4, 5, 8]                  # relative
      font: 12                              # 12 pt allowed in tables
      continue_at: [20]                     # long table: rows 20.. go to "Продовження таблиці N.k" on a new page
      rows:
        - ["1", "Командний пункт", "…", ["рядок 1", "рядок 2"]]   # list = line breaks in cell
  - figure:
      id: goal_tree
      src: lab1/diagrams/03_goal_tree_overview.mmd   # .mmd (preferred) or .png
      caption: Дерево цілей IoT-платформи «Щит-Лінк» (рівні 0–1)
      orientation: auto                     # auto | portrait | landscape
      note: "Примітка: …"                   # optional, 12 pt italic under caption
  - pagebreak: true
```
Numbering is automatic: "Таблиця 1.3 — …" (above table, left), "Рис. 1.4 — …" (below figure, centred). Header rows
repeat on page breaks; rows do not split. Unknown `{fig:…}`/`{tab:…}` ids abort the build — fix the spec.

## 4. Mandatory report structure (department practice + Ізмайлова 2022 §2.4 + лабораторні методички)
1. Титульна сторінка (template).
2. **МЕТА РОБОТИ** — quote/paraphrase the goal from `лбN.docx`, adapted to the theme.
3. **КОРОТКІ ТЕОРЕТИЧНІ ВІДОМОСТІ** — 1–3 pages, own words, cite lecture concepts and terms (e.g. "згідно з
   лекцією «Моделювання IDEF0» …"), definitions of notations used, rules the diagrams follow. No copy-paste of
   textbooks (Пістунов: "не допускається переписування з літератури … визначень").
4. **ХІД ВИКОНАННЯ РОБОТИ** — one numbered subsection per task item of `лбN.docx` ("Завдання" list), in the same
   order, each with explanatory text + tables; every figure/table referenced in text before it appears.
5. **ГРАФІЧНА ЧАСТИНА** — diagrams with captions. Option A (preferred for readability): figures inline in the
   relevant subsection of "Хід виконання роботи" and the "Графічна частина" section lists/briefly comments the
   figures. Option B: all figures here. Keep one option per report.
6. **ВИСНОВКИ** — answer each item of "Мета" explicitly, quantified (кількість рівнів дерева, кількість робочих
   пакетів, виявлені задачі автоматизації тощо). 0.5–1 page.
7. Optional: **ВІДПОВІДІ НА КОНТРОЛЬНІ ПИТАННЯ** if the user asks; **СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ** (ДСТУ 8302:2015 style)
   — lectures, textbooks from `Корисна інфа`, standards.

## 4a. Formatting rules fixed by the user (2026-10-03) — enforced by builder + checker
- **Disclaimer:** exactly one concise sentence in "Вибір об’єкту дослідження" (italic), no legalistic text:
  «Примітка: РЦПДО «Щит-Північ» є навчальною умовною моделлю організації; усі назви, процеси та структури наведено
  суто з навчально-ілюстративною метою для проєктування інформаційної системи.» Table "Загальні відомості" →
  «Статус: Навчальна умовна модель організації».
- **Title page unnumbered:** section 1 has "Different First Page" with explicitly empty first/default headers and
  footers; the body section carries the PAGE field (title counted as 1 → body numbered from 2). Checker enforces.
- **Heading numbers always end with a dot:** "5. Функції…", "1.1. …" (builder normalises, checker fails otherwise).
- **New page** (`new_page: true`) before "Хід виконання роботи" (section 1 follows on the same page), before every
  numbered section 2…N, before "Висновки" and before "Список використаних джерел" (isolated last page).
- **ЗМІСТ** (default `toc: true`): page 2, native `TOC \o "1-3" \h \z \u` field over Heading 1/2 styles (headings
  are real Heading styles, normalised to TNR 14 black, with `_Toc` bookmarks). The field result is pre-filled with
  hyperlinked entries + PAGEREF numbers taken from the rendered PDF (layout loop), so it is correct on opening in
  OnlyOffice/Word and can be regenerated via "Оновити поле/зміст". The body starts on the next page.
- **Tables never break awkwardly:** every row has `<w:cantSplit/>`, header `<w:tblHeader/>`, rows chained with
  keep-with-next. OnlyOffice (the user's editor) ignores these inside tables, so `build_report.py --pdf` runs a
  layout loop: render → detect split tables (last row off the caption page or header repeated on the next page) →
  page break before the caption → rebuild. Tables longer than a page must use `continue_at` («Продовження таблиці»).

## 5. Ukrainian academic style rules
- Formal impersonal style: "розроблено", "визначено", "у роботі побудовано"; avoid "я", "ми зробили".
- Use «ялинки» quotes, em dash " — " in captions, apostrophe ’ (U+2019) in words like "об’єкт".
- Terms exactly as in lectures (see KB §8): "контекстна діаграма", "стрілка-механізм", "пул", "доріжка",
  "дерево цілей", "ієрархічна структура робіт (WBS)", "робочий пакет", "прецедент", "актор".
- Abbreviations defined at first use: "безпілотний літальний апарат (БпЛА)".
- Numbers: decimal comma (0,95), units with non-breaking space (25 км, 2 с).
- No Russian letters/calques ("приймати участь" ✗ → "брати участь" ✓; "на протязі" ✗ → "протягом" ✓;
  "являється" ✗ → "є" ✓; "слідуючий" ✗ → "наступний" ✓; "згідно з" ✓).

## 6. Layout rules
- Body: Times New Roman 14 pt, 1.5 spacing, first-line indent 1.25 cm, justified. Tables: 12 pt, single spacing.
- Portrait text width 16.5 cm; landscape sections (margins L/R 2 cm, T 3 cm, B 1.5 cm → 25.7 × 14.5 cm box) are
  inserted automatically for figures whose `layout.json` says landscape, and the document returns to portrait
  automatically for the next text block.
- Wide tables (> 5 columns or long text) → `orientation: landscape` on the table block.
- Page numbers: bottom centre, from page 2 (title page unnumbered).
- File name: `labN/ЛРN_Кравченко_ІР-31.docx`.

## 7. Done criteria
`check_report.py` prints `RESULT: PASS` (WARNs reviewed and either fixed or justified), every preview page visually
inspected, `curriculum-compliance-reviewer` checklist completed for this lab.
