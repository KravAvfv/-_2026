"""Схеми «Теорії систем»: одна побудова → PNG для звіту (svg_fig.Fig, перевірка розбірливості ≥ 10 pt) і
редагований draw.io-файл (вимога методичних вказівок: схема, створена в редакторі на кшталт Draw.io)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path += [str(ROOT / "cybersec_work" / "lab1"), str(ROOT / "tools")]
from svg_fig import Fig, FONT  # noqa: E402
from drawio_lib import Drawio, hlabel, style  # noqa: E402


class TFig(Fig):
    def __init__(self, W, H, fpx=28, name="Схема"):
        super().__init__(W, H, fpx)
        self.dw = Drawio(name)
        self.pt = round(fpx * 0.75)            # px → pt для draw.io

    def _font(self, bold=False, size=None):
        return dict(fontFamily=FONT, fontSize=round((size or self.fpx) * 0.75), fontStyle=1 if bold else 0,
                    fontColor="#000000")

    def text(self, x, y, lines, size=None, bold=False, anchor="middle", bg=False, _rec=True):
        super().text(x, y, lines, size, bold, anchor, bg)
        if not _rec:
            return
        lines = [lines] if isinstance(lines, str) else lines
        sz = size or self.fpx
        w = max(len(s) for s in lines) * sz * 0.55 + 10
        h = len(lines) * sz * 1.18 + 4
        x0 = x - w / 2 if anchor == "middle" else x
        self.dw.vertex(x0, y - h / 2, w, h, hlabel(lines),
                       style(text=True, html=1, whiteSpace="wrap", align="center" if anchor == "middle" else "left",
                             verticalAlign="middle", fillColor="#FFFFFF" if bg else "none", strokeColor="none",
                             **self._font(bold, size)))

    def box(self, cx, cy, w, h, lines, shape="rect", bold=False, dash=None, fill="#fff"):
        tmp = self.dw                           # Fig.box рисує текст через self.text — не дублюємо його в draw.io
        self.dw = Drawio("_")
        super().box(cx, cy, w, h, lines, shape, bold, dash, fill)
        self.dw = tmp
        extra = {"rect": {}, "round": dict(rounded=1, arcSize=50), "hex": dict(shape="hexagon", perimeter="hexagonPerimeter2", size=0.15),
                 "cyl": dict(shape="cylinder3", boundedLbl=1, size=12)}[shape]
        self.dw.vertex(cx - w / 2, cy - h / 2, w, h, hlabel(lines or []),
                       style(html=1, whiteSpace="wrap", fillColor=fill if fill != "#fff" else "#FFFFFF",
                             strokeColor="#000000", strokeWidth=2, dashed=1 if dash else None, **extra,
                             **self._font(bold)))

    def frame(self, x, y, w, h, title, dash="10 6", bottom=False, fill="#FAFAFA"):
        tmp = self.dw
        self.dw = Drawio("_")
        super().frame(x, y, w, h, title, dash, bottom, fill)
        self.dw = tmp
        self.dw.vertex(x, y, w, h, hlabel([title]),
                       style(html=1, whiteSpace="wrap", fillColor=fill, strokeColor="#404040", strokeWidth=2,
                             dashed=1 if dash else None, align="left", spacingLeft=12,
                             verticalAlign="bottom" if bottom else "top", **self._font(True)))

    def line(self, pts, label=None, at=None, dash=None, width=2, head=True, both=False):
        """Лінія зв’язку: width=5 — енергетичний (силовий) зв’язок, dash — інформаційний бездротовий."""
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = (' marker-end="url(#ar)"' if head else "") + (' marker-start="url(#as)"' if both else "")
        self.out.append('<polyline points="' + " ".join(f"{a},{b}" for a, b in pts) +
                        f'" fill="none" stroke="#000" stroke-width="{width}"{m}{d}/>')
        self.dw.edge([tuple(p) for p in pts], "",
                     style(html=1, rounded=0, endArrow="block" if head else "none", endFill=1,
                           startArrow="block" if both else "none", startFill=1, strokeColor="#000000",
                           strokeWidth=width, dashed=1 if dash else None))
        if label:
            if at is None:
                (x1, y1), (x2, y2) = pts[0], pts[1]
                at = ((x1 + x2) / 2, (y1 + y2) / 2)
            self.text(at[0], at[1], label, bg=True)

    arrow = line

    def save(self, base, orientation="portrait"):
        png = super().save(base, orientation)
        out = Path(base).parent.parent / "drawio" / (Path(base).name + ".drawio")
        self.dw.save(out)
        return png
