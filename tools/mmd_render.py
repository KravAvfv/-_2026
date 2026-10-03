#!/usr/bin/env python3
"""Render a Mermaid .mmd file to a print-grade PNG and check legibility for Word embedding.

Usage:  .venv/bin/python tools/mmd_render.py <file.mmd> [--scale 3] [--min-pt 10]

Pipeline:
  1. mmdc -> SVG (intrinsic geometry, scale 1) to measure the diagram's native width/height and
     the smallest font-size actually used in the drawing.
  2. mmdc -> PNG at --scale (default 3, i.e. ~3x native px) with white background.
  3. Predict the rendered font size (pt) when the image is fitted into the usable text width of a
     portrait page (16.5 cm) and a landscape page (25.7 cm) with the max height constraints.
  4. Print a verdict + JSON sidecar (<file>.layout.json) consumed by tools/build_report.py:
       orientation = portrait | landscape, width_cm = recommended placement width.
Exit code 0 = legible (>= --min-pt somewhere), 3 = too dense even in landscape (split the diagram).
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "mermaid-config.json"
PAGES = {  # usable text box (cm) — must match build_report.py geometry
    "portrait": (16.5, 22.5),    # 21.0 - 3.0 - 1.5 ; leave room for caption on 29.7 - 2 - 2
    "landscape": (25.7, 14.5),   # 29.7 - 2.0 - 2.0 ; 21.0 - 3.0 - 1.5 minus caption
}
CM_TO_PT = 72 / 2.54


def run_mmdc(src: Path, out: Path, scale: int):
    cmd = ["mmdc", "-i", str(src), "-o", str(out), "-b", "white", "-c", str(CONFIG), "-s", str(scale)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        sys.stderr.write(r.stdout + r.stderr)
        sys.exit(1)


def svg_metrics(svg: Path):
    """Return native width/height and the smallest font-size (px) of text actually drawn."""
    t = svg.read_text(encoding="utf-8")
    m = re.search(r'viewBox="([\d.\-]+) ([\d.\-]+) ([\d.]+) ([\d.]+)"', t)
    w, h = (float(m.group(3)), float(m.group(4))) if m else (None, None)
    css = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", t, re.S))
    markup = re.sub(r"<style[^>]*>.*?</style>", "", t, flags=re.S)
    used = set()
    for cl in re.findall(r'class="([^"]*)"', markup):
        used.update(cl.split())
    sizes = []
    for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", css):
        fm = re.search(r"font-size:\s*([\d.]+)px", body)
        if not fm or "tooltip" in sel.lower():
            continue
        # keep the rule only if at least one selector alternative references drawn classes only
        alive = False
        for alt in sel.split(","):
            classes = re.findall(r"\.([\w-]+)", alt)
            if all(c in used for c in classes):
                alive = True
                break
        if alive:
            sizes.append(float(fm.group(1)))
    sizes += [float(x) for x in re.findall(r'font-size:\s*([\d.]+)px', markup)]
    sizes += [float(x) for x in re.findall(r'font-size="([\d.]+)(?:px)?"', markup)]
    sizes = [x for x in sizes if x >= 6]          # ignore hidden/marker artefacts
    return w, h, (min(sizes) if sizes else 16.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mmd")
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--min-pt", type=float, default=10.0)
    ap.add_argument("--target-pt", type=float, default=13.0,
                    help="do not enlarge small diagrams beyond this effective font size")
    a = ap.parse_args()
    src = Path(a.mmd).resolve()
    svg, png = src.with_suffix(".svg"), src.with_suffix(".png")
    run_mmdc(src, svg, 1)
    run_mmdc(src, png, a.scale)
    w, h, fpx = svg_metrics(svg)
    from PIL import Image
    pw, ph = Image.open(png).size
    if not w:
        w, h = pw / a.scale, ph / a.scale
    res = {"file": src.name, "native_px": [round(w), round(h)], "png_px": [pw, ph], "min_font_px": fpx}
    best = None
    for name, (bw, bh) in PAGES.items():
        width_cm = min(bw, bh * w / h)              # fit inside box, keep aspect
        natural = a.target_pt * w / fpx / CM_TO_PT  # width giving target_pt text
        width_cm = max(min(width_cm, natural), min(width_cm, 8.0))
        pt = fpx * (width_cm * CM_TO_PT) / w        # 1 svg px rendered at width_cm
        dpi = pw / (width_cm / 2.54)
        res[name] = {"width_cm": round(width_cm, 2), "font_pt": round(pt, 1), "dpi": round(dpi)}
        if pt >= a.min_pt and best is None:
            best = name                              # prefer portrait when it is legible
    if best is None:
        best = max(PAGES, key=lambda n: res[n]["font_pt"])
    res["orientation"] = best
    res["width_cm"] = res[best]["width_cm"]
    res["legible"] = res[best]["font_pt"] >= a.min_pt
    res["aspect"] = round(w / h, 2)
    src.with_suffix(".layout.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
    print(json.dumps(res, ensure_ascii=False))
    if not res["legible"]:
        print(f"TOO DENSE: smallest text would be {res[best]['font_pt']} pt (< {a.min_pt}) even in {best}. "
              f"Split the diagram, shorten labels or switch direction (TB<->LR).", file=sys.stderr)
        sys.exit(3)
    if res[best]["dpi"] < 300:                      # self-heal: re-render sharper
        scale = a.scale
        while res[best]["dpi"] < 300 and scale < 8:
            scale += 1
            run_mmdc(src, png, scale)
            pw, ph = Image.open(png).size
            res[best]["dpi"] = round(pw / (res["width_cm"] / 2.54))
        res["png_px"] = [pw, ph]
        src.with_suffix(".layout.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
        print(f"re-rendered at -s {scale}: {res[best]['dpi']} dpi")


if __name__ == "__main__":
    main()
