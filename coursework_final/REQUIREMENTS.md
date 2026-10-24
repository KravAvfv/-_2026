# REQUIREMENTS — курсова робота з дисципліни «Проєктування інформаційних систем»

Source: `ПІС_Курсова_робота_2026.pdf` — методичні вказівки (Гладка М. В., Бондаренко О. С., Борисенко І. І.,
Терещук Г. М., Онищенко А. М., КНУ, 2026, 48 с.). Text layer extracted with `pdftotext` (not scanned); image-only
figures 4.1–4.3 (Word paragraph dialogs) were rendered and read visually. Page numbers below = printed page number
= PDF page index.

Status column is filled at the end of the work (see the bottom of this file and `VERIFICATION.md`).

## A. Topic, object, organisation (pp. 6–12, 33, 44–45)

| ID | Requirement | Page |
|---|---|---|
| A1 | Theme form «Проєктування інформаційної системи… (індивідуальні параметри завдання)»; own theme allowed if agreed with supervisor, relevant to the discipline, actual, implies design of a modern IS | 9, 12 |
| A2 | Object of research — enterprise / institution / organisation / unit whose activity needs automation | 9 |
| A3 | Theme approved by application (Додаток Б form); student proposes supervisor | 9, 43 |
| A4 | Project character: complete IS project — full set of models, schemes, diagrams, architecture decisions and prototypes sufficient for further implementation | 4–5, 7 |
| A5 | Pass all life-cycle stages: domain analysis → requirements → functional & OO models → architecture → roles → UI prototype | 4, 6, 13 |
| A6 | Usefulness and practical value are mandatory | 33 |
| A7 | Use modern scientific sources, normative documents, professional software tools | 10 |
| A8 | After literature study — develop the algorithm of the program and program the application itself | 34 |

## B. Tasks of the course work (pp. 6–7)

| ID | Task | Page |
|---|---|---|
| B1 | Investigate the domain, define the object of automation | 6 |
| B2 | Analyse the activity of the enterprise / unit | 6 |
| B3 | Define problems of the existing system, list processes to automate | 6 |
| B4 | Define IS goals and build a goal tree | 6 |
| B5 | Build project structure with WBS | 6 |
| B6 | Functional modelling of business processes in BPMN | 6 |
| B7 | OO design with UML diagrams | 6 |
| B8 | Design the IS concept, software-hardware architecture, user roles, component interaction | 7 |
| B9 | Develop a UI prototype for the main user categories | 7 |
| B10 | Prepare the explanatory note per the guidelines and current standards | 7 |

## C. Structure of the explanatory note (pp. 13–21, Table 4.1, Table 4.2)

| ID | Element (Table 4.1 volume) | Required content (Table 4.2 and text) | Page |
|---|---|---|---|
| C1 | Титульний аркуш (1 p.) | Form of Додаток А | 13, 42 |
| C2 | Завдання на курсову роботу (1 p.) | Assignment (issued by supervisor with deadlines per section) | 14, 33 |
| C3 | Зміст (1–2 p.) | All sections and subsections with start pages; short, literate titles not repeating the work title | 13–14 |
| C4 | Вступ (1–2 p.) | Actuality; object; subject; goal; tasks; practical significance | 14, 18 |
| C5 | Розділ 1 «Аналіз та опис об'єкта дослідження. Постановка задачі на проєктування» (7–10 p.) | | 14–15 |
| C5.1 | 1.1 Аналіз об'єкта дослідження | general characteristic; org structure; characteristic of the structural unit; org-structure scheme; main business processes; list of works of the unit; (recommended) scheme of unit interaction | 15, 18–19 |
| C5.2 | 1.2 Основні функції підприємства | functions of units; list of information flows; table of functional interconnections between units; description of interaction; list of main staff tasks; responsible executors of processes | 15, 19 |
| C5.3 | 1.3 Завдання на автоматизацію | analysis of existing problems; processes to automate; functional requirements to the IS; list of system users; expected results | 15, 19 |
| C5.4 | 1.4 Цілі підприємства | main goal of automation; goal tree built with a modern strategic-planning approach; decomposition into sub-goals; relations between goals; criteria of goal achievement | 15, 19 |
| C5.5 | 1.5 Робоча структура проєкту (WBS) | analysis of project characteristics; list of stages; decomposition of works; hierarchical WBS scheme; short description of each work package | 15, 19 |
| C6 | Розділ 2 «Проєктування моделі інформаційної системи» (7–10 p.) | | 16 |
| C6.1 | 2.1 Функціональне моделювання | BPMN model(s); purpose of each model; participants (pools, lanes); business events; tasks; gateways; information flows; logic of the process | 16, 19–20 |
| C6.2 | 2.2 Об'єктно-орієнтоване проєктування | **mandatory**: Use Case, Activity, Sequence, Class diagrams; specification of main use cases; for each diagram — purpose, explanation of elements, justification of decisions; relations between diagrams | 16, 20 |
| C7 | Розділ 3 «Проєктування компонентів діяльності системи» (5–7 p.) | justify the concept of the automated IS; architecture type (client-server, multi-tier, cloud…); software-hardware architecture; configuration of server, client and network equipment; information flows between components; user categories (roles), functions and access rights; mechanisms of user interaction. Table 4.2: IS concept; architecture description; software-architecture scheme; hardware-architecture scheme; network-interaction scheme; list of software components; server part; client part; database description; list of roles; access-rights table; component-interaction scheme | 16–17, 20 |
| C8 | Розділ 4 «Створення прототипу системи» (5–10 p.) | prototype shows the logic of the system and user interaction; modern prototyping tool (Figma, Adobe XD, Penpot **or other analogous tools**). Needed: navigation map; main page; authorisation page; main functional modules; separate interfaces for each user role; input forms; edit forms; view pages; search & filter pages; short description of purpose and usage scenario of every screen | 17, 20–21 |
| C9 | Висновки (1–2 p.) | evaluate goal achievement; summarise results; main advantages of the IS; directions of further development | 17, 21 |
| C10 | Перелік використаних інформаційних джерел (1–2 p.) | current bibliographic standard (ДСТУ 8302:2015); scientific publications, monographs, normative documents, international standards, technical documentation, e-resources; preferably last 5–10 years; numbered; alphabetical or order of citation | 18, 29–30, 46–47 |
| C11 | Додатки (as needed) | large BPMN/UML diagrams, goal tree, WBS, architecture schemes, full prototypes, requirement specifications, auxiliary tables | 18, 21, 30–31 |
| C12 | Volume 30–50 pages without title, assignment, contents, references and appendices. **Instructor (2026-10-23): whole document = 50 pages** → met: 50 pages total, body (Вступ…Висновки) pp. 4–48 = 45 pages | 14, 21 |
| C13 | All schemes, diagrams, tables and figures interrelated and reflect one IS development process | 13 |

## D. Formatting (pp. 21–31)

| ID | Rule | Page |
|---|---|---|
| D1 | Ukrainian language, A4 | 22 |
| D2 | MS Word or compatible; Times New Roman 14 pt; line spacing 1.5; black; justified; first-line indent 1.25 cm; spacing before/after paragraph 0 pt | 22 |
| D3 | Margins: left 30 mm, right 10 mm, top 20 mm, bottom 20 mm; equal indents throughout | 22 |
| D4 | Screen forms — as numbered figures included in page numbering; tables / figures > 2 pages go to appendices | 22 |
| D5 | Arabic page numbers, continuous including appendices; title page counted but not numbered; number in the **top right corner, no dot** | 22 |
| D6 | Headings ЗМІСТ, ВСТУП, РОЗДІЛ, ВИСНОВКИ, ПЕРЕЛІК ВИКОРИСТАНИХ ІНФОРМАЦІЙНИХ ДЖЕРЕЛ, ДОДАТКИ — capitals, bold, centred | 23 |
| D7 | Each section (розділ) starts on a new page | 23 |
| D8 | Subsections — from paragraph indent, bold; no full stop after headings; spacing before 18 pt, after 12 pt, line 1.5 (Fig. 4.1) | 23 |
| D9 | Sections numbered 1, 2, 3, 4; subsections 1.1, 1.2…; items 2.2.1… | 23 |
| D10 | Lists: dash, or lower-case letter with bracket; deeper level — Arabic numeral with bracket; items end with «,» «;» or «.»; list ends with «.» | 23–24 |
| D11 | Figures right after first mention or on next page; all figures referenced in text; numbered within section; caption below, centred: «Рисунок 2.4 – Назва» (sample is bold); caption paragraph: centred, first line 1 cm, before 6 pt, after 18 pt, 1.5 lines (Fig. 4.2); text reference «…наведено на рисунку 2.4» | 24–26 |
| D12 | Appendix figures numbered «Рисунок А.1» | 26 |
| D13 | Tables right after the paragraph with first reference, or next page; > 1 page → appendix; numbered within section; caption «Таблиця 1.2 – Назва» above the table, **right-aligned**, before 18 pt, after 6 pt, 1.5 lines, keep with next (Fig. 4.3; p. 27 text). (p. 26 also says number top-right and title centred below — conflicting; the explicit paragraph settings of Fig. 4.3 and p. 27 are followed) | 26–27 |
| D14 | Split tables: header repeated, «Продовження табл. N» / «Закінчення табл. N»; every table referenced in text; landscape allowed; appendix tables «Таблиця А.1»; headers capitalised, no full stop at end, horizontal | 26–28 |
| D15 | Citations: «[8, c. 12–14]» — source number and pages where explanatory info is; several sources «[2, 7]» / «[4–6]»; quotation in quotes with page | 28, 30 |
| D16 | Formulas centred, numbered «(4.1)» at right; 12–24 pt before/after; «де» without colon followed by explanation | 29 |
| D17 | Appendices: first clean page «ДОДАТКИ» centred in capitals; each appendix on a new page; «Додаток А» top right; appendix title sentence case, centred; letters of Ukrainian alphabet except Ґ, Є, З, І, Ї, Й, О, Ч, Ь; placed after references, in order of reference; references to appendices in text mandatory | 30–31 |
| D18 | Academic integrity: no plagiarism, fabrication or falsification; correct citations | 31 |

## E. Defence (pp. 34–36) — out of scope for the document, noted for the student

| ID | Item | Page |
|---|---|---|
| E1 | Printed note bound in a folder, signed by author and supervisor; text + presentation uploaded to the e-class | 34 |
| E2 | Submitted to the department one week before defence for norm-control | 34 |
| E3 | Report 5–7 min; presentation 10–16 slides; demonstrate models, architecture, UML and prototype | 35–36 |

## F. Grading (pp. 37–39)

Table 5.1: analysis 5; goal tree + WBS 5; BPMN 10; UML (Use Case, Activity, Sequence, Class) 15; architecture 15;
prototype 15; quality of the note 15; defence 20. Grade-lowering defects (p. 39): mismatch with theme, superficial
analysis, missing/incorrect BPMN or UML, unjustified architecture, missing/incomplete prototype, formatting
violations, missing source references, integrity violations.

## G. Additional requirements from the user's request

| ID | Requirement |
|---|---|
| G1 | Consistent with the student's ПІС labs and ТСПП works on the same topic |
| G2 | Working software, no stubs, all tests passing |
| G3 | All required diagrams; explanatory note in Ukrainian as .docx and .pdf |
| G4 | No invented facts, sources, results, screenshots or numbers; screenshots from the real running app; unknowns → placeholders |
| G5 | Every PDF page rendered and inspected; code ↔ diagram consistency checked; independent strict reviewer loop until clean |
| G6 | Everything in `coursework_final/`; final list of placeholders |
