#!/usr/bin/env python3
"""Native draw.io (.drawio, uncompressed mxGraphModel XML) export of the lab diagrams.

Three converters, one per source family, all producing editable draw.io cells (vertices + glued edges):
  * bpmn_to_drawio(.bpmn)        — BPMN 2.0 semantics + DI coordinates → draw.io BPMN shapes (pools, lanes,
                                   typed tasks, events, gateways, data stores, sequence/message flows);
  * mermaid_to_drawio(.mmd,.svg) — nodes/classes/subgraphs from the .mmd source, geometry from the rendered SVG;
  * svg_to_drawio(.svg)          — geometric conversion of tools/idef_model.py and PlantUML SVGs: boxes become
                                   shapes with their labels, polylines become edges glued to the boxes, arrow-head
                                   polygons become edge markers, the rest stays as free text.
Output is opened by app.diagrams.net / draw.io desktop as-is (drag & drop).
"""
import html
import math
import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import ImageFont

FONT = "Times New Roman"
_FONTS = {}


def text_w(text, size, bold=False):
    key = (bold, round(size * 4))
    if key not in _FONTS:
        f = "/usr/share/fonts/wps-fonts/timesbd.ttf" if bold else "/usr/share/fonts/wps-fonts/times.ttf"
        _FONTS[key] = ImageFont.truetype(f, round(size * 4))
    return _FONTS[key].getlength(text) / 4.0


def style(**kw):
    """dict → draw.io style string; keys with value True become bare tokens (e.g. text=True → 'text;')."""
    out = []
    for k, v in kw.items():
        if v is None or v is False:
            continue
        out.append(k if v is True else f"{k}={v}")
    return ";".join(out) + ";"


def hlabel(lines):
    return "<br>".join(html.escape(str(s), quote=False) for s in lines)


# ============================================================================================ document
class Drawio:
    def __init__(self, name):
        self.name = name
        self.cells = []
        self.n = 1

    def _id(self):
        self.n += 1
        return f"c{self.n}"

    def vertex(self, x, y, w, h, value="", st="", parent="1", cid=None):
        cid = cid or self._id()
        self.cells.append(dict(kind="v", id=cid, value=value, style=st, parent=parent,
                               geo=(round(x, 2), round(y, 2), round(max(w, 1), 2), round(max(h, 1), 2))))
        return cid

    def edge(self, pts, value="", st="", src=None, tgt=None, parent="1", label_pos=None, cid=None):
        """pts — absolute polyline (first/last = terminal points); label_pos = (rel -1..1, dx, dy)."""
        cid = cid or self._id()
        self.cells.append(dict(kind="e", id=cid, value=value, style=st, parent=parent, pts=pts,
                               src=src, tgt=tgt, label_pos=label_pos))
        return cid

    def bounds(self):
        xs, ys = [], []
        for c in self.cells:
            if c["kind"] == "v" and c["parent"] == "1":
                x, y, w, h = c["geo"]; xs += [x, x + w]; ys += [y, y + h]
            elif c["kind"] == "e":
                for p in c["pts"]:
                    xs.append(p[0]); ys.append(p[1])
        return (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 100, 100)

    def tostring(self):
        x0, y0, x1, y1 = self.bounds()
        mxfile = ET.Element("mxfile", host="app.diagrams.net", agent="Shchyt-Link lab toolchain", version="24.7.17",
                            type="device")
        dg = ET.SubElement(mxfile, "diagram", name=self.name, id=uuid.uuid5(uuid.NAMESPACE_URL, self.name).hex[:20])
        model = ET.SubElement(dg, "mxGraphModel", dx="1400", dy="900", grid="1", gridSize="10", guides="1",
                              tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1",
                              pageWidth=str(int(max(827, x1 + 40))), pageHeight=str(int(max(1169, y1 + 40))),
                              math="0", shadow="0", background="#FFFFFF")
        root = ET.SubElement(model, "root")
        ET.SubElement(root, "mxCell", id="0")
        ET.SubElement(root, "mxCell", id="1", parent="0")
        for c in self.cells:
            el = ET.SubElement(root, "mxCell", id=c["id"], value=c["value"], style=c["style"], parent=c["parent"])
            if c["kind"] == "v":
                el.set("vertex", "1")
                x, y, w, h = c["geo"]
                ET.SubElement(el, "mxGeometry", x=f"{x:g}", y=f"{y:g}", width=f"{w:g}", height=f"{h:g}",
                              **{"as": "geometry"})
            else:
                el.set("edge", "1")
                if c["src"]:
                    el.set("source", c["src"])
                if c["tgt"]:
                    el.set("target", c["tgt"])
                g = ET.SubElement(el, "mxGeometry", relative="1", **{"as": "geometry"})
                if c["label_pos"]:
                    rel, dx, dy = c["label_pos"]
                    g.set("x", f"{rel:.3f}")
                    ET.SubElement(g, "mxPoint", x=f"{dx:.1f}", y=f"{dy:.1f}", **{"as": "offset"})
                pts = c["pts"]
                ET.SubElement(g, "mxPoint", x=f"{pts[0][0]:.2f}", y=f"{pts[0][1]:.2f}", **{"as": "sourcePoint"})
                ET.SubElement(g, "mxPoint", x=f"{pts[-1][0]:.2f}", y=f"{pts[-1][1]:.2f}", **{"as": "targetPoint"})
                if len(pts) > 2:
                    arr = ET.SubElement(g, "Array", **{"as": "points"})
                    for p in pts[1:-1]:
                        ET.SubElement(arr, "mxPoint", x=f"{p[0]:.2f}", y=f"{p[1]:.2f}")
        ET.indent(mxfile)
        return ET.tostring(mxfile, encoding="unicode")

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(self.tostring(), encoding="utf-8")
        return path


def glue(dw, cid, box, p, end):
    """exitX/exitY (or entryX/entryY) style fragment fixing the terminal exactly at point p of box."""
    x, y, w, h = box
    fx = min(1, max(0, (p[0] - x) / w)) if w else 0.5
    fy = min(1, max(0, (p[1] - y) / h)) if h else 0.5
    k = "exit" if end == "src" else "entry"
    return f"{k}X={fx:.4f};{k}Y={fy:.4f};{k}Dx=0;{k}Dy=0;{k}Perimeter=0;"


def label_position(pts, c):
    """(rel, dx, dy) of an edge label centred at c — draw.io edge-label geometry."""
    segs, total = [], 0.0
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b); segs.append((a, b, L, total)); total += L
    if total == 0:
        return (0, c[0] - pts[0][0], c[1] - pts[0][1])
    best = None
    for a, b, L, off in segs:
        t = 0 if L == 0 else max(0, min(1, ((c[0] - a[0]) * (b[0] - a[0]) + (c[1] - a[1]) * (b[1] - a[1])) / L / L))
        q = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        d = math.dist(q, c)
        if best is None or d < best[0]:
            best = (d, off + t * L, q)
    _, s, q = best
    return (2 * s / total - 1, c[0] - q[0], c[1] - q[1])


TEXT_ST = dict(text=True, html=1, strokeColor="none", fillColor="none", spacing=0, spacingTop=0, spacingBottom=0,
               spacingLeft=0, spacingRight=0, verticalAlign="top", whiteSpace="nowrap", fontFamily=FONT)


# ============================================================================================ BPMN
BP = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
BPDI = "{http://www.omg.org/spec/BPMN/20100524/DI}"
DC = "{http://www.omg.org/spec/DD/20100524/DC}"
DI = "{http://www.omg.org/spec/DD/20100524/DI}"
TASK_MARK = {"userTask": "user", "serviceTask": "service", "sendTask": "send", "receiveTask": "receive",
             "manualTask": "manual", "scriptTask": "script", "businessRuleTask": "businessRule", "task": "abstract"}
GW_TYPE = {"exclusiveGateway": "exclusive", "parallelGateway": "parallel", "inclusiveGateway": "inclusive",
           "eventBasedGateway": "eventBased", "complexGateway": "complex"}
EV_SYM = {"messageEventDefinition": "message", "timerEventDefinition": "timer", "linkEventDefinition": "link",
          "terminateEventDefinition": "terminate", "signalEventDefinition": "signal",
          "errorEventDefinition": "error", "conditionalEventDefinition": "conditional"}


def bpmn_to_drawio(bpmn_path, name, font=16):
    tree = ET.parse(bpmn_path)
    r = tree.getroot()
    elems = {e.get("id"): e for e in r.iter() if e.get("id")}
    shapes, edges = {}, {}
    for s in r.iter(BPDI + "BPMNShape"):
        b = s.find(DC + "Bounds")
        lb = s.find(f"{BPDI}BPMNLabel/{DC}Bounds")
        shapes[s.get("bpmnElement")] = (tuple(float(b.get(k)) for k in "x y width height".split()),
                                        tuple(float(lb.get(k)) for k in "x y width height".split()) if lb is not None else None)
    for e in r.iter(BPDI + "BPMNEdge"):
        pts = [(float(w.get("x")), float(w.get("y"))) for w in e.findall(DI + "waypoint")]
        lb = e.find(f"{BPDI}BPMNLabel/{DC}Bounds")
        edges[e.get("bpmnElement")] = (pts, tuple(float(lb.get(k)) for k in "x y width height".split()) if lb is not None else None)

    dw = Drawio(name)
    base = dict(html=1, fontFamily=FONT, fontSize=font, fontColor="#000000", strokeColor="#000000")
    ids, absb = {}, {}
    parts = list(r.iter(BP + "participant"))
    lanes = list(r.iter(BP + "lane"))
    lane_of = {}
    for ln in lanes:
        for ref in ln.findall(BP + "flowNodeRef"):
            lane_of[ref.text] = ln.get("id")
    # pools ------------------------------------------------------------------------------------------------
    for p in parts:
        (x, y, w, h), _ = shapes[p.get("id")]
        pl = [ln for ln in lanes if ln.get("id") in shapes and _inside(shapes[ln.get("id")][0], (x, y, w, h))]
        head = pl and (shapes[pl[0].get("id")][0][0] - x) or 50
        if p.get("processRef"):
            st = style(swimlane=True, **base, fontStyle=0, horizontal=0, startSize=round(head), fillColor="#FFFFFF",
                       swimlaneFillColor="#FFFFFF", collapsible=0, container=1, whiteSpace="wrap", strokeWidth=1.5)
        else:                                  # black-box pool: no process, name in the middle
            st = style(rounded=0, **base, fillColor="#FFFFFF", whiteSpace="wrap", strokeWidth=1.5)
        ids[p.get("id")] = dw.vertex(x, y, w, h, html.escape(p.get("name", "")), st, cid="pool_" + p.get("id"))
        absb[p.get("id")] = (x, y, w, h)
        for ln in pl:
            (lx, ly, lw, lh), _ = shapes[ln.get("id")]
            lst = style(swimlane=True, **base, fontStyle=0, horizontal=0, startSize=30, fillColor="none", swimlaneFillColor="none",
                        collapsible=0, container=1, whiteSpace="wrap", strokeWidth=1)
            ids[ln.get("id")] = dw.vertex(lx - x, ly - y, lw, lh, html.escape(ln.get("name", "")), lst,
                                          parent=ids[p.get("id")], cid="lane_" + ln.get("id"))
            absb[ln.get("id")] = (lx, ly, lw, lh)
    # flow nodes ---------------------------------------------------------------------------------------------
    for eid, ((x, y, w, h), lb) in shapes.items():
        e = elems.get(eid)
        if e is None or eid in ids:
            continue
        tag = e.tag.replace(BP, "")
        nm = e.get("name", "") or ""
        par = lane_of.get(eid)
        if par is None:                       # data stores etc.: smallest pool/lane that contains it
            cands = [k for k, b in absb.items() if _inside((x, y, w, h), b)]
            par = min(cands, key=lambda k: absb[k][2] * absb[k][3]) if cands else None
        px, py = (absb[par][0], absb[par][1]) if par else (0, 0)
        parent = ids[par] if par else "1"
        ext = {}
        if lb:
            below = lb[1] + lb[3] / 2 > y + h / 2
            ext = dict(verticalLabelPosition="bottom" if below else "top", verticalAlign="top" if below else "bottom",
                       labelWidth=round(lb[2] + 6), labelBackgroundColor="none", spacing=0)
        if tag in TASK_MARK:
            st = style(shape="mxgraph.bpmn.task", **base, whiteSpace="wrap", rectStyle="rounded", size=10,
                       taskMarker=TASK_MARK[tag], fillColor="#FFFFFF", strokeWidth=1.5, verticalAlign="middle",
                       spacingLeft=6, spacingRight=6, spacingTop=10)
        elif tag in GW_TYPE:
            gw = {"exclusive": dict(outline="none", symbol="none", gwType="exclusive"),
                  "parallel": dict(outline="none", symbol="none", gwType="parallel"),
                  "inclusive": dict(outline="end", symbol="general"),
                  "eventBased": dict(outline="catching", symbol="multiple"),
                  "complex": dict(outline="none", symbol="none", gwType="complex")}[GW_TYPE[tag]]
            st = style(shape="mxgraph.bpmn.gateway2", **base, perimeter="rhombusPerimeter", **gw,
                       fillColor="#FFFFFF", whiteSpace="wrap", **(ext or {"verticalLabelPosition": "bottom", "verticalAlign": "top"}))
        elif tag.endswith("Event"):
            d = next((c.tag.replace(BP, "") for c in e if c.tag.endswith("EventDefinition")), None)
            outline = {"startEvent": "standard", "endEvent": "end", "intermediateCatchEvent": "catching",
                       "intermediateThrowEvent": "throwing", "boundaryEvent": "catching"}[tag]
            symbol = EV_SYM.get(d, "general")
            st = style(shape="mxgraph.bpmn.event", **base, perimeter="ellipsePerimeter", outline=outline,
                       symbol=symbol, fillColor="#FFFFFF", whiteSpace="wrap", **ext)
        elif tag == "dataStoreReference":
            st = style(shape="datastore", **base, fillColor="#FFFFFF", whiteSpace="wrap", **ext)
        elif tag == "dataObjectReference":
            st = style(shape="mxgraph.bpmn.data", **base, fillColor="#FFFFFF", whiteSpace="wrap", **ext)
        else:
            st = style(rounded=1, **base, whiteSpace="wrap")
        ids[eid] = dw.vertex(x - px, y - py, w, h, html.escape(nm), st, parent=parent, cid="n_" + eid)
        absb[eid] = (x, y, w, h)
    # flows -------------------------------------------------------------------------------------------------
    for eid, (pts, lb) in edges.items():
        e = elems.get(eid)
        if e is None:
            continue
        tag = e.tag.replace(BP, "")
        if tag == "dataOutputAssociation" or tag == "dataInputAssociation":
            src = e.getparent().get("id") if hasattr(e, "getparent") else None
            tref = e.find(BP + "targetRef")
            s_id = _owner(r, e)
            t_id = tref.text if tref is not None else None
            st = style(**base, endArrow="open", endFill=0, dashed=1, dashPattern="2 3", edgeStyle="none", rounded=0)
        else:
            s_id, t_id = e.get("sourceRef"), e.get("targetRef")
            if tag == "messageFlow":
                st = style(**base, endArrow="block", endFill=0, startArrow="oval", startFill=0, startSize=7,
                           dashed=1, dashPattern="8 5", edgeStyle="none", rounded=0)
            else:
                st = style(**base, endArrow="block", endFill=1, edgeStyle="none", rounded=0, strokeWidth=1.3)
        if t_id in absb:
            st += glue(dw, None, absb[t_id], pts[-1], "tgt")
        if s_id in absb:
            st += glue(dw, None, absb[s_id], pts[0], "src")
        nm = e.get("name", "") or ""
        lp = label_position(pts, (lb[0] + lb[2] / 2, lb[1] + lb[3] / 2)) if (lb and nm) else None
        if nm:
            st += f"labelBackgroundColor=#FFFFFF;fontSize={font - 1};"
        dw.edge(pts, html.escape(nm), st, src=ids.get(s_id), tgt=ids.get(t_id), label_pos=lp, cid="f_" + eid)
    return dw


def _owner(root, child):
    for el in root.iter():
        if child in list(el):
            return el.get("id")
    return None


def _inside(a, b, tol=1.0):
    return (a[0] >= b[0] - tol and a[1] >= b[1] - tol and a[0] + a[2] <= b[0] + b[2] + tol
            and a[1] + a[3] <= b[1] + b[3] + tol)


# ============================================================================================ Mermaid
SVGNS = "{http://www.w3.org/2000/svg}"


def _tf(s):
    """SVG transform attribute → 3x2 affine (a, b, c, d, e, f)."""
    m = (1, 0, 0, 1, 0, 0)
    for fn, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s or ""):
        v = [float(t) for t in re.split(r"[\s,]+", args.strip()) if t]
        if fn == "translate":
            n = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif fn == "scale":
            n = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif fn == "matrix":
            n = tuple(v)
        else:
            continue
        m = _mul(m, n)
    return m


def _mul(m, n):
    a, b, c, d, e, f = m
    A, B, C, D, E, F = n
    return (a * A + c * B, b * A + d * B, a * C + c * D, b * C + d * D, a * E + c * F + e, b * E + d * F + f)


def _ap(m, x, y):
    return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])


def _walk(el, m=(1, 0, 0, 1, 0, 0)):
    m = _mul(m, _tf(el.get("transform")))
    yield el, m
    for ch in el:
        yield from _walk(ch, m)


def parse_mmd(text):
    classdefs, nodes, cls_of, subgraphs, edges = {}, {}, {}, {}, []
    direction = "TB"
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith("%%"):
            continue
        if m := re.match(r"(?:flowchart|graph)\s+(\w+)", ln):
            direction = m.group(1); continue
        if m := re.match(r"classDef\s+(\w+)\s+(.*?);?$", ln):
            classdefs[m.group(1)] = dict(kv.split(":", 1) for kv in m.group(2).rstrip(";").split(","))
            continue
        if m := re.match(r"class\s+([\w,]+)\s+(\w+)", ln):
            for i in m.group(1).split(","):
                cls_of[i] = m.group(2)
            continue
        if m := re.match(r'subgraph\s+(\w+)\s*\["(.*)"\]', ln):
            subgraphs[m.group(1)] = m.group(2).strip(); continue
        if ln in ("end",) or ln.startswith("direction"):
            continue
        for m in re.finditer(r'(\w+)\["(.*?)"\](?::::(\w+))?', ln):
            nodes[m.group(1)] = m.group(2)
            if m.group(3):
                cls_of[m.group(1)] = m.group(3)
        if "~~~" in ln:
            continue
        em = re.match(r'(\w+)\s*(-->|-\.->|==>|---)\s*(.+)$', ln) or re.match(r'(\w+)\s*-\.\s*"(.*?)"\s*\.->\s*(\w+)', ln)
        if em and ("-->" in ln or "-.->" in ln or ".->" in ln or "==>" in ln):
            if (m := re.match(r'(\w+)\s*-\.\s*"(.*?)"\s*\.->\s*(\w+)', ln)):
                edges.append((m.group(1), m.group(3), m.group(2), "dashed"))
            else:
                chain = re.split(r"\s*(-->|-\.->|==>)\s*", ln)
                for i in range(0, len(chain) - 2, 2):
                    srcs = [re.match(r"(\w+)", s.strip()).group(1) for s in chain[i].split("&")]
                    tgts = [re.match(r"(\w+)", s.strip()).group(1) for s in chain[i + 2].split("&")]
                    for s in srcs:
                        for t in tgts:
                            edges.append((s, t, "", "dashed" if chain[i + 1] == "-.->" else "solid"))
    return dict(direction=direction, classdefs=classdefs, nodes=nodes, cls_of=cls_of, subgraphs=subgraphs,
                edges=edges)


def _path_pts(d):
    """M/L/Q/C/A/H/V/Z path → list of subpaths [(pts, closed)], Q/C control points kept as corners."""
    toks = re.findall(r"[MLQCTHVAZmlqcthvaz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    subs, cur, i, cmd, pos, closed = [], [], 0, None, (0, 0), False
    while i < len(toks):
        t = toks[i]
        if re.match(r"[A-Za-z]", t):
            cmd = t; i += 1
            if cmd in "Zz":
                closed = True
                if cur:
                    subs.append((cur, True)); cur = [cur[0]] if False else []
            continue
        def num(k):
            return [float(x) for x in toks[i:i + k]]
        if cmd in "Mm":
            x, y = num(2); i += 2
            if cmd == "m":
                x, y = pos[0] + x, pos[1] + y
            if cur:
                subs.append((cur, False))
            cur = [(x, y)]; pos = (x, y); cmd = "L" if cmd == "M" else "l"
        elif cmd in "Ll":
            x, y = num(2); i += 2
            if cmd == "l":
                x, y = pos[0] + x, pos[1] + y
            cur.append((x, y)); pos = (x, y)
        elif cmd in "Hh":
            x = num(1)[0]; i += 1; x = pos[0] + x if cmd == "h" else x
            cur.append((x, pos[1])); pos = (x, pos[1])
        elif cmd in "Vv":
            y = num(1)[0]; i += 1; y = pos[1] + y if cmd == "v" else y
            cur.append((pos[0], y)); pos = (pos[0], y)
        elif cmd in "Qq":
            cx, cy, x, y = num(4); i += 4
            cur.append(("Q", cx, cy)); cur.append((x, y)); pos = (x, y)
        elif cmd in "Tt":
            x, y = num(2); i += 2
            cur.append(("T",)); cur.append((x, y)); pos = (x, y)
        elif cmd in "Cc":
            c1x, c1y, c2x, c2y, x, y = num(6); i += 6
            cur.append(("C", c1x, c1y, c2x, c2y)); cur.append((x, y)); pos = (x, y)
        elif cmd in "Aa":
            x, y = num(7)[5:]; i += 7
            cur.append((x, y)); pos = (x, y)
        else:
            i += 1
    if cur:
        subs.append((cur, closed))
    return subs


def mermaid_to_drawio(mmd_path, svg_path, name, font=20):
    spec = parse_mmd(Path(mmd_path).read_text(encoding="utf-8"))
    root = ET.parse(svg_path).getroot()
    geo, clusters, paths, elabels = {}, {}, [], []
    for el, m in _walk(root):
        cl = el.get("class", "") or ""
        tag = el.tag.replace(SVGNS, "")
        if tag == "g" and cl.startswith("node") and el.get("id"):
            nid = re.sub(r"^my-svg-flowchart-(.+)-\d+$", r"\1", el.get("id"))
            r = next((c for c in el if c.tag == SVGNS + "rect"), None)
            if r is not None:
                x, y = _ap(m, float(r.get("x")), float(r.get("y")))
                geo[nid] = (x, y, float(r.get("width")), float(r.get("height")))
        elif tag == "g" and cl.startswith("cluster") and el.get("id"):
            cid = el.get("id").replace("my-svg-", "")
            r = next((c for c in el if c.tag == SVGNS + "rect"), None)
            x, y = _ap(m, float(r.get("x")), float(r.get("y")))
            clusters[cid] = (x, y, float(r.get("width")), float(r.get("height")))
        elif tag == "path" and "flowchart-link" in cl and "edge-thickness-invisible" not in cl:
            pts = []
            for p in _path_pts(el.get("d"))[0][0]:
                if p[0] == "Q":
                    pts.append(_ap(m, p[1], p[2]))
                elif p[0] in ("C", "T"):
                    continue
                else:
                    pts.append(_ap(m, *p))
            dashed = "edge-pattern-dashed" in cl or "edge-pattern-dotted" in cl
            paths.append((pts, dashed))
        elif tag == "g" and cl == "edgeLabel":
            fo = el.find(f".//{SVGNS}foreignObject")
            if fo is not None and float(fo.get("width", 0)) > 0:
                elabels.append(_ap(m, 0, 0))
    dw = Drawio(name)
    allb = {**geo, **clusters}
    ids = {}
    for cid, (x, y, w, h) in clusters.items():
        cd = spec["classdefs"].get(spec["cls_of"].get(cid, ""), {})
        st = style(rounded=0, html=1, fillColor=cd.get("fill", "#FAFAFA"), strokeColor=cd.get("stroke", "#808080"),
                   strokeWidth=_px(cd.get("stroke-width", "1px")), container=1, collapsible=0, fontFamily=FONT,
                   verticalAlign="top", fontColor="#000000")
        ids[cid] = dw.vertex(x, y, w, h, html.escape(spec["subgraphs"].get(cid, "").strip()), st, cid="sg_" + cid)
    for nid, (x, y, w, h) in geo.items():
        cd = spec["classdefs"].get(spec["cls_of"].get(nid, ""), {})
        par = next((c for c, b in clusters.items() if _inside((x, y, w, h), b)), None)
        px, py = (clusters[par][0], clusters[par][1]) if par else (0, 0)
        dash = cd.get("stroke-dasharray")
        st = style(rounded=0, whiteSpace="wrap", html=1, fontFamily=FONT, fontSize=font, fontColor="#000000",
                   fillColor=cd.get("fill", "#FFFFFF"), strokeColor=cd.get("stroke", "#000000").replace("#000", "#000000") if len(cd.get("stroke", "")) == 4 else cd.get("stroke", "#000000"),
                   strokeWidth=_px(cd.get("stroke-width", "1px")),
                   fontStyle=1 if cd.get("font-weight") == "bold" else 0,
                   dashed=1 if dash else None, dashPattern=dash.replace(",", " ") if dash else None,
                   spacingLeft=4, spacingRight=4)
        lines = spec["nodes"].get(nid, nid).split("<br/>")
        ids[nid] = dw.vertex(x - px, y - py, w, h, hlabel(lines), st, parent=ids[par] if par else "1", cid="n_" + nid)
    # edges: endpoints → owning boxes (geometrically), labels from the source in order
    lab_edges = [e for e in spec["edges"] if e[2]]
    for pts, dashed in paths:
        s = _hit(allb, pts[0]); t = _hit(allb, pts[-1])
        st = style(html=1, endArrow="block", endFill=1, endSize=8, rounded=0, edgeStyle="none",
                   strokeColor="#000000", fontFamily=FONT, fontSize=font - 2, dashed=1 if dashed else None,
                   dashPattern="6 4" if dashed else None, labelBackgroundColor="#FFFFFF")
        if s:
            st += glue(dw, None, allb[s], pts[0], "src")
        if t:
            st += glue(dw, None, allb[t], pts[-1], "tgt")
        value, lp = "", None
        le = next((e for e in lab_edges if e[0] == s and e[1] == t), None)
        if le and elabels:
            c = min(elabels, key=lambda q: min(math.dist(q, p) for p in _densify(pts)))
            value, lp = html.escape(le[2]), label_position(pts, c)
        dw.edge(pts, value, st, src=ids.get(s), tgt=ids.get(t), label_pos=lp)
    return dw


def _px(v):
    return re.sub(r"[^\d.]", "", str(v)) or "1"


def _densify(pts, step=10):
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.dist(a, b) // step))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n + 1)]
    return out or pts


def _hit(boxes, p, tol=4):
    best = None
    for k, (x, y, w, h) in boxes.items():
        if x - tol <= p[0] <= x + w + tol and y - tol <= p[1] <= y + h + tol:
            d = min(abs(p[0] - x), abs(p[0] - x - w), abs(p[1] - y), abs(p[1] - y - h))
            if d <= tol and (best is None or w * h < boxes[best][2] * boxes[best][3]):
                best = k
    return best


# ============================================================================================ generic SVG
def _num(v, default=0.0):
    try:
        return float(re.sub(r"[^\d.\-e]", "", str(v)))
    except (TypeError, ValueError):
        return default


def _paint(el):
    """fill, stroke, stroke-width, dasharray from attributes and inline style."""
    st = dict(re.findall(r"([\w-]+)\s*:\s*([^;]+)", el.get("style", "") or ""))
    g = lambda k, d=None: el.get(k) or st.get(k) or d
    fill = g("fill", "#000")
    if _num(g("fill-opacity", "1"), 1.0) == 0:
        fill = "none"
    return dict(fill=fill, stroke=g("stroke", "none"), sw=_num(g("stroke-width", "1"), 1.0),
                dash=g("stroke-dasharray"), font_size=_num(g("font-size", "15"), 15), weight=g("font-weight", ""),
                italic=g("font-style", "") == "italic", anchor=g("text-anchor", "start"))


def _col(c):
    if not c or c == "none":
        return "none"
    c = c.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", c):
        c = "#" + "".join(ch * 2 for ch in c[1:])
    return c.upper() if c.startswith("#") else {"black": "#000000", "white": "#FFFFFF"}.get(c, c)


def _convex(poly):
    sgn = 0
    n = len(poly)
    for i in range(n):
        a, b, c = poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
        z = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(z) < 1e-6:
            continue
        s = 1 if z > 0 else -1
        if sgn and s != sgn:
            return False
        sgn = s
    return True


def _pip(p, poly):
    x, y, ins = p[0], p[1], False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
            ins = not ins
    return ins


def svg_to_drawio(svg_path, name, skip_glyphs=True):
    root = ET.parse(svg_path).getroot()
    shapes, lines, polys, texts = [], [], [], []
    vb = [float(v) for v in (root.get("viewBox") or "0 0 0 0").split()]
    for el, m in _walk(root):
        tag = el.tag.replace(SVGNS, "")
        p = _paint(el)
        if tag == "rect" and el.get("width") not in (None, "100%"):
            x, y = _ap(m, _num(el.get("x")), _num(el.get("y")))
            w, h = _num(el.get("width")), _num(el.get("height"))
            if w <= 0 or h <= 0:
                continue
            shapes.append(dict(kind="rect", box=(x, y, w, h), rx=_num(el.get("rx"), 0), **p))
        elif tag in ("ellipse", "circle"):
            cx, cy = _ap(m, _num(el.get("cx")), _num(el.get("cy")))
            rx = _num(el.get("rx") or el.get("r")); ry = _num(el.get("ry") or el.get("r"))
            shapes.append(dict(kind="ellipse", box=(cx - rx, cy - ry, 2 * rx, 2 * ry), rx=0, **p))
        elif tag in ("polyline", "line"):
            if tag == "line":
                pts = [_ap(m, _num(el.get("x1")), _num(el.get("y1"))), _ap(m, _num(el.get("x2")), _num(el.get("y2")))]
            else:
                v = [float(t) for t in re.split(r"[\s,]+", el.get("points").strip())]
                pts = [_ap(m, v[i], v[i + 1]) for i in range(0, len(v), 2)]
            lines.append(dict(pts=pts, curve=None, **p))
        elif tag == "polygon":
            v = [float(t) for t in re.split(r"[\s,]+", el.get("points").strip())]
            pts = [_ap(m, v[i], v[i + 1]) for i in range(0, len(v), 2)]
            uniq = []
            for q in pts:
                if not any(math.dist(q, u) < 0.3 for u in uniq):
                    uniq.append(q)
            polys.append(dict(pts=uniq, **p))
        elif tag == "path":
            subs = _path_pts(el.get("d", ""))
            # glyph outlines (PlantUML class icon letters) are dropped, the icon gets a text label instead
            if skip_glyphs and p["fill"] not in ("none",) and len(el.get("d", "")) > 200:
                continue
            for pts, closed in subs:
                simple = [_ap(m, *q) for q in pts if not isinstance(q[0], str)]
                if len(simple) < 2:
                    continue
                curve = [q for q in pts if isinstance(q[0], str)]
                if closed and p["fill"] not in ("none",) and len(simple) >= 3:
                    polys.append(dict(pts=simple, closed_path=True, **p))
                else:
                    if curve and curve[0][0] in ("Q",):
                        # squiggle (Q … T …): pass through the control-point midpoints, drawn curved
                        q = curve[0]
                        c1 = _ap(m, q[1], q[2])
                        mid = simple[1]
                        simple = [simple[0], ((simple[0][0] + c1[0]) / 2 * 0 + c1[0], c1[1]), mid,
                                  (2 * mid[0] - c1[0], 2 * mid[1] - c1[1]), simple[-1]]
                        lines.append(dict(pts=simple, curve="squiggle", **p))
                    elif curve and curve[0][0] == "C":
                        lines.append(dict(pts=[simple[0], simple[-1]], curve=None, **p))
                    else:
                        lines.append(dict(pts=simple, curve=None, closed=closed, **p))
        elif tag == "text":
            tsp = [t for t in el if t.tag == SVGNS + "tspan"]
            size = p["font_size"]
            bold = p["weight"] == "bold"
            items = []
            if tsp:
                for t in tsp:
                    items.append((_num(t.get("x", el.get("x"))), _num(t.get("y", el.get("y"))), "".join(t.itertext())))
            else:
                items.append((_num(el.get("x")), _num(el.get("y")), "".join(el.itertext())))
            ls = []
            for x, y, s in items:
                x, y = _ap(m, x, y)
                tl = _num(el.get("textLength"), 0) if not tsp else 0
                w = tl or text_w(s, size, bold)
                x0 = x - w / 2 if p["anchor"] == "middle" else x - w if p["anchor"] == "end" else x
                ls.append(dict(x0=x0, w=w, base=y, s=s))
            if not ls or not "".join(l["s"] for l in ls).strip():
                continue
            texts.append(dict(lines=ls, size=size, bold=bold, italic=p["italic"], color=_col(p["fill"]),
                              anchor=p["anchor"]))
    shapes = [s for s in shapes if not (s["fill"] == "none" and s["stroke"] in ("none", None))]
    # drop the page background
    W, H = (vb[2], vb[3]) if vb[2] else (0, 0)
    shapes = [s for s in shapes if not (s["box"][0] <= 0.5 and s["box"][1] <= 0.5 and
                                        (s["box"][2] >= W - 1 and s["box"][3] >= H - 1)) or s["stroke"] not in ("none", None)]
    shapes = [s for s in shapes if not (s["fill"] in ("#fff", "#FFFFFF", "#ffffff", "white") and s["stroke"] in ("none", None)
                                        and s["box"][2] * s["box"][3] > 0.6 * W * H)]
    # head / diamond classification of polygons ------------------------------------------------------------
    heads = []
    for pg in polys:
        pts = pg["pts"]
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        bw, bh = max(xs) - min(xs), max(ys) - min(ys)
        pg["box"] = (min(xs), min(ys), bw, bh)
        small = max(bw, bh) <= 20 and len(pts) in (3, 4)
        pg["role"] = "head" if small else "shape"
        if small:
            heads.append(pg)
    # edges: attach heads (tip extension), glue to leaf shapes ---------------------------------------------
    for ln in lines:
        ln.setdefault("start", None); ln.setdefault("end", None)
        for end in ("end", "start"):
            pts = ln["pts"]
            p_end, p_prev = (pts[-1], pts[-2]) if end == "end" else (pts[0], pts[1])
            for hd in heads:
                if hd.get("used"):
                    continue
                near = any(math.dist(p_end, q) < 1.6 for q in hd["pts"]) or _pip(p_end, hd["pts"])
                if not near:
                    continue
                tip = max(hd["pts"], key=lambda q: math.dist(q, p_prev))
                if len(hd["pts"]) == 3:
                    kind = "block"
                elif _convex(hd["pts"]):
                    kind = "diamondThin"
                else:
                    kind = "block"
                fill = 0 if _col(hd["fill"]) in ("#FFFFFF", "none") else 1
                ln[end] = (kind, fill)
                if end == "end":
                    pts[-1] = tip
                else:
                    pts[0] = tip
                hd["used"] = True
                break
    # shape hierarchy: big shapes are containers, texts and tiny shapes go to the smallest enclosing leaf
    for s in shapes + [p for p in polys if p["role"] == "shape"]:
        s.setdefault("kind", "poly")
    allshapes = shapes + [p for p in polys if p["role"] == "shape"]
    for i, s_ in enumerate(allshapes):
        s_["z"] = i
    for s in allshapes:
        s["leaf"] = not any(o is not s and o["box"][2] * o["box"][3] > 1200 and _inside(o["box"], s["box"], 0.5)
                            and o["box"][2] * o["box"][3] < s["box"][2] * s["box"][3] for o in allshapes)
    dw = Drawio(name)
    order = sorted(allshapes, key=lambda s: -s["box"][2] * s["box"][3])
    for s in order:
        s["parent"] = None
        if s["box"][2] * s["box"][3] <= 1200:
            cands = [o for o in allshapes if o is not s and o["leaf"] and o["box"][2] * o["box"][3] > 1200
                     and _inside(s["box"], o["box"], 0.5)]
            if cands:
                s["parent"] = min(cands, key=lambda o: o["box"][2] * o["box"][3])
    # assign texts
    for t in texts:
        x0 = min(l["x0"] for l in t["lines"]); x1 = max(l["x0"] + l["w"] for l in t["lines"])
        y0 = min(l["base"] for l in t["lines"]) - t["size"] * 0.82
        y1 = max(l["base"] for l in t["lines"]) + t["size"] * 0.3
        t["box"] = (x0, y0, x1 - x0, y1 - y0)
        c = (x0 + (x1 - x0) / 2, y0 + (y1 - y0) / 2)
        cands = [s for s in allshapes if s["leaf"] and s["box"][0] <= c[0] <= s["box"][0] + s["box"][2]
                 and s["box"][1] <= c[1] <= s["box"][1] + s["box"][3]]
        t["owner"] = min(cands, key=lambda s: (round(s["box"][2] * s["box"][3]), -s["z"])) if cands else None
    # merge centred texts into the owner label
    for s in allshapes:
        own = [t for t in texts if t["owner"] is s]
        if not own:
            continue
        x, y, w, h = s["box"]
        allc = all(abs(l["x0"] + l["w"] / 2 - (x + w / 2)) < 7 for t in own for l in t["lines"])
        ys = [l["base"] for t in own for l in t["lines"]]
        sz = own[0]["size"]
        cy = (min(ys) - sz * 0.82 + max(ys) + sz * 0.18) / 2
        same = len({(t["size"], t["bold"], t["color"]) for t in own}) == 1
        if allc and same and abs(cy - (y + h / 2)) < 3.5:
            ls = sorted((l for t in own for l in t["lines"]), key=lambda l: l["base"])
            s["label"] = (hlabel([l["s"] for l in ls]), own[0])
            for t in own:
                t["merged"] = True
    # emit shapes
    ids = {}
    for s in order:
        x, y, w, h = s["box"]
        par = s.get("parent")
        if par is None:
            for o in order:      # children of leaf shapes (icons) are emitted after their parent
                pass
        fill = _col(s["fill"])
        stroke = _col(s["stroke"])
        base = dict(html=1, whiteSpace="wrap", fontFamily=FONT, fillColor=fill, strokeColor=stroke,
                    strokeWidth=round(s["sw"], 2), dashed=1 if s.get("dash") else None,
                    dashPattern=re.sub(r"[,\s]+", " ", s["dash"]) if s.get("dash") else None, fontColor="#000000",
                    spacing=2)
        lab = ""
        if s.get("label"):
            lab, t = s["label"]
            base.update(fontSize=_fmt(t["size"]), fontStyle=(1 if t["bold"] else 0) + (2 if t["italic"] else 0),
                        fontColor=t["color"] if t["color"] != "none" else "#000000")
        elif s["kind"] == "ellipse" and w < 30 and any(t.get("glyph") for t in []):
            pass
        if s["kind"] == "rect":
            st = style(rounded=1 if s["rx"] else 0, absoluteArcSize=1 if s["rx"] else None,
                       arcSize=_fmt(2 * s["rx"]) if s["rx"] else None, **base)
        elif s["kind"] == "ellipse":
            st = style(ellipse=True, **base)
        else:
            pts = s["pts"]
            if len(pts) == 4 and _convex(pts):
                st = style(rhombus=True, **base)
            elif len(pts) == 3:
                st = style(triangle=True, **base)
            else:
                st = style(shape=_poly_stencil(pts, s["box"]), **base)
        px, py = (par["box"][0], par["box"][1]) if par else (0, 0)
        s["id"] = dw.vertex(x - px, y - py, w, h, lab, st, parent=ids.get(id(par), "1"))
        ids[id(s)] = s["id"]
        if s["kind"] == "ellipse" and w < 30 and par is not None and not lab:
            # PlantUML class icon: letter in the circle
            dw.cells[-1]["value"] = "C"
            dw.cells[-1]["style"] += f"fontSize=13;fontStyle=1;"
    # edges
    for ln in lines:
        pts = ln["pts"]
        if len(pts) < 2:
            continue
        sw = round(ln["sw"], 2)
        ox = None
        # separators inside a leaf box → line shapes owned by the box
        if len(pts) == 2 and not ln["start"] and not ln["end"] and (abs(pts[0][1] - pts[1][1]) < 0.5
                                                                  or abs(pts[0][0] - pts[1][0]) < 0.5):
            lb = (min(pts[0][0], pts[1][0]), min(pts[0][1], pts[1][1]), abs(pts[1][0] - pts[0][0]),
                  abs(pts[1][1] - pts[0][1]))
            own = [s for s in allshapes if s["leaf"] and s["kind"] == "rect" and _inside(lb, s["box"], 1.5)]
            if own:
                ox = min(own, key=lambda s: s["box"][2] * s["box"][3])
        st = dict(html=1, endArrow="none", startArrow="none", rounded=0, edgeStyle="none",
                  strokeColor=_col(ln["stroke"]) if ln["stroke"] != "none" else "#000000", strokeWidth=sw,
                  dashed=1 if ln.get("dash") else None,
                  dashPattern=re.sub(r"[,\s]+", " ", ln["dash"]) if ln.get("dash") else None,
                  curved=1 if ln["curve"] else None)
        if ln["end"]:
            st.update(endArrow=ln["end"][0], endFill=ln["end"][1], endSize=10 if ln["end"][0] == "diamondThin" else 7)
        if ln["start"]:
            st.update(startArrow=ln["start"][0], startFill=ln["start"][1],
                      startSize=10 if ln["start"][0] == "diamondThin" else 7)
        if ox is not None:
            x, y, w, h = ox["box"]
            dw.edge([(pts[0][0] - x, pts[0][1] - y), (pts[1][0] - x, pts[1][1] - y)], "", style(**st),
                    parent=ox["id"])
            continue
        sst = style(**st)
        src = tgt = None
        if not ln["curve"]:
            leaves = {i: s["box"] for i, s in enumerate(allshapes) if s["leaf"] and s["box"][2] * s["box"][3] > 1200}
            a = _hit(leaves, pts[0], 2.5)
            b = _hit(leaves, pts[-1], 2.5)
            if a is not None:
                src = allshapes[a]["id"]; sst += glue(dw, None, leaves[a], pts[0], "src")
            if b is not None:
                tgt = allshapes[b]["id"]; sst += glue(dw, None, leaves[b], pts[-1], "tgt")
        dw.edge(pts, "", sst, src=src, tgt=tgt)
    # loose heads (not attached to a line) stay as small triangles
    for hd in heads:
        if hd.get("used"):
            continue
        x, y, w, h = hd["box"]
        st = style(shape=_poly_stencil(hd["pts"], hd["box"]), html=1, fillColor=_col(hd["fill"]),
                   strokeColor=_col(hd["stroke"]) if hd["stroke"] != "none" else "#000000", strokeWidth=1)
        dw.vertex(x, y, max(w, 1), max(h, 1), "", st)
    # z-order: top-level connectors under the shapes (label backgrounds then mask the lines, as in the SVG)
    cont = {s_["id"] for s_ in allshapes if not s_["leaf"]}
    dw.cells.sort(key=lambda c: 0 if c["id"] in cont else 1 if (c["kind"] == "e" and c["parent"] == "1") else 2)
    # free / child texts
    for t in texts:
        if t.get("merged"):
            continue
        x, y, w, h = t["box"]
        lines_ = sorted(t["lines"], key=lambda l: l["base"])
        align = {"middle": "center", "end": "right"}.get(t["anchor"], "left")
        if len(lines_) == 1:
            align = "left" if t["anchor"] == "start" else align
        st = style(**TEXT_ST, fontSize=_fmt(t["size"]), align=align,
                   fontStyle=(1 if t["bold"] else 0) + (2 if t["italic"] else 0) or None,
                   fontColor=t["color"] if t["color"] not in ("none",) else "#000000")
        n = len(lines_)
        hh = n * t["size"] * 1.18
        yy = lines_[0]["base"] - t["size"] * 1.06
        ww = w + 4
        xx = x - (2 if align == "left" else 2)
        own = t["owner"]
        if own is not None:
            dw.vertex(xx - own["box"][0], yy - own["box"][1], ww, hh, hlabel([l["s"] for l in lines_]), st,
                      parent=own["id"])
        else:
            dw.vertex(xx, yy, ww, hh, hlabel([l["s"] for l in lines_]), st)
    return dw


def _fmt(v):
    return f"{v:g}" if isinstance(v, (int, float)) else v


def _poly_stencil(pts, box):
    """Arbitrary polygon as an inline draw.io stencil (shape=stencil(...)), coordinates in 0..100."""
    import base64, zlib
    from urllib.parse import quote
    x, y, w, h = box
    w = w or 1; h = h or 1
    path = "".join(f'<{"move" if i == 0 else "line"} x="{(p[0] - x) / w * 100:.2f}" y="{(p[1] - y) / h * 100:.2f}"/>'
                   for i, p in enumerate(pts))
    xml = (f'<shape w="100" h="100" aspect="variable" strokewidth="inherit"><connections/><foreground>'
           f'<path>{path}<close/></path><fillstroke/></foreground></shape>')
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    data = comp.compress(quote(xml, safe="~()*!.'").encode()) + comp.flush()
    return "stencil(" + base64.b64encode(data).decode() + ")"
