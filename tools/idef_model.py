#!/usr/bin/env python3
"""IDEF0 / IDEF3 / node-tree renderer for ПІС lab reports (AllFusion-Process-Modeler-like output, strict notation).

Diagrams are Python dicts (see lab3/make_lab3.py). Output: SVG (+ PNG via rsvg-convert) and `.layout.json`
with the same legibility gate as the other renderers (text >= 10 pt in Word, >= 300 dpi).

IDEF0 spec
    {"kind": "idef0", "node": "A0", "title": "...", "number": "3", "status": "РОБОЧИЙ", "feo": False,
     "boxes": [{"id": "A1", "name": "..."}, ...],              # list order = staircase order (top-left → bottom-right)
     "arrows": [{"label": "...", "src": "I" | "C" | "M" | "A1", "dst": ["A2:I", "A3:C"] | ["O"], "code": "I1"}],
     "call": {"box": "A3", "label": "..."},                      # optional call arrow (model split)
     "text": "Мета: ...\nТочка зору: ..."}                       # optional text block (context diagram)
    src "I"/"C"/"M" = boundary arrow entering from left/top/bottom; dst "O" = boundary output (right border).
    "A2:I" / "A2:C" / "A2:M" = input / control / mechanism of box A2. Box outputs always leave the right side.
IDEF3 spec
    {"kind": "idef3", "node": "A3.1", "title": "...",
     "uows": [{"id": "U1", "num": "1", "name": "...", "col": 0, "row": 0}],
     "junctions": [{"id": "J1", "type": "X" | "&" | "O", "sync": False, "col": 1, "row": 0}],
     "referents": [{"id": "R1", "name": "...", "col": 0, "row": 1}],
     "links": [("U1", "J1"), ("J1", "U2"), ("U3", "U4", "object"), ("R1", "U1", "referent")]}
Node tree spec
    {"kind": "tree", "title": "...", "root": {"id": "A0", "name": "...", "children": [...]}}
"""
import json, math, re, subprocess, sys
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT_FILE = "/usr/share/fonts/wps-fonts/times.ttf"
FONT_BOLD = "/usr/share/fonts/wps-fonts/timesbd.ttf"
FPX = 15                         # base font size (px) of all diagram text
LH = 1.16                        # line height factor
_font = ImageFont.truetype(FONT_FILE, FPX * 4)
_fontb = ImageFont.truetype(FONT_BOLD, FPX * 4)


def tw(text, bold=False):
    f = _fontb if bold else _font
    return f.getlength(text) / 4.0


def wrap(text, width, bold=False):
    lines = []
    for para in str(text).split("\n"):
        cur = ""
        for w in para.split():
            cand = (cur + " " + w).strip()
            if tw(cand, bold) <= width or not cur:
                cur = cand
            else:
                lines.append(cur); cur = w
        lines.append(cur)
    return lines


def esc(s):
    return escape(str(s))


class SVG:
    def __init__(self):
        self.items = []

    def rect(self, x, y, w, h, sw=1.6, dash=None, fill="#fff"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" '
                          f'stroke="#000" stroke-width="{sw}"{d}/>')

    def line(self, pts, sw=1.4, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.items.append(f'<polyline points="{p}" fill="none" stroke="#000" stroke-width="{sw}"{d} '
                          f'stroke-linejoin="round"/>')

    def head(self, a, b, size=9, filled=True):
        (x1, y1), (x2, y2) = a, b
        ang = math.atan2(y2 - y1, x2 - x1)
        p1 = (x2 - size * math.cos(ang) + size * 0.45 * math.sin(ang), y2 - size * math.sin(ang) - size * 0.45 * math.cos(ang))
        p2 = (x2 - size * math.cos(ang) - size * 0.45 * math.sin(ang), y2 - size * math.sin(ang) + size * 0.45 * math.cos(ang))
        f = "#000" if filled else "#fff"
        self.items.append(f'<polygon points="{x2:.1f},{y2:.1f} {p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}" '
                          f'fill="{f}" stroke="#000" stroke-width="1"/>')

    def text(self, x, y, lines, anchor="start", bold=False, size=FPX, italic=False):
        """y = top of the text block."""
        fw = ' font-weight="bold"' if bold else ""
        fi = ' font-style="italic"' if italic else ""
        out = [f'<text font-family="Times New Roman" font-size="{size}" text-anchor="{anchor}"{fw}{fi} fill="#000">']
        for i, ln in enumerate(lines):
            out.append(f'<tspan x="{x:.1f}" y="{y + size * 0.82 + i * size * LH:.1f}">{esc(ln)}</tspan>')
        out.append("</text>")
        self.items.append("".join(out))

    def circle(self, cx, cy, r, fill="#fff"):
        self.items.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="#000" stroke-width="1.2"/>')

    def save(self, path, w, h):
        body = "\n".join(self.items)
        Path(path).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" '
                              f'viewBox="0 0 {w:.0f} {h:.0f}"><rect width="100%" height="100%" fill="#fff"/>'
                              f'{body}</svg>', encoding="utf-8")


# ------------------------------------------------------------------------------------------- label placement
def _ov(a, b):
    return max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])) * max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))


def _seg_hits(box, segs):
    x, y, w, h = box
    n = 0
    for (x1, y1), (x2, y2) in segs:
        if abs(x1 - x2) < 0.5:   # vertical
            if x < x1 < x + w and min(y1, y2) < y + h and max(y1, y2) > y:
                n += 1
        else:
            if y < y1 < y + h and min(x1, x2) < x + w and max(x1, x2) > x:
                n += 1
    return n


class Placer:
    """Collision-scored label placement. A label either sits next to its arrow or, when the free space is
    further away, is connected to the arrow by an IDEF0 squiggle (returned as `anchor`)."""

    def __init__(self, bounds, obstacles, segs):
        self.bounds, self.obst, self.segs, self.placed, self.squiggles = bounds, list(obstacles), segs, [], []

    def _score(self, box, anchor_pt, dist):
        bx, by, bw, bh = self.bounds
        x, y, w, h = box
        if x < bx + 3 or y < by + 3 or x + w > bx + bw - 3 or y + h > by + bh - 3:
            return None
        s = sum(_ov(box, o) for o in self.obst) * 25 + sum(_ov(box, o) for o in self.placed) * 25
        s += _seg_hits(box, self.segs) * 1200
        if dist > 9:     # squiggle: penalise length and crossings
            cx, cy = min(max(anchor_pt[0], x), x + w), min(max(anchor_pt[1], y), y + h)
            sq = [((cx, cy), anchor_pt)]
            hits = 0
            for (p1, p2) in self.segs:
                if _cross(sq[0], (p1, p2)):
                    hits += 1
            s += hits * 500 + dist * 2.2 + 40
            s += sum(1 for q in self.squiggles if _cross(sq[0], q)) * 500
        return s

    def place(self, label, pts, widths=(118, 150, 96, 80, 64), prefer="start"):
        best = None
        own = set(zip(pts, pts[1:]))
        foreign = [sg for sg in self.segs if sg not in own and (sg[1], sg[0]) not in own]
        segs = [sg for sg in zip(pts, pts[1:]) if abs(sg[0][0] - sg[1][0]) + abs(sg[0][1] - sg[1][1]) >= 14]
        tot = len(segs)
        for wmax in widths + (1000,):
            lines = wrap(label, wmax)
            w = max(tw(l) for l in lines) + 2
            h = len(lines) * FPX * LH
            for si, ((x1, y1), (x2, y2)) in enumerate(segs):
                horiz = abs(y1 - y2) < 0.5
                L = abs(x2 - x1) + abs(y2 - y1)
                nsamp = max(2, int(L // 28))
                for t in range(nsamp + 1):
                    ax = x1 + (x2 - x1) * t / nsamp
                    ay = y1 + (y2 - y1) * t / nsamp
                    for d in (2, 16, 34, 56, 84):
                        if horiz:
                            cands = [(ax + 4, ay - h - d), (ax - w - 4, ay - h - d), (ax - w / 2, ay - h - d),
                                     (ax + 4, ay + d + 1), (ax - w - 4, ay + d + 1), (ax - w / 2, ay + d + 1)]
                        else:
                            cands = [(ax + d + 3, ay - h - 2), (ax + d + 3, ay + 2), (ax + d + 3, ay - h / 2),
                                     (ax - d - 3 - w, ay - h - 2), (ax - d - 3 - w, ay + 2), (ax - d - 3 - w, ay - h / 2)]
                        for (cx, cy) in cands:
                            box = (cx, cy, w, h)
                            sc = self._score(box, (ax, ay), d)
                            if sc is None:
                                continue
                            sc += (len(lines) - 1) * 10 + si * 4
                            if prefer == "end":
                                sc += (tot - 1 - si) * 10
                            # hard constraints first: no line crossing, no overlap with boxes / labels
                            sq_hits = 0
                            if d > 9:
                                qx, qy = min(max(ax, cx), cx + w), min(max(ay, cy), cy + h)
                                sq_hits = sum(1 for sg in self.segs if _cross(((qx, qy), (ax, ay)), sg))
                            # a label hugging another arrow's line reads as belonging to it
                            near = _seg_hits((cx - 9, cy - 7, w + 18, h + 14), foreign)
                            sc += near * 260
                            hard = (_seg_hits(box, self.segs) + sq_hits,
                                    1 if any(_ov(box, o) > 0 for o in self.obst + self.placed) else 0)
                            key = (hard, sc)
                            if best is None or key < best[0]:
                                best = (key, box, lines, (ax, ay), d)
            if best and best[0][0] == (0, 0) and best[0][1] < 30 and wmax != 1000:
                break
        if best is None:
            return None
        _, box, lines, anchor, d = best
        self.placed.append(box)
        sq = None
        if d > 9:
            x, y, w, h = box
            cx, cy = min(max(anchor[0], x), x + w), min(max(anchor[1], y), y + h)
            sq = ((cx, cy), anchor)
            self.squiggles.append(sq)
        return box, lines, sq


def _cross(s1, s2):
    """Proper intersection of two segments."""
    (a, b), (c, d) = s1, s2

    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < 1e-9 else (1 if v > 0 else -1)
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return o1 * o2 < 0 and o3 * o4 < 0


def squiggle(svg, a, b):
    """IDEF0 squiggle: small S-shaped leader from label (a) to arrow (b)."""
    (x1, y1), (x2, y2) = a, b
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L * 6, dx / L * 6
    svg.items.append(f'<path d="M {x1:.1f},{y1:.1f} Q {(x1 + mx) / 2 + nx:.1f},{(y1 + my) / 2 + ny:.1f} {mx:.1f},{my:.1f} '
                     f'T {x2:.1f},{y2:.1f}" fill="none" stroke="#000" stroke-width="1.1"/>')


# ------------------------------------------------------------------------------------------- frame
HDR_H, FTR_H = 34, 34


def frame(svg, W, H, node, title, number, status="РОБОЧИЙ", feo=False):
    svg.rect(1, 1, W - 2, H - 2, sw=1.8)
    svg.line([(1, HDR_H), (W - 1, HDR_H)], sw=1.2)
    svg.line([(1, H - FTR_H), (W - 1, H - FTR_H)], sw=1.2)
    fields = [("АВТОР:", "Кравченко П."), ("ПРОЄКТ:", "ІС «Щит-Лінк»"), ("ДАТА:", "03.10.2026"),
              ("СТАН:", status), ("ЧИТАЧ:", "Гладка М. В.")]
    x = 8
    for i, (k, v) in enumerate(fields):
        svg.text(x, 9, [f"{k} {v}"])
        x += tw(f"{k} {v}") + 26
        if i < len(fields) - 1:
            svg.line([(x - 13, 1), (x - 13, HDR_H)], sw=0.8)
    num = f"{number}{'F' if feo else ''}"
    svg.text(8, H - FTR_H + 9, [f"ВУЗОЛ: {node}{'F' if feo else ''}"])
    nw = tw(f"ВУЗОЛ: {node}F") + 24
    svg.line([(nw, H - FTR_H), (nw, H - 1)], sw=0.8)
    svg.text(nw + 10, H - FTR_H + 9, [f"НАЗВА: {title}" + ("  (FEO — тільки для експозиції)" if feo else "")])
    svg.line([(W - 130, H - FTR_H), (W - 130, H - 1)], sw=0.8)
    svg.text(W - 120, H - FTR_H + 9, [f"НОМЕР: {num}"])


# ------------------------------------------------------------------------------------------- IDEF0
def render_idef0(spec, svg_path):
    ctx = len(spec["boxes"]) == 1
    BW, BH = (340, 190) if ctx else (spec.get("bw", 124), spec.get("bh", 88))
    GAP, DY = spec.get("gap", 52), spec.get("dy", 74)
    LZ, RZ = spec.get("lz", 122), spec.get("rz", 122)
    TZ, BZ = spec.get("tz", 64), spec.get("bz", 66)
    n = len(spec["boxes"])
    boxes = {}
    for k, b in enumerate(spec["boxes"]):
        boxes[b["id"]] = (LZ + k * (BW + GAP), HDR_H + TZ + k * DY, BW, BH, k, b)
    W = LZ + n * BW + (n - 1) * GAP + RZ
    last_bottom = HDR_H + TZ + (n - 1) * DY + BH
    extra_below = spec.get("below", 34)
    H = last_bottom + extra_below + BZ + FTR_H
    if ctx:
        W = max(W, spec.get("ctx_w", 1000))
        TZc, BZc = spec.get("tz", 104), spec.get("bz", 112)
        bx = (W - BW) / 2 + spec.get("ctx_dx", 40)
        boxes = {spec["boxes"][0]["id"]: (bx, HDR_H + TZc, BW, BH, 0, spec["boxes"][0])}
        H = HDR_H + TZc + BH + BZc + FTR_H
    top, bottom, left, right = HDR_H, H - FTR_H, 0, W

    # ---- collect endpoints per box side
    arrows = spec["arrows"]
    sides = {bid: {"I": [], "C": [], "O": [], "M": []} for bid in boxes}
    for ai, a in enumerate(arrows):
        if a["src"] in boxes:
            sides[a["src"]]["O"].append(ai)
        for d in a["dst"]:
            if d != "O":
                bid, sd = d.split(":")
                sides[bid][sd].append(ai)
    if spec.get("call"):
        sides[spec["call"]["box"]]["M"].append("call")

    def key_src_y(ai):
        a = arrows[ai]
        if a["src"] in boxes:
            return boxes[a["src"]][1]
        return {"I": -1e6, "C": -1e6, "M": 1e6}[a["src"]]

    pos = {}   # (ai, bid, side) -> coordinate
    for bid, (bx, by, bw, bh, k, _) in boxes.items():
        s = sides[bid]
        # inputs: boundary first, then by source position (feedbacks from the right go lowest)
        lst = sorted(s["I"], key=lambda ai: (0 if arrows[ai]["src"] == "I" else
                                             (1 if boxes.get(arrows[ai]["src"], (0, 0, 0, 0, -1))[4] < k else 2)))
        lo, hi = (by + 26, by + bh - 14) if not ctx else (by + 30, by + bh - 30)
        for i, ai in enumerate(lst):
            pos[(ai, bid, "I")] = lo + (hi - lo) * (i + 1) / (len(lst) + 1) if len(lst) > 1 else (lo + hi) / 2
        lst = sorted(s["C"], key=lambda ai: (0 if arrows[ai]["src"] == "C" else 1, key_src_y(ai)))
        for i, ai in enumerate(lst):
            pos[(ai, bid, "C")] = bx + bw * (i + 1) / (len(lst) + 1)
        lst = sorted(s["M"], key=lambda ai: 0 if ai == "call" else 1)
        for i, ai in enumerate(lst):
            pos[(ai, bid, "M")] = bx + bw * (i + 1) / (len(lst) + 1)
        lst = s["O"]
        lo, hi = (by + 12, by + min(bh, DY) - 12) if not ctx else (by + 30, by + bh - 30)
        def dst_y(ai):
            d = arrows[ai]["dst"][0]
            if d == "O":
                return 0
            return boxes[d.split(":")[0]][1]
        lst = sorted(lst, key=dst_y)
        for i, ai in enumerate(lst):
            pos[(ai, bid, "O")] = lo + (hi - lo) * (i + 1) / (len(lst) + 1) if len(lst) > 1 else (lo + hi) / 2

    # ---- context diagram: boundary arrows leave the border well spread and jog into the box (room for labels)
    if ctx:
        bid = spec["boxes"][0]["id"]
        bx, by, bw, bh = boxes[bid][:4]
        routes_ctx = []
        def fan(items, side):
            n_ = len(items)
            if side in ("C", "M"):            # spread only around the box (corners stay free)
                x0_, x1_ = bx - 0.38 * bw, bx + bw + 0.38 * bw
                xs_b = [x0_ + (x1_ - x0_) * (i + 1) / (n_ + 1) for i in range(n_)]
                ents = [bx + bw * (i + 1) / (n_ + 1) for i in range(n_)]
            else:
                y0, y1 = by - 34, by + bh + 34
                xs_b = [y0 + (y1 - y0) * (i + 1) / (n_ + 1) for i in range(n_)]
                ents = [by + bh * (i + 1) / (n_ + 1) for i in range(n_)]
            # jog levels: arrows nearer the middle turn closer to the box edge (no crossings)
            order = sorted(range(n_), key=lambda i: abs(xs_b[i] - ents[i]))
            lvl = {i: r for r, i in enumerate(order)}
            for i, ai in enumerate(items):
                b_, e_ = xs_b[i], ents[i]
                if side == "C":
                    yj = by - 22 - 13 * (n_ - 1 - lvl[i])
                    pts = [(b_, top), (b_, yj), (e_, yj), (e_, by)] if abs(b_ - e_) > 1 else [(b_, top), (e_, by)]
                elif side == "M":
                    yj = by + bh + 22 + 13 * (n_ - 1 - lvl[i])
                    pts = [(b_, bottom), (b_, yj), (e_, yj), (e_, by + bh)] if abs(b_ - e_) > 1 else [(b_, bottom), (e_, by + bh)]
                elif side == "I":
                    xj = bx - 26 - 13 * (n_ - 1 - lvl[i])
                    pts = [(left, b_), (xj, b_), (xj, e_), (bx, e_)] if abs(b_ - e_) > 1 else [(left, b_), (bx, e_)]
                else:
                    xj = bx + bw + 26 + 13 * (n_ - 1 - lvl[i])
                    pts = [(bx + bw, e_), (xj, e_), (xj, b_), (right, b_)] if abs(b_ - e_) > 1 else [(bx + bw, e_), (right, b_)]
                routes_ctx.append((ai, [pts]))
        for side in ("I", "C", "M"):
            fan([ai for ai, a in enumerate(arrows) if a["src"] == side], side)
        fan([ai for ai, a in enumerate(arrows) if a["dst"] == ["O"]], "O")
    # ---- route
    chan = {}       # gap index -> used offsets
    below_slots, above_slots = {}, {}
    routes = []     # (ai, list of polylines, label_anchor_poly)

    def channel(k):
        used = chan.setdefault(k, 0)
        chan[k] = used + 1
        return 12 + used * 11

    bus_c, bus_m = {}, {}
    used_h = []      # (y, x0, x1) of horizontal tracks already taken

    def free_y(y, x0, x1, step):
        lo, hi = min(x0, x1), max(x0, x1)
        while any(abs(y - uy) < 7 and not (hi < ux0 or lo > ux1) for uy, ux0, ux1 in used_h):
            y += step
        used_h.append((y, lo, hi))
        return y

    for ai, a in enumerate(arrows):
        polys = []
        src = a["src"]
        if src in ("I", "C", "M"):
            tgts = [d.split(":") for d in a["dst"]]
            if src == "I":
                for bid, sd in tgts:
                    y = pos[(ai, bid, "I")]
                    polys.append([(left, y), (boxes[bid][0], y)])
            elif src == "C":
                xs = sorted((pos[(ai, bid, "C")], boxes[bid][1]) for bid, sd in tgts)
                if len(xs) == 1:
                    polys.append([(xs[0][0], top), (xs[0][0], xs[0][1])])
                else:
                    slot = len(bus_c); bus_c[ai] = slot
                    yb = free_y(min(y for _, y in xs) - 18 - slot * 11, xs[0][0], xs[-1][0], -11)
                    polys.append([(xs[0][0], top), (xs[0][0], xs[0][1])])
                    polys.append([(xs[0][0], yb), (xs[-1][0], yb)])
                    for x, y in xs[1:]:
                        polys.append([(x, yb), (x, y)])
            else:  # mechanism
                xs = sorted((pos[(ai, bid, "M")], boxes[bid][1] + boxes[bid][3]) for bid, sd in tgts)
                if len(xs) == 1:
                    polys.append([(xs[0][0], bottom), (xs[0][0], xs[0][1])])
                else:
                    slot = len(bus_m); bus_m[ai] = slot
                    yb = free_y(max(y for _, y in xs) + 18 + slot * 11, xs[0][0], xs[-1][0], 11)
                    polys.append([(xs[-1][0], bottom), (xs[-1][0], xs[-1][1])])
                    polys.append([(xs[0][0], yb), (xs[-1][0], yb)])
                    for x, y in xs[:-1]:
                        polys.append([(x, yb), (x, y)])
        else:
            sx, sy, sw_, sh, sk, _ = boxes[src]
            ye = pos[(ai, src, "O")]
            x0 = sx + sw_
            for d in a["dst"]:
                if d == "O":
                    polys.append([(x0, ye), (right, ye)])
                    continue
                bid, sd = d.split(":")
                tx, ty, tw_, th, tk, _ = boxes[bid]
                if tk > sk:
                    if sd == "I":
                        xc = x0 + channel(sk)
                        yi = pos[(ai, bid, "I")]
                        polys.append([(x0, ye), (xc, ye), (xc, yi), (tx, yi)])
                    elif sd == "C":
                        xcx = pos[(ai, bid, "C")]
                        polys.append([(x0, ye), (xcx, ye), (xcx, ty)])
                    else:
                        xc = x0 + channel(sk)
                        xm = pos[(ai, bid, "M")]
                        yb = free_y(ty + th + 16, xc, xm, 11)
                        polys.append([(x0, ye), (xc, ye), (xc, yb), (xm, yb), (xm, ty + th)])
                else:   # feedback
                    xc = x0 + channel(sk)
                    if sd == "C":
                        xcx = pos[(ai, bid, "C")]
                        yu = free_y(ty - 16, xc, xcx, -11)
                        polys.append([(x0, ye), (xc, ye), (xc, yu), (xcx, yu), (xcx, ty)])
                    else:
                        xl = tx - 14 - below_slots.get(("l", bid), 0)
                        yb = free_y(sy + sh + 18, xc, xl, 11)
                        below_slots[("l", bid)] = below_slots.get(("l", bid), 0) + 11
                        yi = pos[(ai, bid, sd)]
                        if sd == "I":
                            polys.append([(x0, ye), (xc, ye), (xc, yb), (xl, yb), (xl, yi), (tx, yi)])
                        else:  # feedback to mechanism
                            xm = pos[(ai, bid, "M")]
                            polys.append([(x0, ye), (xc, ye), (xc, yb), (xm, yb), (xm, ty + th)])
        routes.append((ai, polys))
    if ctx:
        routes = routes_ctx
    if spec.get("call"):
        bid = spec["call"]["box"]
        x = pos[("call", bid, "M")]
        routes.append(("call", [[(x, boxes[bid][1] + boxes[bid][3]), (x, bottom)]]))

    # ---- draw
    svg = SVG()
    frame(svg, W, H, spec["node"], spec["title"], spec["number"], spec.get("status", "РОБОЧИЙ"), spec.get("feo"))
    allsegs = []
    for _, polys in routes:
        for p in polys:
            allsegs += list(zip(p, p[1:]))
    obst = [(b[0] - 3, b[1] - 3, b[2] + 6, b[3] + 6) for b in boxes.values()]
    for ai, polys in routes:                        # tunnel brackets are obstacles for labels
        if ai != "call" and arrows[ai].get("tunnel"):
            (x, y), (x2, y2) = polys[0][0], polys[0][1]
            if abs(x - x2) < 0.5:
                yy = y + (12 if y2 > y else -12)
                obst.append((x - 14, yy - 10, 28, 20))
            else:
                xx = x + (12 if x2 > x else -12)
                obst.append((xx - 10, y - 14, 20, 28))
    text_lines = wrap(spec["text"], spec.get("text_w", 330)) if spec.get("text") else []
    if text_lines:
        th = len(text_lines) * FPX * LH
        ty0 = top + 10 if spec.get("text_pos", "top") == "top" else bottom - th - 10
        text_box = (10, ty0 - 2, spec.get("text_w", 330) + 8, th + 6)
        obst.append(text_box)
    placer = Placer((0, HDR_H, W, H - HDR_H - FTR_H), obst, allsegs)
    feo_keep = None          # FEO diagrams receive an already filtered arrow list; all their labels are shown
    for bid, (bx, by, bw, bh, k, b) in boxes.items():
        svg.rect(bx, by, bw, bh, sw=2.0)
        lines = wrap(b["name"], bw - 14)
        th_ = len(lines) * FPX * LH
        svg.text(bx + bw / 2, by + (bh - 16 - th_) / 2 + 2, lines, anchor="middle")
        svg.text(bx + bw - 5, by + bh - FPX - 3, [bid if not ctx else spec["node"]], anchor="end", size=FPX)
    # draw arrows (heads at each target end)
    order = sorted(routes, key=lambda r: 0 if r[0] == "call" or arrows[r[0]]["src"] in ("I", "C", "M") or
                   "O" in arrows[r[0]]["dst"] else 1)
    for ai, polys in order:
        dim = False
        sw = 1.0 if dim else 1.5
        dash = "4 3" if dim else None
        for p in polys:
            svg.line(p, sw=sw, dash=dash)
        # arrowheads: on polylines that end on a box side or the right border / call bottom
        for p in polys:
            end = p[-1]
            if ai == "call" or end[0] >= right - 0.5 or any(abs(end[0] - bb[0]) < .6 or abs(end[1] - bb[1]) < .6 or
                                                             abs(end[1] - (bb[1] + bb[3])) < .6
                                                             for bb in boxes.values()):
                svg.head(p[-2], p[-1], filled=not dim)
        # tunnelled arrow: round brackets at the border end (arrow not shown on the parent diagram)
        if ai != "call" and arrows[ai].get("tunnel"):
            (x, y), (x2, y2) = polys[0][0], polys[0][1]
            if abs(x - x2) < 0.5:          # vertical (control / mechanism)
                yy = y + (12 if y2 > y else -12)
                svg.items.append(f'<path d="M {x-5:.1f},{yy-7:.1f} Q {x-11:.1f},{yy:.1f} {x-5:.1f},{yy+7:.1f} '
                                 f'M {x+5:.1f},{yy-7:.1f} Q {x+11:.1f},{yy:.1f} {x+5:.1f},{yy+7:.1f}" '
                                 f'fill="none" stroke="#000" stroke-width="1.4"/>')
            else:                          # horizontal (input / output)
                xx = x + (12 if x2 > x else -12)
                svg.items.append(f'<path d="M {xx-7:.1f},{y-5:.1f} Q {xx:.1f},{y-11:.1f} {xx+7:.1f},{y-5:.1f} '
                                 f'M {xx-7:.1f},{y+5:.1f} Q {xx:.1f},{y+11:.1f} {xx+7:.1f},{y+5:.1f}" '
                                 f'fill="none" stroke="#000" stroke-width="1.4"/>')
        # junction dots for branching buses
        if ai != "call" and (ai in bus_c or ai in bus_m):
            for p in polys[2:]:
                svg.circle(p[0][0], p[0][1], 2.6, fill="#000")
    # labels
    for ai, polys in order:
        if ai == "call":
            lbl = spec["call"]["label"]
        else:
            lbl = arrows[ai].get("label")
            if feo_keep is not None and lbl not in feo_keep:
                continue
        if not lbl:
            continue
        a = arrows[ai] if ai != "call" else {"src": "call"}
        main = polys[0] if not (a.get("src") == "C" and len(polys) > 1) else polys[0] + polys[1][1:]
        prefer = "end" if a.get("src") not in ("I", "C", "M", "call") and a["dst"] != ["O"] else "start"
        res = placer.place(lbl, main if len(polys) == 1 else max(polys, key=lambda p: sum(abs(q[0][0] - q[1][0]) + abs(q[0][1] - q[1][1]) for q in zip(p, p[1:]))), prefer=prefer)
        if res:
            (lx, ly, lw, lh), lines, sq = res
            svg.text(lx + 1, ly, lines)
            if sq:
                squiggle(svg, *sq)
        # ICOM code at the border end on decompositions
        code = a.get("code")
        if code and not ctx:
            p0 = polys[0]
            if a["src"] == "I":
                svg.text(left + 4, p0[0][1] + 3, [code])
            elif a["src"] == "C":
                svg.text(p0[0][0] - 4, top + 3, [code], anchor="end")
            elif a["src"] == "M":
                p = polys[0]
                svg.text(p[0][0] - 4, bottom - 18, [code], anchor="end")
            elif "O" in a["dst"]:
                po = next(p for p in polys if p[-1][0] >= right - 0.5)
                svg.text(right - 4, po[-1][1] + 3, [code], anchor="end")
    if text_lines:
        svg.text(14, ty0, text_lines, italic=True)
    svg.save(svg_path, W, H)
    return W, H


# ------------------------------------------------------------------------------------------- IDEF3
def render_idef3(spec, svg_path):
    UW, UH, CW, RH = 150, 80, 196, 112
    JW, JH = 30, 44
    RW, RHt = 130, 40
    X0, Y0 = 26, HDR_H + 30
    cols = 1 + max([u["col"] for u in spec["uows"]] + [j["col"] for j in spec.get("junctions", [])] +
                   [r["col"] for r in spec.get("referents", [])])
    rows = 1 + max([u["row"] for u in spec["uows"]] + [j["row"] for j in spec.get("junctions", [])] +
                   [r["row"] for r in spec.get("referents", [])])
    colw = {}
    for u in spec["uows"]:
        colw[u["col"]] = max(colw.get(u["col"], 0), CW)
    for r in spec.get("referents", []):
        colw[r["col"]] = max(colw.get(r["col"], 0), RW + 40)
    for j in spec.get("junctions", []):
        colw[j["col"]] = max(colw.get(j["col"], 0), 70)
    xs, x = {}, X0
    for c in range(cols):
        xs[c] = x; x += colw.get(c, 70)
    W = max(x + 20, 1010)
    if W > x + 20:                      # centre the content in a wider frame
        shift = (W - x - 20) / 2
        xs = {c: v + shift for c, v in xs.items()}
    H = Y0 + rows * RH + 20 + FTR_H
    shapes = {}

    def ctr(c, r):
        return xs[c] + colw.get(c, 70) / 2, Y0 + r * RH + RH / 2
    for u in spec["uows"]:
        cx, cy = ctr(u["col"], u["row"])
        shapes[u["id"]] = ("uow", cx - UW / 2, cy - UH / 2, UW, UH, u)
    for j in spec.get("junctions", []):
        cx, cy = ctr(j["col"], j["row"])
        shapes[j["id"]] = ("j", cx - JW / 2, cy - JH / 2, JW, JH, j)
    for r in spec.get("referents", []):
        cx, cy = ctr(r["col"], r["row"])
        shapes[r["id"]] = ("ref", cx - RW / 2, cy - RHt / 2, RW, RHt, r)

    svg = SVG()
    frame(svg, W, H, spec["node"], spec["title"], spec.get("number", ""), spec.get("status", "РОБОЧИЙ"))
    for sid, (t, x, y, w, h, o) in shapes.items():
        if t == "uow":
            svg.rect(x, y, w, h, sw=2.0)
            svg.line([(x, y + h - 22), (x + w, y + h - 22)], sw=1.0)
            svg.line([(x + w - 46, y + h - 22), (x + w - 46, y + h)], sw=1.0)
            lines = wrap(o["name"], w - 12)
            svg.text(x + w / 2, y + (h - 22 - len(lines) * FPX * LH) / 2 + 1, lines, anchor="middle")
            svg.text(x + w - 23, y + h - 20, [o["num"]], anchor="middle")
            if o.get("ref"):
                svg.text(x + 5, y + h - 20, [o["ref"]])
        elif t == "j":
            svg.rect(x, y, w, h, sw=1.8)
            if o.get("sync"):
                svg.line([(x + 6, y), (x + 6, y + h)], sw=1.4)
                svg.line([(x + w - 6, y), (x + w - 6, y + h)], sw=1.4)
            sym = {"X": "X", "&": "&", "O": "O"}[o["type"]]
            svg.text(x + w / 2, y + h / 2 - 10, [sym], anchor="middle", bold=True, size=17)
            svg.text(x + w / 2, y + h + 2, [o["id"]], anchor="middle")
        else:
            svg.rect(x, y, w, h, sw=1.3)
            lines = wrap(o["name"], w - 10)
            svg.text(x + w / 2, y + (h - len(lines) * FPX * LH) / 2, lines, anchor="middle")
    for lk in spec.get("links", []):
        s, t = lk[0], lk[1]
        kind = lk[2] if len(lk) > 2 else "prec"
        ts, sx_, sy_, sw_, sh_, _ = shapes[s]
        tt, tx_, ty_, tw_, th_, _ = shapes[t]
        scx, scy = sx_ + sw_ / 2, sy_ + sh_ / 2
        tcx, tcy = tx_ + tw_ / 2, ty_ + th_ / 2
        if kind == "referent":   # line without arrowhead, shortest side-to-side
            if abs(scx - tcx) < 2:
                pts = [(scx, sy_ if tcy < scy else sy_ + sh_), (tcx, ty_ + th_ if tcy < scy else ty_)]
            else:
                pts = [(scx, sy_ if tcy < scy else sy_ + sh_), (scx, tcy), (tx_ if tcx > scx else tx_ + tw_, tcy)]
            svg.line(pts, sw=1.2)
            continue
        if abs(scy - tcy) < 1:
            pts = [(sx_ + sw_, scy), (tx_, tcy)]
        elif tcx > scx:
            if ts == "j" or tt == "j":
                # fan-out from junction: leave right side then vertical in front of the target
                mx = (sx_ + sw_ + tx_) / 2
                pts = [(sx_ + sw_, scy), (mx, scy), (mx, tcy), (tx_, tcy)]
            else:
                mx = (sx_ + sw_ + tx_) / 2
                pts = [(sx_ + sw_, scy), (mx, scy), (mx, tcy), (tx_, tcy)]
        else:
            yb = max(sy_ + sh_, ty_ + th_) + 16
            pts = [(scx, sy_ + sh_), (scx, yb), (tcx, yb), (tcx, ty_ + th_)]
        dash = "6 4" if kind == "relational" else None
        svg.line(pts, sw=1.5, dash=dash)
        svg.head(pts[-2], pts[-1])
        if kind == "object":                     # object flow: double arrowhead
            (ax, ay), (bx2, by2) = pts[-2], pts[-1]
            L = math.hypot(bx2 - ax, by2 - ay) or 1
            back = (bx2 - (bx2 - ax) / L * 9, by2 - (by2 - ay) / L * 9)
            svg.head(pts[-2], back)
    svg.save(svg_path, W, H)
    return W, H


# ------------------------------------------------------------------------------------------- node tree
def render_tree(spec, svg_path):
    BW, BH, HG, VG = spec.get("bw", 184), spec.get("bh", 58), 24, spec.get("vg", 30)
    root = spec["root"]
    lv1 = root.get("children", [])
    col_w = BW + HG
    RW = BW + 70
    W = 30 + len(lv1) * col_w + 6

    def h_of(nd, w, bold=False):
        return max(BH, len(wrap(nd["name"], w - 14, bold)) * FPX * LH + 26)
    rh = h_of(root, RW, True)
    l1h = max(h_of(c, BW) for c in lv1)
    stack = max([sum(h_of(g, BW - 18) + 10 for g in c.get("children", [])) for c in lv1] + [0])
    ry = HDR_H + 18
    y1 = ry + rh + VG
    H = y1 + l1h + (VG + stack if stack else 0) + 10 + FTR_H
    svg = SVG()
    frame(svg, W, H, spec.get("node", "A0"), spec["title"], spec.get("number", ""), "РОБОЧИЙ")

    def box(x, y, nd, bold=False, w=BW, h=None):
        lines = wrap(nd["name"], w - 14, bold)
        h = h or h_of(nd, w, bold)
        svg.rect(x, y, w, h, sw=2.0 if bold else 1.6)
        svg.text(x + w / 2, y + (h - 18 - len(lines) * FPX * LH) / 2 + 2, lines, anchor="middle", bold=bold)
        svg.text(x + w - 5, y + h - FPX - 3, [nd["id"]], anchor="end")
        return h
    rx = (W - RW) / 2
    box(rx, ry, root, bold=True, w=RW, h=rh)
    for i, c in enumerate(lv1):
        x = 30 + i * col_w
        box(x, y1, c, h=l1h)
        svg.line([(rx + RW / 2, ry + rh), (rx + RW / 2, ry + rh + VG / 2), (x + BW / 2, ry + rh + VG / 2),
                  (x + BW / 2, y1)], sw=1.3)
        yy = y1 + l1h + VG
        for g in c.get("children", []):
            gx = x + 18
            gh = box(gx, yy, g, w=BW - 18)
            svg.line([(x + 8, y1 + l1h), (x + 8, yy + gh / 2), (gx, yy + gh / 2)], sw=1.2)
            yy += gh + 10
    svg.save(svg_path, W, H)
    return W, H


# ------------------------------------------------------------------------------------------- render + gate
def render(spec, out_base, min_pt=10.0):
    out_base = Path(out_base)
    svg = out_base.with_suffix(".svg")
    fn = {"idef0": render_idef0, "idef3": render_idef3, "tree": render_tree}[spec["kind"]]
    W, H = fn(spec, svg)
    png = out_base.with_suffix(".png")
    res = {"file": out_base.name, "native_px": [round(W), round(H)], "min_font_px": FPX}
    cm_to_pt = 72 / 2.54
    best = None
    for name, (bw, bh) in {"portrait": (16.5, 22.5), "landscape": (25.7, 14.5)}.items():
        wcm = min(bw, bh * W / H, 13.0 * W / FPX / cm_to_pt)      # all text is FPX; cap at ~13 pt
        pt = FPX * wcm * cm_to_pt / W
        res[name] = {"width_cm": round(wcm, 2), "font_pt": round(pt, 1), "main_pt": round(pt, 1)}
        if pt >= min_pt and best is None:
            best = name
    best = best or max(("portrait", "landscape"), key=lambda n: res[n]["main_pt"])
    zoom = max(3, math.ceil(300 * res[best]["width_cm"] / 2.54 / W))
    subprocess.run(["rsvg-convert", "-z", str(zoom), "-b", "white", "-o", str(png), str(svg)], check=True)
    for name in ("portrait", "landscape"):
        res[name]["dpi"] = round(W * zoom / (res[name]["width_cm"] / 2.54))
    res.update(orientation=best, width_cm=res[best]["width_cm"], legible=res[best]["main_pt"] >= min_pt)
    out_base.with_suffix(".layout.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
    return res


if __name__ == "__main__":
    print("library module — use from labN/make_labN.py")
