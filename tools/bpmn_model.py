#!/usr/bin/env python3
"""Grid-layout BPMN 2.0 generator + renderer with legibility gate.

A diagram is described as a Python dict (see lab2/make_lab2.py):

    {"id": "p_monitor", "pools": [
        {"id": "P1", "name": "...", "lanes": [{"id": "L1", "name": "Роль"}, ...],
         "nodes": [{"id": "s1", "type": "start", "marker": "message", "lane": "L1", "col": 0, "label": "..."},
                   {"id": "t1", "type": "task", "kind": "user", "lane": "L1", "col": 1, "row": 0, "label": "..."},
                   {"id": "g1", "type": "xor", "lane": "L1", "col": 2, "label": "Ціль підтверджено?"}, ...],
         "flows": [("s1", "t1"), ("t1", "g1"), ("g1", "t2", "так"), ...],
         "data": [{"id": "d1", "type": "store", "lane": "L2", "col": 3, "row": 1, "label": "...",
                   "links": [("t3", "out")]}]},
        {"id": "P2", "name": "Сенсорна мережа", "collapsed": True}],
     "messages": [("P2", "s1", "Виявлення"), ("t5", "P3", "Бойове завдання")],
     "annotations": [{"id": "a1", "pool": "P1", "lane": "L1", "col": 5, "row": 1, "text": "...", "to": "t5"}]}

Node types: start | end | intermediate (catch) | throw | task | subprocess | xor | and | or | event_gw
Event markers: none | message | timer | signal | error | terminate | conditional
Task kinds: none | user | service | send | receive | manual | script | rule

Layout: variable-width columns (narrow for events/gateways), lanes = rows of pools, optional sub-rows inside
a lane (`row`), orthogonal sequence-flow routing, message flows routed vertically between pools.

CLI:  .venv/bin/python tools/bpmn_model.py <file.bpmn>   (render an existing .bpmn + legibility gate)
"""
import json, subprocess, sys
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
FONT_PX = 16
SIZES = {"task": (164, 88), "subprocess": (164, 88), "start": (40, 40), "end": (40, 40),
         "intermediate": (40, 40), "throw": (40, 40), "xor": (54, 54), "and": (54, 54), "or": (54, 54),
         "event_gw": (54, 54), "store": (54, 50), "object": (40, 52), "annotation": (164, 60)}
COLW = {"task": 184, "subprocess": 184, "annotation": 184}           # others: narrow columns
NARROW = 96
ROW_H = 118
POOL_HDR, LANE_HDR, PAD_X = 50, 50, 8
POOL_GAP = 40
COLLAPSED_H = 64
EVENT_TAG = {"start": "startEvent", "end": "endEvent", "intermediate": "intermediateCatchEvent",
             "throw": "intermediateThrowEvent"}
TASK_TAG = {"none": "task", "user": "userTask", "service": "serviceTask", "send": "sendTask",
            "receive": "receiveTask", "manual": "manualTask", "script": "scriptTask", "rule": "businessRuleTask"}
GW_TAG = {"xor": "exclusiveGateway", "and": "parallelGateway", "or": "inclusiveGateway",
          "event_gw": "eventBasedGateway"}
DEF_TAG = {"message": "messageEventDefinition", "timer": "timerEventDefinition",
           "signal": "signalEventDefinition", "error": "errorEventDefinition",
           "terminate": "terminateEventDefinition", "conditional": "conditionalEventDefinition",
           "link": "linkEventDefinition"}


def esc(s):
    return escape(str(s), {'"': "&quot;"})


class Layout:
    def __init__(self, spec):
        self.spec = spec
        self.shapes = {}      # id -> (x, y, w, h)
        self.pool_box = {}    # pool id -> (x, y, w, h)
        self.lane_box = {}    # lane id -> (x, y, w, h)
        self.node_pool = {}
        self.node_lane = {}
        self.ntype = {n["id"]: n["type"] for p in spec["pools"] for n in p.get("nodes", [])}
        self._compute()

    def _compute(self):
        pools = self.spec["pools"]
        ncols = 0
        colw = {}
        for p in pools:
            for n in p.get("nodes", []) + p.get("data", []):
                c = n["col"]; ncols = max(ncols, c + 1)
                colw[c] = max(colw.get(c, NARROW), COLW.get(n["type"], NARROW))
            for a in self.spec.get("annotations", []):
                if a["pool"] == p["id"]:
                    ncols = max(ncols, a["col"] + 1); colw[a["col"]] = max(colw.get(a["col"], NARROW), 184)
        xs, x = [], POOL_HDR + LANE_HDR + PAD_X
        for c in range(ncols):
            xs.append(x); x += colw.get(c, NARROW)
        self.col_x, self.col_w = xs, colw
        width = x + PAD_X
        if self.spec.get("free"):                     # hand-placed collapsed pools (interaction map)
            for p in pools:
                self.pool_box[p["id"]] = tuple(p["box"])
            self.width = max(b[0] + b[2] for b in self.pool_box.values())
            self.height = max(b[1] + b[3] for b in self.pool_box.values())
            return
        y = 0
        slot_y = {}
        for p in pools:
            if p.get("collapsed"):
                # pools sharing a "slot" sit side by side; "cols": (a, b) limits the x-range
                yy = slot_y.setdefault(p["slot"], y) if p.get("slot") else y
                x0, x1 = 0, width
                if p.get("cols"):
                    a, b = p["cols"]
                    x0 = 0 if a == 0 else xs[a] - 4
                    x1 = width if b == ncols - 1 else xs[b] + colw.get(b, NARROW) + 4
                self.pool_box[p["id"]] = (x0, yy, x1 - x0, COLLAPSED_H)
                if yy == y:
                    y += COLLAPSED_H + POOL_GAP
                continue
            py = y
            for lane in p["lanes"]:
                rows = 1 + max([n.get("row", 0) for n in p.get("nodes", []) + p.get("data", [])
                                if n["lane"] == lane["id"]] +
                               [a.get("row", 0) for a in self.spec.get("annotations", [])
                                if a.get("lane") == lane["id"]] + [0])
                h = rows * ROW_H
                self.lane_box[lane["id"]] = (POOL_HDR, y, width - POOL_HDR, h)
                lane["_y"], lane["_h"] = y, h
                y += h
            self.pool_box[p["id"]] = (0, py, width, y - py)
            y += POOL_GAP
            for n in p.get("nodes", []) + p.get("data", []):
                self._place(n, p)
        for a in self.spec.get("annotations", []):
            pool = next(p for p in pools if p["id"] == a["pool"])
            self._place(dict(a, type="annotation"), pool, key=a["id"])
        self.width, self.height = width, y - POOL_GAP

    def _place(self, n, pool, key=None):
        lane = next(l for l in pool["lanes"] if l["id"] == n["lane"])
        w, h = SIZES[n["type"]]
        cx = self.col_x[n["col"]] + self.col_w.get(n["col"], NARROW) / 2
        cy = lane["_y"] + n.get("row", 0) * ROW_H + ROW_H / 2
        self.shapes[key or n["id"]] = (cx - w / 2, cy - h / 2, w, h)
        self.node_pool[key or n["id"]] = pool["id"]
        self.node_lane[key or n["id"]] = n["lane"]

    def stacked(self, nid, up=True):
        """True if another shape of the same pool sits in the same column above (up) / below `nid`."""
        b = self.shapes[nid]; cx = b[0] + b[2] / 2
        for o, ob in self.shapes.items():
            if o == nid or self.node_pool.get(o) != self.node_pool.get(nid):
                continue
            if abs((ob[0] + ob[2] / 2) - cx) < ob[2] / 2 + 22 and ((ob[1] < b[1]) if up else (ob[1] > b[1])):
                return True
        return False

    # --- routing
    @staticmethod
    def c(b):
        x, y, w, h = b
        return x + w / 2, y + h / 2

    def seq_waypoints(self, s, t, s_type, t_type):
        sb, tb = self.shapes[s], self.shapes[t]
        sx, sy = self.c(sb); tx, ty = self.c(tb)
        sr, tl = sb[0] + sb[2], tb[0]
        gw = ("xor", "and", "or", "event_gw")
        if abs(sy - ty) < 1 and tx > sx:
            return [(sr, sy), (tl, ty)]
        if abs(sx - tx) < 1:                                   # same column, vertical
            return [(sx, sb[1] + sb[3]), (tx, tb[1])] if ty > sy else [(sx, sb[1]), (tx, tb[1] + tb[3])]
        if tx > sx:
            if s_type in gw:                                   # branch leaves gateway from top/bottom vertex
                vy = sb[1] + sb[3] if ty > sy else sb[1]
                return [(sx, vy), (sx, ty), (tl, ty)]
            if t_type in gw:                                   # merge enters gateway from top/bottom vertex
                vy = tb[1] if ty > sy else tb[1] + tb[3]
                return [(sr, sy), (tx, sy), (tx, vy)]
            mx = sr + (tl - sr) / 2
            return [(sr, sy), (mx, sy), (mx, ty), (tl, ty)]
        # backward flow (loop): run just above the bottom edge of the lower lane, clear of the tasks
        lower = s if sb[1] + sb[3] >= tb[1] + tb[3] else t
        lb = self.lane_box[self.node_lane[lower]]
        yb = lb[1] + lb[3] - 8
        return [(sx, sb[1] + sb[3]), (sx, yb), (tx, yb), (tx, tb[1] + tb[3])]

    def msg_waypoints(self, s, t):
        sb = self.shapes.get(s) or self.pool_box[s]
        tb = self.shapes.get(t) or self.pool_box[t]
        s_is_pool, t_is_pool = s not in self.shapes, t not in self.shapes
        sx, sy = self.c(sb); tx, ty = self.c(tb)
        ev = ("start", "end", "intermediate", "throw")
        st, tt = self.ntype.get(s), self.ntype.get(t)
        if st in ("task", "subprocess"):
            sx += 30                                  # keep clear of sequence flows that use the centre
        if tt in ("task", "subprocess"):
            tx += 30
        # events: straight vertical unless another shape is in the way -> attach to the right side
        if st in ev and t_is_pool:
            down = ty > sy
            if self.stacked(s, up=not down):
                xr = sb[0] + sb[2] + 16
                y2 = tb[1] if down else tb[1] + tb[3]
                return [(sb[0] + sb[2], sy), (xr, sy), (xr, y2)]
        if tt in ev and s_is_pool:
            from_below = sy > ty
            if self.stacked(t, up=not from_below):
                xr = tb[0] + tb[2] + 16
                y1 = sb[1] if from_below else sb[1] + sb[3]
                return [(xr, y1), (xr, ty), (tb[0] + tb[2], ty)]
        if s_is_pool and not t_is_pool:
            sx = tx
        if t_is_pool and not s_is_pool:
            tx = sx
        down = ty > sy
        y1 = sb[1] + sb[3] if down else sb[1]
        y2 = tb[1] if down else tb[1] + tb[3]
        if abs(sx - tx) < 1:
            return [(sx, y1), (tx, y2)]
        my = (y1 + y2) / 2
        return [(sx, y1), (sx, my), (tx, my), (tx, y2)]


def build_xml(spec):
    L = Layout(spec)
    out, di = [], []
    pools = spec["pools"]
    node_type = {}
    for p in pools:
        for n in p.get("nodes", []):
            node_type[n["id"]] = n["type"]
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
               'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
               'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
               'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
               f'id="Defs_{spec["id"]}" targetNamespace="http://knu.ua/pis/shchyt-link" '
               'exporter="tools/bpmn_model.py" exporterVersion="1.0">')
    collab = f'Collab_{spec["id"]}'
    out.append(f'  <bpmn:collaboration id="{collab}">')
    for p in pools:
        ref = "" if p.get("collapsed") else f' processRef="Proc_{p["id"]}"'
        out.append(f'    <bpmn:participant id="{p["id"]}" name="{esc(p["name"])}"{ref}/>')
    for i, m in enumerate(spec.get("messages", [])):
        s, t, lbl = (m["s"], m["t"], m.get("label", "")) if isinstance(m, dict) else (m + ("",))[:3]
        out.append(f'    <bpmn:messageFlow id="MF_{spec["id"]}_{i}" sourceRef="{s}" targetRef="{t}" name="{esc(lbl)}"/>')
    for a in spec.get("annotations", []):
        out.append(f'    <bpmn:textAnnotation id="{a["id"]}"><bpmn:text>{esc(a["text"])}</bpmn:text></bpmn:textAnnotation>')
        if a.get("to"):
            out.append(f'    <bpmn:association id="As_{a["id"]}" sourceRef="{a["to"]}" targetRef="{a["id"]}"/>')
    out.append('  </bpmn:collaboration>')

    for p in pools:
        if p.get("collapsed"):
            continue
        out.append(f'  <bpmn:process id="Proc_{p["id"]}" isExecutable="false">')
        out.append(f'    <bpmn:laneSet id="LS_{p["id"]}">')
        for lane in p["lanes"]:
            out.append(f'      <bpmn:lane id="{lane["id"]}" name="{esc(lane["name"])}">')
            for n in p.get("nodes", []):
                if n["lane"] == lane["id"]:
                    out.append(f'        <bpmn:flowNodeRef>{n["id"]}</bpmn:flowNodeRef>')
            out.append('      </bpmn:lane>')
        out.append('    </bpmn:laneSet>')
        flows = [tuple(f) + ("",) * (3 - len(f)) for f in p.get("flows", [])]
        fid = {(s, t): f'SF_{p["id"]}_{k}' for k, (s, t, _) in enumerate(flows)}
        assoc_in = {}
        assoc_out = {}
        for d in p.get("data", []):
            for (tid, direction) in d.get("links", []):
                (assoc_out if direction == "out" else assoc_in).setdefault(tid, []).append(d["id"])
        for n in p.get("nodes", []):
            t, nid_, lbl = n["type"], n["id"], esc(n.get("label", ""))
            inc = [fid[(s, x)] for (s, x, _) in flows if x == nid_]
            outg = [fid[(s, x)] for (s, x, _) in flows if s == nid_]
            refs = "".join(f"<bpmn:incoming>{r}</bpmn:incoming>" for r in inc) + \
                   "".join(f"<bpmn:outgoing>{r}</bpmn:outgoing>" for r in outg)
            if t in EVENT_TAG:
                mk = n.get("marker", "none")
                body = f'<bpmn:{DEF_TAG[mk]} id="ED_{nid_}"/>' if mk in DEF_TAG else ""
                if mk == "link":
                    body = f'<bpmn:linkEventDefinition id="ED_{nid_}" name="{esc(n.get("link", "A"))}"/>'
                if mk == "conditional":
                    body = f'<bpmn:conditionalEventDefinition id="ED_{nid_}"><bpmn:condition/></bpmn:conditionalEventDefinition>'
                out.append(f'    <bpmn:{EVENT_TAG[t]} id="{nid_}" name="{lbl}">{refs}{body}</bpmn:{EVENT_TAG[t]}>')
            elif t == "task":
                tag = TASK_TAG[n.get("kind", "none")]
                da = ""
                for k, d in enumerate(assoc_in.get(nid_, [])):
                    da += f'<bpmn:dataInputAssociation id="DIA_{nid_}_{k}"><bpmn:sourceRef>{d}</bpmn:sourceRef></bpmn:dataInputAssociation>'
                for k, d in enumerate(assoc_out.get(nid_, [])):
                    da += f'<bpmn:dataOutputAssociation id="DOA_{nid_}_{k}"><bpmn:targetRef>{d}</bpmn:targetRef></bpmn:dataOutputAssociation>'
                loop = '<bpmn:standardLoopCharacteristics/>' if n.get("loop") else ""
                multi = '<bpmn:multiInstanceLoopCharacteristics/>' if n.get("multi") else ""
                out.append(f'    <bpmn:{tag} id="{nid_}" name="{lbl}">{refs}{loop}{multi}{da}</bpmn:{tag}>')
            elif t == "subprocess":
                out.append(f'    <bpmn:subProcess id="{nid_}" name="{lbl}">{refs}</bpmn:subProcess>')
            elif t in GW_TAG:
                out.append(f'    <bpmn:{GW_TAG[t]} id="{nid_}" name="{lbl}">{refs}</bpmn:{GW_TAG[t]}>')
        for (s, t, lbl) in flows:
            out.append(f'    <bpmn:sequenceFlow id="{fid[(s, t)]}" sourceRef="{s}" targetRef="{t}" name="{esc(lbl)}"/>')
        for d in p.get("data", []):
            if d["type"] == "store":
                out.append(f'    <bpmn:dataStoreReference id="{d["id"]}" name="{esc(d["label"])}"/>')
            else:
                out.append(f'    <bpmn:dataObject id="DO_{d["id"]}"/>')
                out.append(f'    <bpmn:dataObjectReference id="{d["id"]}" name="{esc(d["label"])}" dataObjectRef="DO_{d["id"]}"/>')
        out.append('  </bpmn:process>')

    # ---------------------------------------------------------------- DI
    di.append(f'  <bpmndi:BPMNDiagram id="Dgm_{spec["id"]}"><bpmndi:BPMNPlane id="Plane_{spec["id"]}" bpmnElement="{collab}">')

    # which events have a message flow attached at their bottom; which gateways branch up / down
    msg_below, gw_up, gw_down = {}, {}, {}
    for m in spec.get("messages", []):
        if isinstance(m, dict):
            continue
        s_, t_ = m[0], m[1]
        for nid_, other in ((s_, t_), (t_, s_)):
            if nid_ in L.shapes and node_type.get(nid_) in EVENT_TAG:
                ob = L.shapes.get(other) or L.pool_box[other]
                if L.c(ob)[1] > L.c(L.shapes[nid_])[1]:     # partner below -> line runs below the event
                    msg_below[nid_] = True
    for p in pools:
        for f in p.get("flows", []):
            a_, b2 = f[0], f[1]
            if node_type.get(a_) in GW_TAG:
                dy = L.c(L.shapes[b2])[1] - L.c(L.shapes[a_])[1]
                dx = L.c(L.shapes[b2])[0] - L.c(L.shapes[a_])[0]
                if dy < -1 and dx >= -1:
                    gw_up[a_] = True
                if dy > 1:
                    gw_down[a_] = True
            if node_type.get(b2) in GW_TAG:              # merges entering from below/above use the vertices too
                dy = L.c(L.shapes[a_])[1] - L.c(L.shapes[b2])[1]
                if dy < -1:
                    gw_up[b2] = True
                if dy > 1:
                    gw_down[b2] = True

    def shape(eid, b, extra="", label=None):
        x, y, w, h = b
        s = f'    <bpmndi:BPMNShape id="{eid}_di" bpmnElement="{eid}"{extra}><dc:Bounds x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}"/>'
        if label:
            lx, ly, lw, lh = label
            s += f'<bpmndi:BPMNLabel><dc:Bounds x="{lx:.0f}" y="{ly:.0f}" width="{lw:.0f}" height="{lh:.0f}"/></bpmndi:BPMNLabel>'
        di.append(s + '</bpmndi:BPMNShape>')

    def edge(eid, pts, label=None):
        s = f'    <bpmndi:BPMNEdge id="{eid}_di" bpmnElement="{eid}">' + \
            "".join(f'<di:waypoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in pts)
        if label:
            lx, ly, lw, lh = label
            s += f'<bpmndi:BPMNLabel><dc:Bounds x="{lx:.0f}" y="{ly:.0f}" width="{lw:.0f}" height="{lh:.0f}"/></bpmndi:BPMNLabel>'
        di.append(s + '</bpmndi:BPMNEdge>')

    for p in pools:
        shape(p["id"], L.pool_box[p["id"]], ' isHorizontal="true"')
        for lane in p.get("lanes", []) if not p.get("collapsed") else []:
            shape(lane["id"], L.lane_box[lane["id"]], ' isHorizontal="true"')
        for n in p.get("nodes", []):
            b = L.shapes[n["id"]]
            extra = ' isExpanded="false"' if n["type"] == "subprocess" else ""
            if n["type"] in ("task", "subprocess"):
                shape(n["id"], b, extra)
            else:   # external label under events / gateways
                longest = max((len(w) for w in str(n.get("label", "")).split()), default=0)
                lw = max(104, 9.2 * longest)
                lbl = (b[0] + b[2] / 2 - lw / 2, b[1] + b[3] + 3, lw, 40) if n.get("label") else None
                if n["type"] in EVENT_TAG and n.get("label") and msg_below.get(n["id"]):
                    # a message flow uses the bottom of the event -> put the label above it
                    lbl = (b[0] + b[2] / 2 - lw / 2, b[1] - 40, lw, 38)
                if n["type"] in GW_TAG and n.get("label"):
                    auto = "top"
                    if gw_up.get(n["id"]):     # an upward branch would cross a label above the diamond
                        auto = "below" if not gw_down.get(n["id"]) else "above_left"
                    pos = n.get("label_pos", auto)
                    if pos == "below":         # two lines within the narrow column
                        lbl = (b[0] + b[2] / 2 - 52, b[1] + b[3] + 3, 104, 40)
                    if pos == "top":              # one line (<= ~18 chars) centred above the diamond
                        lbl = (b[0] + b[2] / 2 - 80, b[1] - 23, 160, 20)
                    elif pos == "below_left":
                        lbl = (b[0] + b[2] / 2 - lw - 6, b[1] + b[3] - 6, lw, 40)
                    elif pos == "above_left":
                        lbl = (b[0] + b[2] / 2 - lw - 6, b[1] - 36, lw, 40)
                shape(n["id"], b, extra, lbl)
        for d in p.get("data", []):
            b = L.shapes[d["id"]]
            # label on the side opposite to its association (association from below -> label above)
            from_below = any(L.c(L.shapes[tid])[1] > L.c(b)[1] for tid, _ in d.get("links", []))
            lb = (b[0] + b[2] / 2 - 70, b[1] - 24, 140, 20) if from_below else (b[0] + b[2] / 2 - 70, b[1] + b[3] + 4, 140, 40)
            shape(d["id"], b, "", lb)
    for a in spec.get("annotations", []):
        shape(a["id"], L.shapes[a["id"]])
        if a.get("to"):
            sb, tb = L.shapes[a["to"]], L.shapes[a["id"]]
            sc, tc = L.c(sb), L.c(tb)
            if abs(sc[1] - tc[1]) < 1:                     # same row: right edge -> annotation left
                pts = [(sb[0] + sb[2], sc[1]), (tb[0], tc[1])] if tc[0] > sc[0] else [(sb[0], sc[1]), (tb[0] + tb[2], tc[1])]
            elif tc[1] < sc[1]:                            # annotation above: top edge
                pts = [(sc[0], sb[1]), (tb[0], tc[1])] if tc[0] > sc[0] + 1 else [(sc[0], sb[1]), (tc[0], tb[1] + tb[3])]
            else:                                          # annotation below: bottom edge
                pts = [(sc[0], sb[1] + sb[3]), (tb[0], tc[1])] if tc[0] > sc[0] + 1 else [(sc[0], sb[1] + sb[3]), (tc[0], tb[1])]
            edge(f'As_{a["id"]}', pts)

    for p in pools:
        flows = [tuple(f) + ("",) * (3 - len(f)) for f in p.get("flows", [])]
        for k, (s, t, lbl) in enumerate(flows):
            pts = L.seq_waypoints(s, t, node_type[s], node_type[t])
            lab = None
            if lbl:                    # label right at the start of the branch
                (x1, y1), (x2, y2) = pts[0], pts[1]
                lw = 8.5 * len(lbl) + 6
                if abs(x1 - x2) < 1:   # leaves a gateway vertex vertically
                    lab = (x1 + 5, y1 + 2 if y2 > y1 else y1 - 22, lw, 20)
                else:                  # leaves horizontally
                    lab = (x1 + 6, y1 - 22, lw, 20)
            edge(f'SF_{p["id"]}_{k}', pts, lab)
        for d in p.get("data", []):
            for k, (tid, direction) in enumerate(d.get("links", [])):
                tb, db = L.shapes[tid], L.shapes[d["id"]]
                tc, dc = L.c(tb), L.c(db)
                a_pt = (tc[0], tb[1] + tb[3]) if dc[1] > tc[1] else (tc[0], tb[1])
                b_pt = (dc[0], db[1]) if dc[1] > tc[1] else (dc[0], db[1] + db[3])
                if abs(dc[1] - tc[1]) < 1:
                    a_pt, b_pt = ((tb[0] + tb[2], tc[1]), (db[0], dc[1])) if dc[0] > tc[0] else \
                                 ((tb[0], tc[1]), (db[0] + db[2], dc[1]))
                pts = [a_pt, b_pt] if direction == "out" else [b_pt, a_pt]
                kin = [dd for dd, dirn in [(dd["id"], dirn) for dd in p.get("data", []) for (tt, dirn) in dd.get("links", []) if tt == tid] if dirn == direction]
                idx = kin.index(d["id"])
                eid = f'DOA_{tid}_{idx}' if direction == "out" else f'DIA_{tid}_{idx}'
                edge(eid, pts)
    placed_labels = []
    # messages whose labels share the same gap: leftmost label goes left of its line, rightmost goes right
    gap_side = {}
    groups = {}
    for i, m in enumerate(spec.get("messages", [])):
        if isinstance(m, dict) or len(m) < 3 or not m[2]:
            continue
        s_, t_ = m[0], m[1]
        sp_ = s_ if s_ in L.pool_box else L.node_pool[s_]
        tp_ = t_ if t_ in L.pool_box else L.node_pool[t_]
        up_ = min((L.pool_box[sp_], L.pool_box[tp_]), key=lambda b: b[1])
        pts_ = L.msg_waypoints(s_, t_)
        x_ = pts_[0][0] if L.pool_box[sp_] is up_ else pts_[-1][0]
        groups.setdefault(round(up_[1] + up_[3]), []).append((x_, i, max(60, 8.6 * len(m[2]))))
    for g in groups.values():
        g.sort()
        for k, (x_, i, lw_) in enumerate(g):
            # default right of the line; go left when the next line to the right is closer than the label
            nxt = g[k + 1][0] if k + 1 < len(g) else None
            gap_side[i] = "left" if nxt is not None and nxt - x_ < lw_ + 12 else "right"
    for i, m in enumerate(spec.get("messages", [])):
        if isinstance(m, dict):                      # explicit geometry (free mode)
            edge(f'MF_{spec["id"]}_{i}', m["pts"], m.get("lab"))
            continue
        s, t, lbl = (m + ("",))[:3]
        pts = L.msg_waypoints(s, t)
        lab = None
        if lbl:                        # label centred in the gap below the upper of the two pools
            sp = s if s in L.pool_box else L.node_pool[s]
            tp = t if t in L.pool_box else L.node_pool[t]
            up, lo = sorted((L.pool_box[sp], L.pool_box[tp]), key=lambda b: b[1])
            gap_y = up[1] + up[3] + POOL_GAP / 2
            x = pts[0][0] if L.pool_box[sp] is up else pts[-1][0]
            lw = max(60, 8.6 * len(lbl))
            cands = [(x + 6, gap_y - 11, lw, 22), (x - 6 - lw, gap_y - 11, lw, 22)]
            if gap_side.get(i) == "left":
                cands.reverse()
            cands = [c for c in cands if c[0] >= 0 and c[0] + c[2] <= L.width] or cands
            def hits(c):
                return any(not (c[0] + c[2] < o[0] or o[0] + o[2] < c[0] or c[1] + c[3] < o[1] or o[1] + o[3] < c[1])
                           for o in placed_labels)
            lab = next((c for c in cands if not hits(c)), cands[0])
            placed_labels.append(lab)
        edge(f'MF_{spec["id"]}_{i}', pts, lab)
    di.append('  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>')
    return "\n".join(out) + "\n" + "\n".join(di) + "\n</bpmn:definitions>\n", L


def stats(spec):
    """Counts used for the pools/lanes/interactions analysis."""
    res = {"pools": [], "lane_handoffs": {}, "messages": len(spec.get("messages", []))}
    for p in spec["pools"]:
        if p.get("collapsed"):
            res["pools"].append({"id": p["id"], "name": p["name"], "collapsed": True})
            continue
        lane_of = {n["id"]: n["lane"] for n in p["nodes"]}
        lname = {l["id"]: l["name"] for l in p["lanes"]}
        kinds = {}
        for n in p["nodes"]:
            k = n["type"] if n["type"] != "task" else "task"
            kinds[k] = kinds.get(k, 0) + 1
        hand = 0
        for f in p["flows"]:
            a, b = lane_of[f[0]], lane_of[f[1]]
            if a != b:
                hand += 1
                key = (lname[a], lname[b])
                res["lane_handoffs"][key] = res["lane_handoffs"].get(key, 0) + 1
        res["pools"].append({"id": p["id"], "name": p["name"], "lanes": [l["name"] for l in p["lanes"]],
                             "tasks": sum(1 for n in p["nodes"] if n["type"] in ("task", "subprocess")),
                             "events": sum(1 for n in p["nodes"] if n["type"] in EVENT_TAG),
                             "gateways": sum(1 for n in p["nodes"] if n["type"] in GW_TAG),
                             "flows": len(p["flows"]), "handoffs": hand,
                             "data": len(p.get("data", []))})
    return res


def render(bpmn_path, min_pt=10.0):
    """bpmn → svg/png via bpmn-js, then the same legibility gate as mmd_render (writes .layout.json)."""
    bpmn_path = Path(bpmn_path).resolve()
    svg, png = bpmn_path.with_suffix(".svg"), bpmn_path.with_suffix(".png")
    r = subprocess.run(["node", str(ROOT / "tools/bpmn/render.mjs"), str(bpmn_path), str(svg), str(png), "4",
                        str(FONT_PX)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"bpmn render failed for {bpmn_path.name}:\n{r.stdout}{r.stderr}")
    if "warnings" in r.stderr.lower():
        print(r.stderr.strip(), file=sys.stderr)
    info = json.loads(r.stdout.strip().splitlines()[-1])
    w, h = info["width"], info["height"]
    from PIL import Image
    pw, ph = Image.open(png).size
    font_px = FONT_PX - 1                       # external labels are 1 px smaller
    res = {"file": bpmn_path.name, "native_px": [w, h], "png_px": [pw, ph], "min_font_px": font_px}
    cm_to_pt = 72 / 2.54
    best = None
    for name, (bw, bh) in {"portrait": (16.5, 22.5), "landscape": (25.7, 14.5)}.items():
        wcm = min(bw, bh * w / h, 13.0 * w / font_px / cm_to_pt)
        pt = font_px * wcm * cm_to_pt / w
        res[name] = {"width_cm": round(wcm, 2), "font_pt": round(pt, 1), "dpi": round(pw / (wcm / 2.54))}
        if pt >= min_pt and best is None:
            best = name
    best = best or max(("portrait", "landscape"), key=lambda n: res[n]["font_pt"])
    res.update(orientation=best, width_cm=res[best]["width_cm"], legible=res[best]["font_pt"] >= min_pt)
    bpmn_path.with_suffix(".layout.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
    return res


def write(spec, out_path):
    xml, L = build_xml(spec)
    Path(out_path).write_text(xml, encoding="utf-8")
    return L


if __name__ == "__main__":
    r = render(sys.argv[1])
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r["legible"] else 3)
