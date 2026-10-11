#!/usr/bin/env python3
"""Hand-placed block diagrams (SVG → PNG via rsvg-convert) with the same legibility sidecar (`.layout.json`)
as tools/mmd_render.py: font size in Word is computed from the placement width, not assumed."""
import json, subprocess
from pathlib import Path
from xml.sax.saxutils import escape

FONT = "Times New Roman"
PAGES = {"portrait": (16.5, 22.5), "landscape": (25.7, 14.5)}
CM_TO_PT = 72 / 2.54


class Fig:
    def __init__(self, W, H, fpx=28):
        self.W, self.H, self.fpx = W, H, fpx
        self.out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
                    '<defs><marker id="ar" markerWidth="12" markerHeight="12" refX="11" refY="6" orient="auto" '
                    'markerUnits="userSpaceOnUse"><path d="M0,0 L12,6 L0,12 z" fill="#000"/></marker>'
                    '<marker id="as" markerWidth="12" markerHeight="12" refX="1" refY="6" orient="auto" '
                    'markerUnits="userSpaceOnUse"><path d="M12,0 L0,6 L12,12 z" fill="#000"/></marker></defs>',
                    f'<rect width="{W}" height="{H}" fill="#fff"/>']

    def text(self, x, y, lines, size=None, bold=False, anchor="middle", bg=False):
        size = size or self.fpx
        lines = [lines] if isinstance(lines, str) else lines
        lh = size * 1.18
        y0 = y - lh * (len(lines) - 1) / 2
        if bg:
            w = max(len(s) for s in lines) * size * 0.52 + 12
            self.out.append(f'<rect x="{x - w / 2}" y="{y0 - lh / 2 - 2}" width="{w}" height="{lh * len(lines) + 4}" '
                            'fill="#fff"/>')
        for i, s in enumerate(lines):
            self.out.append(f'<text x="{x}" y="{y0 + i * lh}" font-family="{FONT}" font-size="{size}" '
                            f'text-anchor="{anchor}" dominant-baseline="central"'
                            f'{" font-weight=\"bold\"" if bold else ""}>{escape(s)}</text>')

    def box(self, cx, cy, w, h, lines, shape="rect", bold=False, dash=None, fill="#fff"):
        x, y = cx - w / 2, cy - h / 2
        d = f' stroke-dasharray="{dash}"' if dash else ""
        if shape == "rect":
            self.out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#000" '
                            f'stroke-width="2"{d}/>')
        elif shape == "round":
            self.out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2}" fill="{fill}" '
                            f'stroke="#000" stroke-width="2"{d}/>')
        elif shape == "hex":
            k = h / 3
            pts = [(x + k, y), (x + w - k, y), (x + w, cy), (x + w - k, y + h), (x + k, y + h), (x, cy)]
            self.out.append('<polygon points="' + " ".join(f"{a},{b}" for a, b in pts) +
                            f'" fill="{fill}" stroke="#000" stroke-width="2"{d}/>')
        if lines:
            self.text(cx, cy, lines, bold=bold)

    def frame(self, x, y, w, h, title, dash="10 6", bottom=False, fill="#FAFAFA"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#404040" '
                        f'stroke-width="2"{d}/>')
        ty = y + h - self.fpx * 0.9 if bottom else y + self.fpx * 0.9
        self.text(x + 14, ty, title, anchor="start", bold=True)

    def arrow(self, pts, label=None, at=None, dash=None, width=2, both=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        if both:
            d += ' marker-start="url(#as)"'
        self.out.append('<polyline points="' + " ".join(f"{a},{b}" for a, b in pts) +
                        f'" fill="none" stroke="#000" stroke-width="{width}" marker-end="url(#ar)"{d}/>')
        if label:
            if at is None:
                (x1, y1), (x2, y2) = pts[0], pts[1]
                at = ((x1 + x2) / 2, (y1 + y2) / 2)
            self.text(at[0], at[1], label, bg=True)

    def save(self, base, orientation="portrait"):
        base = Path(base)
        self.out.append("</svg>")
        svg = base.with_suffix(".svg"); png = base.with_suffix(".png")
        svg.write_text("\n".join(self.out), encoding="utf-8")
        scale = 3
        subprocess.run(["rsvg-convert", "-z", str(scale), "-b", "white", "-o", str(png), str(svg)], check=True)
        lay = {"file": svg.name, "native_px": [self.W, self.H], "png_px": [self.W * scale, self.H * scale],
               "min_font_px": self.fpx}
        for o, (pw, ph) in PAGES.items():
            wcm = min(pw, ph * self.W / self.H)
            lay[o] = {"width_cm": round(wcm, 2), "font_pt": round(self.fpx * wcm / self.W * CM_TO_PT, 1),
                      "dpi": int(self.W * scale / (wcm / 2.54))}
        lay["orientation"] = orientation
        lay["width_cm"] = lay[orientation]["width_cm"]
        lay["legible"] = lay[orientation]["font_pt"] >= 10 and lay[orientation]["dpi"] >= 300
        base.with_suffix(".layout.json").write_text(json.dumps(lay, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(lay, ensure_ascii=False))
        if not lay["legible"]:
            raise SystemExit(f"{svg.name}: not legible")
        return png
