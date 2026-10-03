#!/usr/bin/env python3
"""Render a PlantUML (.puml) diagram to SVG + print PNG with the project legibility gate.

Usage: .venv/bin/python tools/puml_render.py <file.puml> [--min-pt 10]

* Uses tools/plantuml/plantuml.jar (PlantUML 1.2026.8, sha1-verified from Maven Central) with the built-in
  Smetana layout (no Graphviz needed). The common style (Times New Roman 15 px, monochrome) is injected from
  STYLE below, so .puml sources contain only the model.
* Writes <file>.svg, <file>.png (rsvg-convert, zoom chosen for >= 300 dpi) and <file>.layout.json
  (orientation / width_cm / font_pt) consumed by tools/build_report.py. Exit 3 = too dense.
"""
import json, math, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JAR = ROOT / "tools/plantuml/plantuml.jar"
FPX = 15
STYLE = f"""!pragma layout smetana
skinparam dpi 96
skinparam defaultFontName Times New Roman
skinparam defaultFontSize {FPX}
skinparam shadowing false
skinparam monochrome true
skinparam backgroundColor #FFFFFF
skinparam ArrowColor #000000
skinparam ArrowFontSize {FPX}
skinparam ArrowThickness 1.2
skinparam ActorBorderThickness 1.3
skinparam usecaseBorderThickness 1.4
skinparam classBorderThickness 1.4
skinparam classAttributeIconSize 0
skinparam packageStyle rectangle
skinparam roundcorner 14
skinparam sequenceMessageAlign center
skinparam sequenceLifeLineBorderColor #000000
skinparam BoxPadding 6
skinparam ActivityBorderThickness 1.4
skinparam SwimlaneTitleFontSize {FPX + 1}
skinparam SwimlaneTitleFontStyle bold
skinparam TitleFontSize {FPX + 1}
"""


def render(src, min_pt=10.0):
    src = Path(src).resolve()
    text = src.read_text(encoding="utf-8")
    if "@startuml" not in text:
        sys.exit(f"{src.name}: no @startuml")
    body = text.replace("@startuml", "@startuml\n" + STYLE, 1)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "d.puml"
        tmp.write_text(body, encoding="utf-8")
        r = subprocess.run(["java", "-Djava.awt.headless=true", "-jar", str(JAR), "-tsvg", "-charset", "UTF-8",
                            "-failfast2", str(tmp)], capture_output=True, text=True)
        out = Path(td) / "d.svg"
        if r.returncode != 0 or not out.exists():
            sys.stderr.write(r.stdout + r.stderr)
            sys.exit(1)
        svg_t = out.read_text(encoding="utf-8")
    if "Syntax Error" in svg_t or "An error has occured" in svg_t:
        sys.exit(f"{src.name}: PlantUML syntax error (see {src.with_suffix('.svg')})")
    src.with_suffix(".svg").write_text(svg_t, encoding="utf-8")
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg_t)
    W, H = float(m.group(1)), float(m.group(2))
    sizes = [float(x) for x in re.findall(r'font-size="([\d.]+)"', svg_t)]
    fpx = min([s for s in sizes if s >= 8] or [FPX])
    cm_to_pt = 72 / 2.54
    res = {"file": src.name, "native_px": [round(W), round(H)], "min_font_px": fpx}
    best = None
    for name, (bw, bh) in {"portrait": (16.5, 22.5), "landscape": (25.7, 14.5)}.items():
        wcm = min(bw, bh * W / H, 13.0 * W / fpx / cm_to_pt)
        pt = fpx * wcm * cm_to_pt / W
        res[name] = {"width_cm": round(wcm, 2), "font_pt": round(pt, 1)}
        if pt >= min_pt and best is None:
            best = name
    best = best or max(("portrait", "landscape"), key=lambda n: res[n]["font_pt"])
    zoom = max(3, math.ceil(300 * res[best]["width_cm"] / 2.54 / W))
    png = src.with_suffix(".png")
    subprocess.run(["rsvg-convert", "-z", str(zoom), "-b", "white", "-o", str(png), str(src.with_suffix(".svg"))],
                   check=True)
    for name in ("portrait", "landscape"):
        res[name]["dpi"] = round(W * zoom / (res[name]["width_cm"] / 2.54))
    res.update(orientation=best, width_cm=res[best]["width_cm"], legible=res[best]["font_pt"] >= min_pt)
    src.with_suffix(".layout.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
    return res


if __name__ == "__main__":
    r = render(sys.argv[1])
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r["legible"] else 3)
