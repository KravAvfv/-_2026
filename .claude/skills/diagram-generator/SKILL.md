---
name: diagram-generator
description: Autonomous, self-healing Mermaid diagram pipeline for ПІС lab reports — writes .mmd sources with the project theme, renders ultra-high-DPI PNGs with mmdc (-s 3+), measures the font size the text will have once placed in Word, and re-works the diagram until it is legible (≥ 10 pt) and sharp (≥ 300 dpi). Use whenever a lab needs any diagram (goal tree, WBS, org chart, BPMN-style flow, IDEF0/IDEF3/DFD approximations, UML, architecture).
allowed-tools: Bash, Read, Write, Edit
---

# Diagram Generator (Mermaid → print-grade PNG)

The user never edits diagrams by hand. You own the whole loop: model → `.mmd` → render → measure → fix → embed.

## 0. Ground rules
- **Language:** every label in Ukrainian, using lecture terminology from `DOMAIN_KNOWLEDGE_BASE.md` §8.
  No generic placeholders ("User", "Process 1", "Item"). Names come from the knowledge base (R-xx, S-xx, BP-xx, E-xx).
- **Notation fidelity first, Mermaid second.** Check the lecture rules (see `curriculum-compliance-reviewer`) before
  drawing: e.g. IDEF0 needs 3–6 blocks per decomposition, verb names for functions, noun names for arrows, ≥ 1
  control and ≥ 1 output per block; BPMN needs start/end events, pools/lanes; goal-tree levels formulated as results.
- **Location:** `labN/diagrams/<NN>_<slug>.mmd` (e.g. `lab1/diagrams/03_goal_tree_overview.mmd`). PNG, SVG and
  `.layout.json` are generated next to it — never hand-edit generated files.
- **No init directive needed.** The project theme lives in `tools/mermaid-config.json` (Times New Roman, 20 px,
  black on white, no shadows) and is applied by the renderer.
- **Known mmdc 12 behaviour (verified 2026-10-03):** `%%{init}%%` directives, YAML frontmatter and config-file
  `flowchart.rankSpacing/nodeSpacing/padding` are **ignored** by the default layout engine. Forcing
  `"layout": "dagre"` makes spacing work but produces diagonal edges that cut through boxes — **do not use it**.
  Control density through structure instead: direction (TB/LR), label line breaks, splitting, subgraphs.

## 1. Authoring rules for legibility
1. **One idea per figure.** Max ≈ 12–15 nodes per flowchart, ≈ 8 lifelines per sequence diagram, ≈ 10 classes per
   class diagram. Bigger models → overview figure + one figure per branch/subsystem (e.g. "Рис. 1.6 — Гілка 2 дерева
   цілей"). This is the single most important rule; the instructor's own examples (лб1.docx Рис. 2.6–2.7) fail it with
   rotated microscopic text — never reproduce that.
2. **Break long labels** manually with `<br/>` at ~22–28 characters per line; keep ≤ 4 lines per node.
3. **Choose direction by shape of the tree:** wide-and-shallow → `flowchart TB`; deep-and-narrow or long chains →
   `flowchart LR`. A chain of > 5 boxes in one row is never legible — wrap into rows with subgraphs or switch to TB.
4. Hierarchies (goal tree, WBS, org chart): `flowchart TB`, numbered codes in labels ("1.2 Скоротити час…").
   For the lowest level use a vertical stack: connect children in a chain with invisible links (`~~~`) under a parent
   to make columns instead of a 15-wide row.
5. Use `classDef` for levels (e.g. bold border for level 0, light grey fill `#F2F2F2` for level 1). Stay
   monochrome/greyscale — reports are printed in black and white.
6. Quote every label: `A["…"]`. Escape quotes inside labels with `#quot;`. Avoid `(`, `)`, `;` unquoted.
7. Edge labels short (≤ 3 words). For IDEF0-like arrows prefer noun phrases.

## 2. Render + measure (always through the tool)
```bash
.venv/bin/python tools/mmd_render.py labN/diagrams/NN_slug.mmd            # default: -s 3, min 10 pt
```
The tool:
- runs `mmdc -i … -o ….svg -c tools/mermaid-config.json -b white` (native geometry) and
  `mmdc … -o ….png -s 3` (print raster);
- computes the effective font size for portrait (16.5 cm text width) and landscape (25.7 cm) placement, picks
  portrait if legible else landscape, caps small diagrams at ≈ 13 pt so they are not blown up;
- auto re-renders with a higher scale until effective resolution ≥ 300 dpi;
- writes `NN_slug.layout.json` (`orientation`, `width_cm`, `font_pt`, `dpi`) used by the report builder;
- exits **3** if the diagram is too dense even in landscape.

## 3. Self-healing loop (mandatory)
Repeat until exit code 0 **and** visual check passes (max ~6 iterations, then redesign the figure split):
| Symptom | Fix |
|---|---|
| mmdc parse error (exit 1) | read the error line, fix syntax: unquoted special chars, reserved words (`end`, `graph`) as ids, missing `end` of subgraph, bad arrow syntax |
| exit 3 "TOO DENSE" | split into overview + detail figures; switch TB↔LR; shorten labels; use `<br/>`; stack leaf nodes vertically |
| aspect ratio > 3.5 or < 0.35 | rebalance (wrap rows / subgraphs) — extreme ratios waste the page and shrink text |
| overlapping edges / spaghetti | reorder node declarations, add `rankSpacing`/`nodeSpacing`, split |
| warning dpi < 300 | handled automatically; if still low raise `--scale` manually |

**Visual verification:** after a successful render, `Read` the PNG (it is an image) and check: no clipped text,
no overlapping labels, no crossing spaghetti, Cyrillic glyphs rendered (no tofu boxes), arrows point the right way,
numbering correct. Only then hand the `.mmd` to the report.

## 4. Notation recipes (Mermaid approximations)
- **Goal tree / WBS / org chart:** `flowchart TB` + `classDef`. WBS codes `1`, `1.1`, `1.1.1`; goal codes `0`, `1`, `1.1`.
- **IDEF0 context (A-0) & decomposition:** `flowchart LR`; function = rectangle with label `A1<br/>Назва (дієслово)`;
  inputs enter from the left, outputs leave right, controls from a top subgraph, mechanisms from a bottom subgraph;
  label every arrow with a noun. Put the node number bottom-right in label text (e.g. `A2`). If Mermaid layout cannot
  keep ICOM sides, state ICOM role explicitly in arrow labels (`Вх:`, `Упр:`, `Вих:`, `Мех:`) and add a legend line in
  the caption note.
- **IDEF3:** `flowchart LR`; UOW boxes `1.1 Назва`; junctions as small nodes `J1{{"X"}}`, `J2{{"&"}}`, `J3{{"O"}}`.
- **DFD (Gane–Sarson flavour):** process = rounded `("1.0<br/>Назва")`, store = `[("D1 Треки")]`-style cylinder or
  open rectangle `["D1 | Треки"]`, external entity = rectangle with thick border via classDef.
- **BPMN-style:** `flowchart LR` with `subgraph` per pool/lane; start `(( ))`, end `((( )))`, gateways `{"X"}`;
  label message flows with `-.->`. (For strict BPMN a dedicated tool is required; state this in the report if needed.)
- **UML:** use native `classDiagram`, `sequenceDiagram`, `stateDiagram-v2`; use-case diagrams via `flowchart LR`
  with actors as `["👤 Роль"]`-free plain boxes styled `actor` classDef and ellipses `(["Прецедент"])`.
- **Architecture/deployment:** `flowchart TB` with subgraphs per IoT layer (рівень сприйняття → периферійний →
  прикладний → користувача).

## 4a. Strict BPMN 2.0 (use this, not Mermaid, for BPMN)
Mermaid cannot draw real BPMN (typed events, gateway markers, pools/lanes, message flows). Use the project engine:
- Describe the diagram as a Python dict (pools → lanes → nodes with `col`/`row`, `flows`, `data`, `messages`) —
  see `lab2/make_lab2.py` and the docstring of `tools/bpmn_model.py`.
- `write(spec, "labN/diagrams/NN_name.bpmn")` emits valid BPMN 2.0 XML **with DI** (opens in Camunda Modeler /
  bpmn.io); `tools/bpmn/render.mjs` renders it with **bpmn-js** (bpmn.io reference renderer) in Chrome headless,
  Times New Roman, 4× scale; `render()` applies the same legibility gate (`.layout.json`).
- Budget per landscape figure at ≥ 10 pt: ≈ 1090 × 615 native px → about 4 task columns + 2–3 narrow
  (event/gateway) columns and ≤ 5 lane-rows. Split big pools with **link events** (`"marker": "link", "link": "А"`).
- Engine conventions: gateway questions ≤ 18 chars (one line above the diamond; auto-moves below when a branch goes
  up); events get labels opposite their message flows; tasks' message flows attach off-centre; loops run along
  the lane bottom; collapsed external pools can share a row (`"slot"`, `"cols"`); `"free": True` for hand-placed
  interaction maps. Keep lane names ≤ 2 lines (≈ 14 chars per line).
- **Always regenerate the model (`make_labN.py`) before re-rendering** — `tools/bpmn_model.py file.bpmn` only
  re-renders existing XML.

## 5. Hand-off to the report
In `labN/report.yaml` reference the `.mmd` / `.bpmn` source (not the PNG):
```yaml
- figure: {id: goal_tree, src: lab1/diagrams/03_goal_tree_overview.mmd, caption: Дерево цілей …, orientation: auto}
```
The builder re-renders automatically when the `.mmd` is newer than the PNG and uses `layout.json` for orientation
and width. Force `orientation: landscape` only if a human-looking reason exists (e.g. series of related figures).
