# CLAUDE.md — two independent course tracks (ПІС + «Технології створення програмних продуктів»)

## 0. Tracks — read first
| | Track 1 | Track 2 |
|---|---|---|
| Course | ПІС — Проєктування інформаційних систем | «Технології створення програмних продуктів» (always the full name, never abbreviated in deliverables) |
| Work type | Лабораторні роботи (ЛР1…ЛР7) | Практичні роботи (ПР1…ПР4) |
| Instructor | к.т.н. Гладка М. В. | к.т.н., доц. Кравченко Ольга Віталіївна |
| Theory sources | `ПІС_*.pdf`, `Корисна інфа 1–5.pdf`, `лбN.docx` | **only** files in `Технології створення програмних продуктів/` (lectures `Л1…Л8 *.pptx`, testing PDFs, `Корисна література від викладача/`, `2020-КР-Приклад опису Діаграм…pdf`) |
| Theme file | `My_theme.txt` (root) | `Технології створення програмних продуктів/My_theme.txt` |
| Title template | `Титульна сторінка для лб.docx` | `Технології створення програмних продуктів/Титульна сторінка для практичних робіт.docx` |
| Workspace | `labN/` | `tspp_work/practN/` |
| Details | §1–§8 below | §9 below |

**Knowledge isolation:** never cite or borrow theory, standards or terminology of one course in the other. **Shared:**
the domain model (`DOMAIN_KNOWLEDGE_BASE.md` — РЦПДО «Щит-Північ», IoT-платформа «Щит-Лінк») and the toolchain in
`tools/`. Never modify `lab1/`…`lab7/` or root ПІС files from Track 2 work.

## 1. Project overview (Track 1 — ПІС)
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
| `tools/puml_render.py`, `tools/plantuml/` | PlantUML renderer (jar not committed — see tools/plantuml/README.md) + legibility gate |
| `tools/drawio_lib.py`, `tools/drawio_export.py` | native draw.io export of every ПІС diagram (BPMN via DI, Mermaid via .mmd + SVG geometry, IDEF/PlantUML via SVG) → `labN/drawio/NN_*.drawio` in defence order (`MANIFEST`); `--png` previews via `drawio` desktop CLI |
| `tools/make_speeches.py` | defence prompters («СУФЛЕР», Ukrainian .docx) for **every work of every subject** → `Суфлери/<дисципліна>/<робота>/NN_*_СУФЛЕР.docx` + `Суфлери/README.md`. Registry `WORKS`; content: ПІС `labN/speech/content_labN.py` (one per draw.io file, order = MANIFEST), ТСПП `tspp_work/speech/content_*.py`, кібербезпека `cybersec_work/speech/`, ТАУ `tau_work/speech/` (one per defence topic, `show` = figures/tables to show). **Every new work gets prompters too.** |
| `tools/docx2pdf.sh` | headless .docx → .pdf via OnlyOffice x2t (no LibreOffice on this machine) |
| `.claude/skills/diagram-generator/` | diagram workflow skill |
| `.claude/skills/academic-report-builder/` | report assembly skill |
| `.claude/skills/curriculum-compliance-reviewer/` | pre-submission audit skill |
| `tspp_work/practN/` | Track 2 workspace (see §9): `model_pN.py`, `make_practN.py`, `diagrams/`, output `ПРN_Кравченко_ІР-31.docx` |
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
  diagrams rendered by `tools/idef_model.py`; AFPM dialog steps described in text).
- **ЛР4** — done: `lab4/model4.py` + `lab4/make_lab4.py`: DFD A4, DFD A5 (Gane–Sarson, off-page reference),
  ABC (cost centres, roll-up C = Σ C·F, A0 with ABC Data), Activity Cost Report, UDP + Diagram Object Report,
  Arrow / Data Usage / Consistency reports.
- **ЛР5** (brief `лб5_6.docx`) — done: `lab5/model5.py` + `lab5/make_lab5.py`: use-case diagrams (idef_model
  `usecase` renderer), activity ×2, sequence, class ×2 (PlantUML via `tools/puml_render.py`).
- **ЛР7** (brief `лб7_Архітектура ІоТ.docx`) — done: `lab7/model7.py` + `lab7/make_lab7.py`: 6-level architecture
  (idef_model `layers` renderer, portrait, security badges S1–S5), information-flow diagram (`dfd` with
  `frame: False` + layer `columns`), components / protocols / security tables.

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

## 9. Track 2 — «Технології створення програмних продуктів» (practical works)
- **Briefs:** ПР1 = `Технології створення програмних продуктів/Практична робота 1.docx`; ПР2–ПР4 are screenshots
  `Практична робота 2.png`, `3.png`, `4.png` — `Read` them (image) before work. They do not name specific slides;
  map lectures yourself (Л1 ЖЦ/models, Л2 requirements, Л3 IS & DB, Л4 methodologies, Л5 design/patterns,
  Л6 testing, Л7 tools, Л8 RUP/use cases).
  - **ПР1** (done) — Збір та документування вимог: theme + DB (≥ 5–6 linked populated tables), FR/NFR, use case
    diagram, SRS (10-section structure of the brief), conclusions.
  - **ПР2** (done; was due 2026-09-23) — Архітектура IoT-екосистеми: `pract2/model_p2.py` + `make_pract2.py`.
    Level model = the teacher's own 4-level IoT model (Zinko, Kravchenko 2024; Васюта, Кравченко IST 2025; Легойда,
    Кравченко 2024 — all in `Корисна література від викладача/`): рівень датчиків (сприйняття) / мережевий / обробки
    даних (проміжного ПЗ) / застосунків, drawn in her 4-column figure style (`idef_model` kind `columns`).
    Styles/patterns/SOLID from Л5. Do NOT use ПІС lecture 7 terminology here.
  - **ПР3** (done; was due 2026-09-30) — `pract3/model_p3.py` + `make_pract3.py`: analogues DELTA, DedroneTracker.AI,
    Flightradar24, ThingsBoard, QGroundControl (9 criteria / 4 groups); hardware by weighted scoring (winner computed):
    UMA-16 v2 + Raspberry Pi 5, Robin Radar IRIS, FLIR Hadron 640R, Jetson Orin Nano Super. Facts web-verified
    04.10.2026 (31 sources, «дата звернення»); drop any claim that cannot be verified on a primary page.
    Original brief: 4–5 software analogues (any domain), each
    with "what we take from it", comparison table by own criteria; sensors from vendors compared by criteria and
    chosen; conclusion = overall HW + SW solution. **Sources numbered by order of first mention, `[n]` before the
    sentence's full stop.** Structure: 2 sections with subsections + Висновки + джерела.
  - **ПР4** (done; due 2026-10-14) — `pract4/model_p4.py` + `make_pract4.py`: BPMN ×2 (TO-BE, platform lanes),
    IDEF0 A-0 + A0 (system viewpoint, mechanisms = gateways / core / apps), UML concept (use case reused from ПР1,
    state of «Місія», classes) → logical (activity, sequence, collaboration) → physical (DB classes, components,
    deployment), mirroring the 2020 example's structure.
    §2.6 «Реалізація моделей у CASE-засобах» (added 2026-10-11, mirrors the example's CASE subsection): toolchain
    figure `14_toolchain.mmd` + `pract4/ddl_gen.py` (forward engineering: physical class `.puml` + state `.puml`
    → `pract4/schema.sql` for PostgreSQL, enum values `model_p4.ENUMS`, nullable `model_p4.NULLABLE`; fragment
    rendered as `15_ddl_fragment.png` with its own layout.json). Script verified in a temp PostgreSQL 18 cluster. `idef_model` IDEF0 frame fields now overridable via spec
    `frame` (Track 2 reader = Кравченко О. В.). PlantUML: prefix typed attributes with `{field}` when `hide methods`.
    Original brief: Проектування системи: "section 2 of the project work" — BPMN, UML and IDEF diagrams of
    the application domain and node/module interconnections; every figure described in detail; third-person
    technical narrative. Reference: `2020-КР-Приклад опису Діаграм -Розробка UML.pdf`.
- **Лабораторні роботи Track 2** (assignment text only in MS Teams — differs from `Теми лабораторних робіт…docx`;
  title template `Титульна сторінка для лб.docx`, `work_label: "Лабораторна робота №"`, workspace `tspp_work/labN/`):
  - **ЛР1** (done; due 2026-10-21) «Опис бази даних»: context / logical / physical DB model, table descriptions with
    types, conclusions = FR for ЛР2 (ФВ-БД-01…13). `lab1/model_l1.py` (single source: 18 tables in 3 levels
    довідникові/основні/операційні × 4 subject groups, 14 ENUMs, indexes) → `gen_l1.py` (SQL DDL, IE-notation
    PlantUML ER logical+physical per group, context .mmd, `verify()` = temp PostgreSQL cluster + integrity tests)
    → `make_lab1.py`. Theory = Л3 (трирівнева архітектура СКБД, моделі даних); structure mirrors Безносюк 2026
    thesis (supervisor Кравченко). In prose write `0..∗` (U+2217), not `0..*` — `*` triggers Markdown italics.
  - **ЛР2** (done; due 2026-10-28) «Опис програмної реалізації системи»: мета, вхідні/вихідні дані, системні
    вимоги, засоби з обґрунтуванням, алгоритм + блок-схеми, інтерфейс; plus §8 = implementation of ФВ-БД-01…13.
    Real working product: `lab2/db/impl.sql` (PL/pgSQL functions, triggers, views, roles, hash-chained audit),
    `lab2/db/seed.py`, Flask app `lab2/app/` (psycopg, Jinja2), `lab2/run_demo.py` (temp PostgreSQL → seed → app →
    REST API → screenshots via `tools/bpmn/shots.mjs` at 720 px × 3 → FR checks → `demo.json`, read by
    `make_lab2.py`), `lab2/serve.py` = live demo at http://127.0.0.1:5080. Flowcharts = `idef_model` kind
    `flowchart` (ISO 5807 symbols, grid + on-page connectors; Mermaid TB flowcharts were < 10 pt).
    Order: `run_demo.py` → `make_lab2.py` → build. Screenshots: all CSS fonts ≥ 16 px, viewport 720 → 10.4 pt.
- **Product:** theme from the course `My_theme.txt` («Розподілена IoT-система цілевказівки та координації дронів для
  перехоплення повітряних цілей») realised as IoT-платформа «Щит-Лінк»; title-page «Тема» = practical-work title.
- **Pattern:** `tspp_work/practN/model_pN.py` (data) + `make_practN.py` (diagrams + `report.yaml`); shared helpers in
  `tspp_work/tspp_common.py` (`number_citations` — `[@key]` → `[n]` by first mention, aborts on uncited sources;
  `block_helpers`). Later practicals import earlier models (e.g. ПР2 reads FR/NFR from `pract1/model_p1.py`).
- **`idef_model` kind `columns`** (added for Track 2): vertical columns with dashed separators, titles on top, bold
  layer names at the bottom, orthogonal item-to-item arrows (`gap`, `rh`, `colw`, `bw`, link opts `both`/`dash`).
- **Spec keys for the shared tools:** `template`, `work_label: "Практична робота №"`, `subject`, `theme`,
  `required_sections` (checker), block `refs:` for the reference list (left-aligned so URLs don't stretch lines; the checker skips
  the reference list when scanning for English placeholder words). Structure used: numbered sections
  `1. Мета та завдання роботи` … `N.`, then `Висновки`, `Список використаних джерел` (each on a new page).
- **Build/check:** `.venv/bin/python tspp_work/practN/make_practN.py && .venv/bin/python tools/build_report.py
  tspp_work/practN/report.yaml --pdf && .venv/bin/python tools/check_report.py tspp_work/practN/ПРN_Кравченко_ІР-31.docx
  --spec tspp_work/practN/report.yaml` (check only `--pdf` builds: without page numbers the ЗМІСТ entries equal the
  headings and the TOC-style check misfires).
