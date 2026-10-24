#!/usr/bin/env python3
"""Lines through labels in a PlantUML SVG: detection and automatic label relocation.

Usage: .venv/bin/python tools/svg_overlap.py <file.svg> [...]   (exit 1 if any overlap remains)

* check(svg) — every text is tested against every line, path, polygon and rect edge of the other top-level groups
  (entities, clusters, links); link labels are also tested against their own link (a label sits beside its line,
  not on it). Text inside its own box/cluster is not tested against that box.
* fix_labels(svg) — moves every colliding link label (multiplicities, association names, arrow labels) to the
  nearest free spot around its original anchor (outside class boxes, off every line, clear of other texts) and
  slides colliding cluster titles along the cluster's top band. Used by tools/puml_render.py before rasterising.
"""
import math, re, sys
import xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"
PAD = 1.0          # tolerance (px) when testing a placed label
GAP = 2.5          # clearance (px) required around a relocated label
MAXR = 46          # search radius (px) for a relocated label


def nums(s):
    return [float(v) for v in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", s)]


def path_segs(d):
    segs, cur, start = [], None, None
    for cmd, args in re.findall(r"([MLCQZmlcqz])([^MLCQZmlcqz]*)", d):
        a = nums(args)
        if cmd == "M":
            cur = start = (a[0], a[1])
            for i in range(2, len(a) - 1, 2):
                segs.append((cur, (a[i], a[i + 1]))); cur = (a[i], a[i + 1])
        elif cmd == "L":
            for i in range(0, len(a) - 1, 2):
                segs.append((cur, (a[i], a[i + 1]))); cur = (a[i], a[i + 1])
        elif cmd == "C":
            for i in range(0, len(a) - 5, 6):
                p0, p1, p2, p3 = cur, (a[i], a[i + 1]), (a[i + 2], a[i + 3]), (a[i + 4], a[i + 5])
                prev = p0
                for k in range(1, 21):
                    t = k / 20
                    pt = tuple((1 - t) ** 3 * p0[j] + 3 * (1 - t) ** 2 * t * p1[j] + 3 * (1 - t) * t * t * p2[j]
                               + t ** 3 * p3[j] for j in (0, 1))
                    segs.append((prev, pt)); prev = pt
                cur = p3
        elif cmd in "Zz" and cur and start:
            segs.append((cur, start)); cur = start
    return segs


def geom(el):
    tag = el.tag.replace(NS, "")
    if tag == "line":
        g = [float(el.get(k)) for k in ("x1", "y1", "x2", "y2")]
        return [((g[0], g[1]), (g[2], g[3]))]
    if tag == "path":
        return path_segs(el.get("d", ""))
    if tag in ("polygon", "polyline"):
        a = nums(el.get("points", ""))
        pts = list(zip(a[0::2], a[1::2]))
        return list(zip(pts, pts[1:] + (pts[:1] if tag == "polygon" else [])))
    if tag == "rect":
        x, y, w, h = (float(el.get(k, 0)) for k in ("x", "y", "width", "height"))
        if w == 0 or h == 0:
            return []
        p = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        return list(zip(p, p[1:] + p[:1]))
    return []


def seg_box(s, b):
    """Liang–Barsky: does segment s intersect box b = (x0, y0, x1, y1)?"""
    (x0, y0), (x1, y1) = s
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - b[0]), (dx, b[2] - x0), (-dy, y0 - b[1]), (dy, b[3] - y0)):
        if p == 0:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return False
    return True


def box_box(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def grow(b, d):
    return (b[0] - d, b[1] - d, b[2] + d, b[3] + d)


def text_box(el):
    fs = float(el.get("font-size", 14)); x = float(el.get("x")); y = float(el.get("y"))
    w = float(el.get("textLength") or len(el.text.strip()) * fs * 0.5)
    return (x, y - 0.72 * fs, x + w, y + 0.18 * fs)


def scan(root):
    """Top-level groups → texts [(gi, cls, el, box)], shapes [(gi, cls, segs)], solid boxes [(gi, box)]."""
    groups = [g for g in root.iter(NS + "g") if g.get("class") in ("entity", "cluster", "link")]
    texts, shapes, solids = [], [], []
    for gi, g in enumerate(groups):
        cls = g.get("class")
        for el in g.iter():
            tag = el.tag.replace(NS, "")
            if tag == "text" and (el.text or "").strip():
                texts.append((gi, cls, el, text_box(el)))
            elif tag in ("line", "path", "polygon", "polyline", "rect"):
                segs = geom(el)
                shapes.append((gi, cls, segs))
                if cls == "entity" and tag in ("rect", "polygon") and segs:
                    xs = [p[0] for s in segs for p in s]; ys = [p[1] for s in segs for p in s]
                    solids.append((gi, (min(xs), min(ys), max(xs), max(ys))))
    return groups, texts, shapes, solids


def collisions(box, gi, cls, shapes, pad=PAD):
    b = grow(box, -pad)
    return [gj for gj, cls2, segs in shapes
            if not (gi == gj and cls != "link") and any(seg_box(s, b) for s in segs)]


def check(svg_text):
    groups, texts, shapes, _ = scan(ET.fromstring(svg_text))
    bad = []
    for gi, cls, el, box in texts:
        hit = collisions(box, gi, cls, shapes)
        if hit:
            g = groups[hit[0]]
            bad.append((el.text.strip(), g.get("data-qualified-name") or g.get("id") or g.get("class")))
    return bad


def fix_labels(svg_text):
    """Relocate colliding link labels / cluster titles; returns the new SVG text."""
    root = ET.fromstring(svg_text)
    groups, texts, shapes, solids = scan(root)
    vb = nums(root.get("viewBox", "0 0 1e9 1e9"))
    fixed = [box for gi, cls, el, box in texts]           # boxes of all texts, updated as labels move
    moves = []
    for k, (gi, cls, el, box) in enumerate(texts):
        others = fixed[:k] + fixed[k + 1:]
        crowded = cls == "link" and any(box_box(grow(box, 2), o) for o in others)
        if not crowded and not collisions(box, gi, cls, shapes):
            continue
        w, h = box[2] - box[0], box[3] - box[1]

        def free(b):
            if b[0] < vb[0] + 1 or b[1] < vb[1] + 1 or b[2] > vb[0] + vb[2] - 1 or b[3] > vb[1] + vb[3] - 1:
                return False
            if collisions(b, gi, cls, shapes, pad=-GAP):
                return False
            if cls == "link" and any(box_box(grow(b, GAP), s) for _, s in solids):
                return False
            return not any(box_box(grow(b, 3), o) for o in others)

        best = None
        if cls == "link":
            for r in range(2, MAXR + 1, 2):
                for a in range(0, 360, 15):
                    dx, dy = r * math.cos(math.radians(a)), r * math.sin(math.radians(a))
                    b = (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)
                    if free(b):
                        best = (dx, dy); break
                if best:
                    break
        elif cls == "cluster":                             # slide the title along the top band
            g = groups[gi]
            xs = [p[0] for _, c, segs in shapes for s in segs for p in s if _ == gi]
            lo, hi = min(xs) + 6, max(xs) - 16 - w
            cands = sorted((x - box[0] for x in range(int(lo), int(hi) + 1)), key=abs)
            best = next(((dx, 0) for dx in cands if free((box[0] + dx, box[1], box[2] + dx, box[3]))), None)
        if best:
            dx, dy = best
            nx, ny = float(el.get("x")) + dx, float(el.get("y")) + dy
            moves.append((el.get("x"), el.get("y"), el.text, f"{nx:.3f}", f"{ny:.3f}"))
            fixed[k] = (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)
    for ox, oy, txt, nx, ny in moves:
        pat = re.compile(r'(<text x=")' + re.escape(ox) + r'(" y=")' + re.escape(oy) + r'("[^>]*>' +
                         re.escape(txt) + r"</text>)")
        svg_text, n = pat.subn(lambda m: m.group(1) + nx + m.group(2) + ny + m.group(3), svg_text, count=1)
        assert n == 1, (ox, oy, txt)
    return svg_text


if __name__ == "__main__":
    rc = 0
    for f in sys.argv[1:]:
        bad = check(open(f, encoding="utf-8").read())
        print(f"{f}: {'OK' if not bad else f'{len(bad)} overlap(s)'}")
        for t, who in bad:
            print(f"   «{t}» × {who}")
        rc |= bool(bad)
    sys.exit(rc)
