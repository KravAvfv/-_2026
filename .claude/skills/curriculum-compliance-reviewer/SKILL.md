---
name: curriculum-compliance-reviewer
description: Pre-submission audit of any ПІС lab deliverable against the instructor's lectures (ПІС_1…ПІС_8_9, Гладка М.В.), the lab briefs (лб1–лб3.docx), the reference textbooks (Корисна інфа 1–5) and Ukrainian academic writing norms. Runs the automated checker, then walks a notation-specific rule catalogue (goal tree, WBS, BPMN, IDEF0, IDEF3, DFD, UML, IoT architecture) and reports PASS/FAIL per rule with fixes. Use before finalising every report or diagram set.
allowed-tools: Bash, Read, Grep, Glob
---

# Curriculum Compliance Reviewer

Run this **after** the report is built and **before** telling the user it is done. Fix every FAIL yourself,
rebuild, re-run. Report the final checklist to the user in English (short).

## Step 1 — automated gate
```bash
.venv/bin/python tools/check_report.py labN/ЛРN_Кравченко_ІР-31.docx --spec labN/report.yaml
```
Must end with `RESULT: PASS`. Review each WARN.

## Step 2 — task coverage vs. the lab brief
Open `лбN.docx` ("Завдання" list). Build a trace table *task item → report subsection → figure/table*. Every item must be
covered in the same order. Missing item = FAIL. (Lab 1 brief has 14 items; see CLAUDE.md §7 Lab map.)

## Step 3 — notation rule catalogue (source in brackets)

### Дерево цілей (ЛР1; лекція 2; лб1 теорія)
- [ ] One generic goal (генеральна мета) at the top, formulated as a desired result, code `0`. *(лб1, рис. 2.3)*
- [ ] Goals of each level comparable in scale and importance. *(лекція 2, вимога 1)*
- [ ] Formulations allow quantitative/qualitative assessment (measurable — KPI from KB §6.8). *(в. 2)*
- [ ] Completeness of reduction: sub-goals of a node fully cover the parent. *(в. 3; лб1 "повнота")*
- [ ] Describe desired results, not ways to obtain them (except lowest level = measures/actions). *(в. 4, в. 6)*
- [ ] Sub-goals of one level independent, not derived from each other. *(в. 5)*
- [ ] No contradictions between levels. *(в. 7)*
- [ ] Same methodological approach for the whole decomposition (state which: метод дезагрегації or метод
      забезпечення необхідних умов, Глушков). *(в. 8; лб1)*
- [ ] Lowest-level goals have responsible executors / terms where reasonable. *(в. 9)*
- [ ] Level 1 has no alternatives; alternatives ("і/або") start from level 2 if the disaggregation method is used. *(лб1)*
- [ ] All goals formulated "в термінах робіт" (verbal nouns / infinitives). *(лб1)*
- [ ] Coded hierarchically 0 / 1 / 1.1 / 1.1.1; depth 3–4 levels.

### WBS (ЛР1; лекція 2; лб1)
- [ ] Six development steps documented: ступінь деталізації → кількість рівнів → структура рівнів → опис елементів →
      система кодування → зворотні обчислення (bottom-up cost/effort roll-up). *(лекція 2; лб1)*
- [ ] Levels: 1 проект → 2 стадії/субпроекти → 3 системи/блоки → 4 робочі пакети; 3–4 levels. *(лб1)*
- [ ] Decomposition principle stated (за продуктами/субпроектами, за фазами, за місцем, за центрами затрат). *(лб1)*
- [ ] Every element has a code; lowest level = work packages with: обсяг робіт, відповідальний, бюджет, ресурси,
      дати початку/кінця (table "Основні характеристики проекту"). *(лб1 табл. 2.1–2.2)*
- [ ] Rules: результативність, агрегація, логічність, унікальність (no work in two places — 100 % rule), гнучкість. *(лекція 2)*
- [ ] Integrated work common to several elements is a separate element (e.g. «Управління проектом»). *(лб1)*

### Структурна схема та таблиці (ЛР1)
- [ ] Org chart: rectangles = units, solid arrows = subordination; clear who reports to whom. *(лб1)*
- [ ] Table "Задачі і функції" (№ | Задачі | Функції). *(лб1 табл. 1.1)*
- [ ] Table "Взаємодія підрозділів" (№ | Підрозділ | Одержання | Надання). *(лб1 табл. 1.2)*

### BPMN 2.0 (ЛР2; лекція 3)
- [ ] Four element categories used correctly: об'єкти потоку (події, дії, шлюзи), з'єднувальні об'єкти (потік
      управління, потік повідомлень, асоціації), ролі (пули, доріжки), артефакти (дані, групи, анотації).
- [ ] Each process has start and end events; gateways split *and* merge; message flows only between pools;
      sequence flows never cross pool boundaries; each separate function of the organisation as a separate pool (лб2).
- [ ] Analysis of pools/lanes count and role interactions given in text (лб2 task 3).

### IDEF0 (ЛР3; лекція 4)
- [ ] Context diagram A-0 present: one block, ICOM arrows, **мета моделювання** and **точка зору** stated.
- [ ] Non-context diagrams have 3–6 blocks, placed diagonally (staircase).
- [ ] Function names = verbs/verbal phrases; arrow names = nouns; all names unique.
- [ ] Each block has ≥ 1 control and ≥ 1 output.
- [ ] Minimal crossings and bends; branching/merging arrows labelled; ICOM consistency between parent and child
      (boundary arrows of child = arrows of parent block).
- [ ] Arrow types: вхід (left), управління (top), вихід (right), механізм (bottom); виклик only for model split/merge.
- [ ] Relations shown where relevant: вихід-вхід, вихід-управління, зворотний зв'язок, вихід-механізм.
- [ ] Organisation separated from functions (blocks are functions, not departments).
- [ ] Total depth incl. context ≤ 5–6 levels; stop criteria respected.
- [ ] Node tree and FEO diagram provided when the brief asks (лб3).

### IDEF3 (ЛР3; лекція 5)
- [ ] UOW = rectangle, verb name, unique number; links precedence (solid), relational (dashed), object flow
      (double-headed); referents linked without arrowhead.
- [ ] Junctions typed (асинхронне/синхронне «і», «або», виключне «XOR») and paired fan-out/fan-in; named J1, J2…
- [ ] Flow left→right; scenario diagram if requested.

### DFD (лекція 5; Пістунов)
- [ ] Components: зовнішні сутності, процеси, накопичувачі, потоки; notation declared (Гейна–Сарсона or Йордана).
- [ ] 3–6(7) processes per diagram; decomposition of flows parallel to processes; no flow store→store or
      entity→entity; every store has in- and out-flows; clear names without abbreviations.

### UML 2.x (лекція 6; Ізмайлова)
- [ ] Use cases: actors are roles (not people); use cases named by verbs; include/extend correct; system boundary.
- [ ] Class: name bold, capitalised; attributes `visibility name: type [mult]`; operations lower-camel; correct
      association/aggregation/composition/generalisation semantics; multiplicities on associations.
- [ ] Sequence: lifelines, solid = calls, dashed = returns, only participants of the scenario.
- [ ] State/activity/component/deployment per lecture symbols.

### IoT architecture (лекції 7, 8–9)
- [ ] Four levels named: сприйняття, мережевий/периферійний (edge/gateway), прикладний/хмарний, користувача.
- [ ] Roles & interfaces: людські ролі + системні (M2M); апаратні, програмні (API), користувацькі (UI).
- [ ] Security architecture: фізичний, організаційний, програмно-апаратний рівні захисту; IEC 62443 / ISO 27001.

## Step 4 — report-form rules
- [ ] Title page = template, only 3 placeholders changed (lab №, theme, year).
- [ ] Sections: Мета роботи → Короткі теоретичні відомості → Хід виконання роботи → Графічна частина → Висновки.
- [ ] Times New Roman 14, 1.5 spacing, indent 1.25 cm, justified; tables 12 pt allowed. (Пістунов: TNR 14, 1.5)
- [ ] Captions: "Рис. N.k — Назва" under figures, "Таблиця N.k — Назва" above tables; all referenced in text.
- [ ] Every diagram legible: `layout.json` font_pt ≥ 10, dpi ≥ 300; visually checked in `labN/preview/`.
- [ ] Ukrainian only in the report; no placeholder/generic names; lecture terminology (KB §8).
- [ ] Conclusions answer every goal statement with concrete numbers.

## Step 5 — common student mistakes to hunt (from the instructor's material)
1. Goal tree lists *departments* or *actions* instead of goals/results at upper levels.
2. Goal levels mixing scales (strategic next to trivial task).
3. WBS duplicating the goal tree (WBS = work/deliverables of the *project of creating the IS*, not company goals).
4. WBS without codes / without work-package characteristics table.
5. IDEF0 blocks named as nouns or departments; arrows named as verbs; missing control arrows.
6. More than 6 blocks on a decomposition; context diagram without purpose/viewpoint.
7. BPMN with sequence flows between pools; gateways without merge; missing end events.
8. Diagrams pasted as illegible screenshots (rotated text) — forbidden here.
9. Theory copied verbatim from textbooks; Russian calques.
10. Theme not consistent between labs — always use `DOMAIN_KNOWLEDGE_BASE.md` names.

## Output to the user
A compact English table: rule group → PASS/FAIL count → fixes applied. Mention any WARN accepted and why.
