# CLAUDE.md — ПІС (Проєктування інформаційних систем) course project

## 1. Project overview
- **Student:** Петро Кравченко, гр. ІР-31, КНУ ім. Тараса Шевченка, ФІТ, кафедра інформаційних систем та технологій.
- **Instructor / lecturer:** к.т.н. Гладка Мирослава Вікторівна (lectures `ПІС_*.pdf` are hers — her terminology wins).
- **Theme (verbatim from `My_theme.txt`):** «Проєктування розподіленої IoT-системи обміну телеметрією та координації
  дронів-перехоплювачів».
- **Domain model:** fictional organisation **РЦПДО «Щит-Північ»** (regional counter-drone defence centre) and the
  designed system **IoT-платформа «Щит-Лінк»**. All facts, actors (R-xx, S-xx), processes (BP-xx), entities (E-xx),
  architecture and the EN↔UA glossary live in **`DOMAIN_KNOWLEDGE_BASE.md` — read it before any lab work** and never
  invent conflicting names.
- **Scope guard:** model the *information system* (data, roles, processes, software architecture). No flight-control,
  guidance, warhead or EW-technique details. Engagements are always human-authorised.

## 2. Language mandate
- Conversation with the user (terminal): **English**.
- Deliverables (`.docx` reports, diagram labels, captions, tables): **formal Ukrainian only**, ДСТУ 3008:2015
  styling, lecture terminology (KB §8). No Russian letters or calques, no English placeholders.

## 3. Quality directives
- Depth over speed. Every lab must cover **every item of the "Завдання" list** of `лбN.docx`, in order.
- **Diagram legibility is non-negotiable:** effective text size in Word ≥ 10 pt (target ≈ 12–13 pt), ≥ 300 dpi,
  no rotated text, no overlaps. Split large models into overview + detail figures. Landscape sections for wide
  figures are automatic. The instructor's own sample figures (лб1 Рис. 2.6–2.7) are an anti-example.
- The user does **not** edit files manually — rendering, fixing, assembling and verifying is our job.
- Before reporting "done": automated check PASS + visual inspection of every preview page + compliance checklist.

## 4. File index
| Path | What |
|---|---|
| `My_theme.txt` | project theme (used in report body; title-page «Тема» = lab assignment title, see §8) |
| `Титульна сторінка для лб.docx` | official title page template — **never modify**; builder copies it |
| `лб1.docx`, `лб2.docx`, `лб3.docx` | lab briefs: ЛР1 goal tree + WBS; ЛР2 BPMN; ЛР3 AllFusion PM: IDEF0/IDEF3/FEO/node tree |
| `ПІС_1.pdf` … `ПІС_8_9_*.pdf` | lectures: 1 basics/ДСТУ stages/structuring; 2 planning, goal tree rules, WBS; 3 BPMN; 4 IDEF0 rules; 5 IDEF3 & DFD; 6 UML; 7 architecture & IoT 4-level; 8–9 infrastructure, SCADA/АСК ТП, CPS, MAS, security |
| `Корисна інфа 1–5.pdf` | textbooks: Марченко 2015; Пістунов 2008 (report rules: TNR 14, 1.5; DFD Gane–Sarson/Yourdon); Ременяк 2016 (ГОСТ 34 stages, standards); Ізмайлова 2022 (UML, report contents); Коваленко & Добровська 2020 (ЖЦ, ДСТУ ISO/IEC 12207) |
| `DOMAIN_KNOWLEDGE_BASE.md` | domain reference (single source of truth) |
| `tools/mmd_render.py` | Mermaid → SVG/PNG + legibility/DPI gate → `*.layout.json` |
| `tools/mermaid-config.json` | diagram theme (Times New Roman 20 px, monochrome, no shadows) |
| `tools/build_report.py` | YAML spec → .docx (title page fill, sections, numbering, landscape, previews) |
| `tools/check_report.py` | automated compliance checks of a built .docx |
| `tools/bpmn_model.py`, `tools/bpmn/` | BPMN 2.0 generator (grid layout + DI) and bpmn-js renderer (node, puppeteer-core); legibility gate |
| `tools/idef_model.py` | IDEF0 / IDEF3 / node-tree renderer (AFPM-style frame, ICOM routing, squiggle label placer, tunnels, call arrows, FEO) → SVG/PNG + legibility gate |
| `tools/docx2pdf.sh` | headless .docx → .pdf via OnlyOffice x2t (no LibreOffice on this machine) |
| `.claude/skills/diagram-generator/` | diagram workflow skill |
| `.claude/skills/academic-report-builder/` | report assembly skill |
| `.claude/skills/curriculum-compliance-reviewer/` | pre-submission audit skill |
| `labN/` | per-lab workspace: `report.yaml`, `diagrams/*.mmd`, output `ЛРN_Кравченко_ІР-31.docx`, `preview/` |

## 5. Environment
- Python venv: `.venv/` (python-docx, lxml, Pillow, PyYAML, pypdf). Always call `.venv/bin/python`.
- Node packages for BPMN rendering: `tools/bpmn/node_modules` (bpmn-js 18, puppeteer-core) — `npm install` in
  `tools/bpmn/` if missing; uses the Chrome Headless Shell from `~/.cache/puppeteer`.
- Mermaid CLI: `mmdc` 12 (system, Chrome headless via puppeteer cache).
- PDF/raster: `pdftotext`, `pdftoppm`, `magick`. OnlyOffice converter `/opt/onlyoffice/desktopeditors/converter/x2t`
  with font cache `~/.local/share/onlyoffice/desktopeditors/data/fonts/AllFonts.js`.
- zsh quirk: don't start an `echo` argument with `=` (zsh `=cmd` expansion).

## 6. Workflow per lab (step by step)
1. Read `лбN.docx` (tasks, theory, sample), relevant lectures, KB sections (KB §7 maps labs → content).
2. Write a WBS/plan of the report (task item → subsection → tables/figures).
3. Diagrams — skill **diagram-generator**: write `labN/diagrams/NN_slug.mmd`, run
   `.venv/bin/python tools/mmd_render.py labN/diagrams/NN_slug.mmd`, fix until exit 0, `Read` the PNG to verify.
4. Content — write `labN/report.yaml` in Ukrainian (skill **academic-report-builder** §3 for syntax).
5. Build: `.venv/bin/python tools/build_report.py labN/report.yaml --pdf`; inspect `labN/preview/page-*.png`.
6. Check: `.venv/bin/python tools/check_report.py labN/ЛРN_Кравченко_ІР-31.docx --spec labN/report.yaml`;
   then skill **curriculum-compliance-reviewer** checklist. Fix → rebuild → recheck.
7. Report to the user in English: what was produced, checks passed, any assumptions.

## 7. Lab map (what each brief demands)
- **ЛР1** — Вибір об'єкту дослідження; задачі автоматизації; дерево цілей; WBS. Tasks: (1) тема; (2) загальні
  відомості про підприємство; (3) структурна схема; (4) роботи підрозділу; (5) функції та задачі; (6) таблиця
  функціональних взаємозв'язків; (7) задачі для автоматизації; (8) вершини дерева цілей; (9) підхід до побудови;
  (10) дерево цілей; (11) робоча структура проекту; (12) етапи розробки WBS; (13) аналіз характеристик проекту;
  (14) схематичне WBS зображення.
- **ЛР2** — BPMN model of the organisation; each function as a separate pool; analysis of pools/lanes/interactions.
  Done: `lab2/make_lab2.py` (5 functional pools P1–P5 + interaction map, 8 `.bpmn` diagrams, analysis computed
  from the model).
- **ЛР3** — done: `lab3/model3.py` (model data) + `lab3/make_lab3.py` (10 diagrams, report). IDEF0 context + decomposition, model report, node tree, FEO, split/merge, IDEF3 + scenario (AFPM-style;
  we reproduce diagrams faithfully with Mermaid and describe the tool steps).

## 8. Operational rules for future sessions
- **Formatting rules (2026-10-03, see academic-report-builder §4a):** dot after heading numbers; new page before
  Хід виконання / each numbered section / Висновки; tables never split (layout loop + `continue_at`); one-sentence
  «Примітка» disclaimer.
- **User decisions (2026-10-03):** title-page «Тема» = name of the lab assignment (spec `theme:`); fictional
  organisation is declared in one concise «Примітка» sentence (not a legal disclaimer); figures inline where the brief
  demands them, always legible.
- Keep cross-lab consistency: same unit names, process codes, entity names (KB). Update KB first if the model changes.
- Don't commit generated previews/PDFs unless asked; commit sources (`.mmd`, `.yaml`, tools) and final `.docx`.
- Never overwrite the title template, lab briefs or lecture files.
- Git: commit only when the user asks; branch off `main` first.
- If a tool fails twice for the same reason, diagnose root cause (paths with Cyrillic, fonts, mmdc syntax) instead
  of retrying blindly.
