"""Імітація рукописного конспекту в зошиті в клітинку (фото на телефон).

Розмітка рядка:
  {чисельник|знаменник}  — дріб;   x^2, x^<−0,2t>  — верхній індекс;   x_1, W_<роз>  — нижній індекс
  ~~слово~~              — закреслено однією лінією;   ##слово##  — замальовано «пилкою»
  \\{ \\}                — буквальні фігурні дужки;   ✓ — галочка (малюється рукою)
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = Path(__file__).resolve().parent
CAVEAT = str(HERE / "fonts" / "Caveat.ttf")          # формули — друкованими літерами
SCRIPT = str(HERE / "fonts" / "Caveat.ttf")  # текст: той самий Caveat, але ширший, жирніший і недбаліший
SX = 1.14  # розтяг літер по ширині (почерк автора — широкі округлі літери)
try:
    from fontTools.ttLib import TTFont
    SCRIPT_CMAP = set(TTFont(SCRIPT).getBestCmap())
except Exception:  # pragma: no cover
    SCRIPT_CMAP = set()
FALLBACK = "/usr/share/fonts/wps-fonts/segoepr.ttf"
FALLBACK_CHARS = set("δζω∞≥≤±∫→φΔγ√ν")

W, H, CELL = 1320, 1720, 37
GRID_X0, GRID_Y0 = 11, 9
MARGIN_X = W - 4 * CELL - 12          # червона лінія полів
LEFT = GRID_X0 + CELL                 # пишемо з першої клітинки
RIGHT = MARGIN_X - 18
TOP = GRID_Y0 + CELL * 2
BOTTOM = H - CELL
SIZE = 62          # текст
MATH = 56          # формули


# ---------------------------------------------------------------- розбір розмітки
def parse(s):
    pos = 0

    def seq(stops):
        nonlocal pos
        out, buf = [], ""

        def flush():
            nonlocal buf
            if buf:
                out.append(("txt", buf))
                buf = ""

        while pos < len(s):
            c = s[pos]
            if s.startswith("~~", pos) and "~~" in stops:
                break
            if s.startswith("##", pos) and "##" in stops:
                break
            if c in stops:
                break
            if c == "\\" and pos + 1 < len(s):
                buf += s[pos + 1]
                pos += 2
            elif s.startswith("~~", pos) or s.startswith("##", pos):
                mark = s[pos:pos + 2]
                flush()
                pos += 2
                inner = seq({mark})
                pos += 2
                out.append(("strike" if mark == "~~" else "scribble", inner))
            elif c == "{":
                flush()
                pos += 1
                num = seq({"|"})
                pos += 1
                den = seq({"}"})
                pos += 1
                out.append(("frac", num, den))
            elif c in "^_":
                flush()
                pos += 1
                if pos < len(s) and s[pos] == "<":
                    pos += 1
                    inner = seq({">"})
                    pos += 1
                else:
                    inner = [("txt", s[pos])]
                    pos += 1
                out.append(("sup" if c == "^" else "sub", inner))
            else:
                buf += c
                pos += 1
        flush()
        return out

    return seq(set())


def split_words(nodes):
    """Розбиває вузли на слова за пробілами у текстових вузлах верхнього рівня."""
    words, cur = [], []
    for n in nodes:
        if n[0] == "txt":
            parts = n[1].split(" ")
            for i, p in enumerate(parts):
                if i > 0:
                    if cur:
                        words.append(cur)
                    cur = []
                if p:
                    cur.append(("txt", p))
        else:
            cur.append(n)
    if cur:
        words.append(cur)
    return words


# ---------------------------------------------------------------- рука
class Hand:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.fonts = {}
        self.style = "math"
        self.pages = []
        self.new_page()

    # --- сторінки
    def new_page(self):
        self.ink = Image.new("L", (W, H), 0)
        self.draw = ImageDraw.Draw(self.ink)
        self.pages.append(self.ink)
        self.y = TOP + self.rng.randint(0, 1) * CELL
        self.slope = 0.0
        self.x0 = LEFT

    def font(self, ch, size):
        if ch in FALLBACK_CHARS:
            path = FALLBACK
        elif self.style == "text" and ord(ch) in SCRIPT_CMAP and ch not in ",.;:":
            path = SCRIPT
        else:
            path = CAVEAT
        size = max(8, int(round(size * (0.82 if path == FALLBACK else 1.0))))
        key = (path, size)
        if key not in self.fonts:
            self.fonts[key] = ImageFont.truetype(path, size)
        return self.fonts[key]

    def track(self, ch):
        return 0.9 * SX if self.style == "text" else 0.96

    def pressure(self):
        return self.rng.randint(205, 255)

    def blit(self, m, x, y):
        x, y = int(round(x)), int(round(y))
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(W, x + m.width), min(H, y + m.height)
        if x1 <= x0 or y1 <= y0:
            return
        part = m.crop((x0 - x, y0 - y, x1 - x, y1 - y))
        box = (x0, y0, x1, y1)
        self.ink.paste(ImageChops.lighter(self.ink.crop(box), part), box)

    # --- штрихи
    def _path(self, pts, amp=1.1, bow=1.0):
        rng = self.rng
        out, v = [], 0.0
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            L = math.hypot(x2 - x1, y2 - y1)
            if L < 0.5:
                continue
            nx, ny = -(y2 - y1) / L, (x2 - x1) / L
            n = max(2, int(L / 7))
            b = rng.uniform(-1, 1) * min(9, L * 0.016) * bow
            for i in range(n + 1):
                t = i / n
                v = 0.8 * v + rng.gauss(0, 0.45 * amp)
                off = b * math.sin(math.pi * t) + v
                out.append((x1 + (x2 - x1) * t + nx * off, y1 + (y2 - y1) * t + ny * off))
        return out

    def stroke(self, pts, width=5, amp=1.7, bow=1.8):
        path = self._path(pts, amp, bow)
        if len(path) > 1:
            self.draw.line(path, fill=self.pressure(), width=width, joint="curve")

    def line(self, a, b, width=5, over=True, bow=1.8):
        (x1, y1), (x2, y2) = a, b
        L = math.hypot(x2 - x1, y2 - y1) or 1
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        if over:  # рука трохи «проскакує» кінці
            s, e = self.rng.uniform(-4, 12), self.rng.uniform(-3, 14)
            x1, y1, x2, y2 = x1 - ux * s, y1 - uy * s, x2 + ux * e, y2 + uy * e
        self.stroke([(x1, y1), (x2, y2)], width, bow=bow)

    def polyline(self, pts, width=5):
        for a, b in zip(pts, pts[1:]):
            self.line(a, b, width, over=False)

    def arrow(self, a, b, width=5, head=17):
        self.line(a, b, width, over=False)
        (x1, y1), (x2, y2) = a, b
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (1, -1):
            da = math.radians(self.rng.uniform(20, 30)) * s
            hl = head * self.rng.uniform(0.85, 1.15)
            self.line((x2, y2), (x2 - hl * math.cos(ang + da), y2 - hl * math.sin(ang + da)), width, over=False)

    def box(self, x, y, w, h, width=5):
        c = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        for i in range(4):
            self.line(c[i], c[(i + 1) % 4], width)

    def circle(self, cx, cy, r, width=5, cross=True, minus=None):
        rng = self.rng
        a0 = rng.uniform(0, 2 * math.pi)
        tot = 2 * math.pi + rng.uniform(0.15, 0.45)
        pts, v = [], 0.0
        for i in range(41):
            a = a0 + tot * i / 40
            v = 0.7 * v + rng.gauss(0, 0.5)
            rr = r * (1 + 0.06 * math.sin(a * 2 + 1)) + v
            pts.append((cx + rr * math.cos(a), cy + rr * 0.95 * math.sin(a)))
        self.draw.line(pts, fill=self.pressure(), width=width, joint="curve")
        if cross:
            d = r * 0.72
            self.line((cx - d, cy - d), (cx + d, cy + d), width - 1)
            self.line((cx - d, cy + d), (cx + d, cy - d), width - 1)
        if minus:  # заштрихований сектор («−»): 'down' | 'up' | 'left'
            base = {"down": math.pi / 2, "up": -math.pi / 2, "left": math.pi}[minus]
            for k in range(6):
                a = base - math.pi / 4 + (k + 0.5) * (math.pi / 2) / 6
                self.line((cx + 3 * math.cos(a), cy + 3 * math.sin(a)),
                          (cx + (r - 3) * math.cos(a), cy + (r - 3) * math.sin(a)), 3, over=False)

    def dot(self, x, y, r=4):
        self.draw.ellipse([x - r, y - r, x + r, y + r], fill=self.pressure())

    def check(self, x, base, size):
        h = size * 0.5
        self.stroke([(x, base - h * 0.5), (x + h * 0.35, base - 2), (x + h * 0.95, base - h * 1.25)], 4, bow=0.3)
        return h * 1.1

    def scribble(self, x1, x2, base, size):
        rng = self.rng
        for _ in range(2):  # дві «петлі» туди-назад, нерівні
            pts, x = [], x1 - 4
            while x < x2 + 4:
                pts.append((x + rng.uniform(-3, 3), base - size * rng.uniform(0.35, 0.7)))
                x += rng.uniform(3, 8)
                pts.append((x + rng.uniform(-3, 3), base + size * rng.uniform(-0.05, 0.1)))
                x += rng.uniform(3, 8)
            self.draw.line(pts, fill=self.pressure(), width=3, joint="curve")
            x1, x2 = x2, x1
            x1, x2 = min(x1, x2), max(x1, x2)

    # --- літери
    def glyph(self, x, base, ch, size):
        if ch == "✓":
            return self.check(x, base, size)
        rng = self.rng
        text = self.style == "text"
        f = self.font(ch, size)
        adv = f.getlength(ch)
        pad = int(size * 0.6)
        gw, gh = int(adv + 2 * pad), int(size * 2.3)
        ox, oy = pad, int(size * 1.55)
        g = Image.new("L", (gw, gh), 0)
        ImageDraw.Draw(g).text((ox, oy), ch, font=f, fill=self.pressure(), anchor="ls")
        sx = SX * rng.uniform(0.94, 1.07) if text else rng.uniform(0.97, 1.05)
        g = g.resize((max(1, int(gw * sx)), gh), Image.BICUBIC)
        ox = ox * sx
        g = g.filter(ImageFilter.MaxFilter(3))          # кулькова ручка, натиск
        j = size * (0.07 if text else 0.04)             # недбалість: кожна літера трохи «гуляє»
        w_, h_ = g.size
        q = [rng.uniform(-j, j) for _ in range(8)]
        g = g.transform(g.size, Image.QUAD, (q[0], q[1], q[2], h_ + q[3], w_ + q[4], h_ + q[5], w_ + q[6], q[7]),
                        resample=Image.BICUBIC)
        g = g.rotate(rng.uniform(-6, 6), resample=Image.BICUBIC, center=(ox, oy))
        sh = (0.24 if text else 0.1) + rng.uniform(-0.06, 0.06)
        g = g.transform(g.size, Image.AFFINE, (1, sh, -sh * oy, 0, 1, 0), resample=Image.BICUBIC)
        y = base + (x - self.x0) * self.slope + rng.uniform(-2.5, 2.5)
        self.blit(g, x - ox, y - oy)
        return adv * self.track(ch) / 0.96 * (sx / SX if text else 1)

    # --- вимірювання / малювання формул
    def measure(self, nodes, size):
        w, up, down = 0.0, size * 0.72, size * 0.24
        for n in nodes:
            k = n[0]
            if k == "txt":
                for ch in n[1]:
                    w += (size * (0.55 if self.style == "text" else 0.32)) if ch == " " else (size * 0.55 if ch == "✓" else self.font(ch, size).getlength(ch) * self.track(ch))
            elif k in ("strike", "scribble"):
                cw, cu, cd = self.measure(n[1], size)
                w += cw
                up, down = max(up, cu), max(down, cd)
            elif k == "sup":
                cw, cu, cd = self.measure(n[1], size * 0.64)
                w += cw + 2
                up = max(up, size * 0.42 + cu)
            elif k == "sub":
                cw, cu, cd = self.measure(n[1], size * 0.64)
                w += cw + 2
                down = max(down, size * 0.2 + cd)
            elif k == "frac":
                s2 = size * 0.9
                aw, au, ad = self.measure(n[1], s2)
                bw, bu, bd = self.measure(n[2], s2)
                w += max(aw, bw) + size * 0.45
                axis, gap = size * 0.3, size * 0.14
                up = max(up, axis + gap + ad + au)
                down = max(down, -axis + gap + bu + bd)
        return w, up, down

    def render(self, nodes, x, base, size, word_jitter=True):
        rng = self.rng
        for n in nodes:
            k = n[0]
            if k == "txt":
                dy, sc = 0.0, 1.0
                for ch in n[1]:
                    if ch == " ":
                        x += size * (rng.uniform(0.45, 0.65) if self.style == "text" else rng.uniform(0.26, 0.42))
                        if word_jitter:
                            dy, sc = rng.uniform(-5, 4), rng.uniform(0.92, 1.09)
                        continue
                    x += self.glyph(x, base + dy, ch, size * sc * rng.uniform(0.96, 1.04)) * rng.uniform(0.9, 1.0)
            elif k in ("strike", "scribble"):
                x1 = x
                x = self.render(n[1], x, base, size, False)
                if k == "strike":
                    yy = base - size * 0.28
                    self.line((x1 - 3, yy + rng.uniform(-3, 3)), (x + 3, yy + rng.uniform(-3, 3)), 4)
                else:
                    self.scribble(x1, x, base, size)
                x += size * 0.15
            elif k == "sup":
                x = self.render(n[1], x + 1, base - size * 0.42, size * 0.64, False) + 2
            elif k == "sub":
                x = self.render(n[1], x + 1, base + size * 0.2, size * 0.64, False) + 2
            elif k == "frac":
                s2 = size * 0.9
                aw, au, ad = self.measure(n[1], s2)
                bw, bu, bd = self.measure(n[2], s2)
                fw = max(aw, bw) + size * 0.25
                axis, gap = size * 0.3, size * 0.14
                bar = base - axis
                x += size * 0.1
                self.render(n[1], x + (fw - aw) / 2 + rng.uniform(-4, 4), bar - gap - ad, s2, False)
                self.render(n[2], x + (fw - bw) / 2 + rng.uniform(-4, 4), bar + gap + bu, s2, False)
                self.line((x, bar), (x + fw, bar + rng.uniform(-2, 2)), 3)
                x += fw + size * 0.1
        return x

    # --- потік тексту
    def _place(self, up, down):
        up, down = max(up, SIZE * 0.75), max(down, SIZE * 0.3)
        lead = SIZE * self.rng.uniform(0.3, 0.45)
        if self.y + up + down + lead > BOTTOM:
            self.new_page()
        base = self.y + up + self.rng.uniform(-4, 4)
        self.y = base + down + lead
        return base

    def text_line(self, nodes, x, size=SIZE, center=False, underline=False, style="text"):
        self.style = style
        w, up, down = self.measure(nodes, size)
        avail = RIGHT - x
        if w > avail:  # довгу формулу пишемо дрібніше
            size *= max(0.72, avail / w)
            w, up, down = self.measure(nodes, size)
        base = self._place(up, down)
        if center:
            x = LEFT + (RIGHT - LEFT - w) / 2
        x += self.rng.uniform(-8, 16)
        self.x0, self.slope = x, self.rng.uniform(-0.02, 0.014)
        xe = self.render(nodes, x, base, size)
        if underline:
            self.line((x - 4, base + 9), (xe + 4, base + 9 + (xe - x) * self.slope), 3)
        return xe

    def para(self, s, indent=1, size=SIZE):
        self.style = "text"
        words = split_words(parse(s))
        line, x = [], LEFT + indent * CELL
        space = size * 0.55
        cur_w = 0
        start = x
        lines = []
        for wd in words:
            ww = self.measure(wd, size)[0]
            if line and start + cur_w + space + ww > RIGHT:
                lines.append(line)
                line, cur_w, start = [], 0, LEFT
            line.append(wd)
            cur_w += (space if len(line) > 1 else 0) + ww
        if line:
            lines.append(line)
        for i, ln in enumerate(lines):
            nodes = []
            for j, wd in enumerate(ln):
                if j:
                    nodes.append(("txt", " "))
                nodes += wd
            self.text_line(nodes, LEFT + indent * CELL if i == 0 else LEFT, size)

    def math(self, s, indent=2, size=MATH):
        self.text_line(parse(s), LEFT + indent * CELL, size, style="math")

    def heading(self, s, size=SIZE + 4, center=False, underline=True):
        if self.y + 6 * CELL > BOTTOM:  # заголовок не лишаємо внизу сторінки
            self.new_page()
        self.text_line(parse(s), LEFT + CELL, size, center=center, underline=underline)

    def gap(self, rows=1):
        self.y += rows * CELL
        if self.y > BOTTOM - CELL:
            self.new_page()

    def figure(self, fn, rows, caption=None):
        need = rows * CELL + (CELL * 2 if caption else 0)
        if self.y + need > BOTTOM:
            self.new_page()
        fn(self, LEFT, self.y)
        self.y += rows * CELL
        if caption:
            self.text_line(parse(caption), LEFT, SIZE - 4, center=True)

    def label(self, s, x, base, size=46):
        self.style = "math"
        self.x0, self.slope = x, 0
        return self.render(parse(s), x, base, size, False)

    def label_c(self, s, cx, base, size=46):
        self.style = "math"
        w = self.measure(parse(s), size)[0]
        return self.label(s, cx - w / 2, base, size)


# ---------------------------------------------------------------- папір і «фото»
def paper():
    img = Image.new("RGB", (W, H), (238, 240, 236))
    d = ImageDraw.Draw(img)
    col = (150, 178, 214)
    for x in range(GRID_X0, W, CELL):
        d.line([(x, 0), (x, H)], fill=col, width=2)
    for y in range(GRID_Y0, H, CELL):
        d.line([(0, y), (W, y)], fill=col, width=2)
    d.line([(MARGIN_X, 0), (MARGIN_X, H)], fill=(214, 150, 190), width=3)
    return img


def _lowfreq(nrng, shape, cells, amp):
    """Плавний шум (хвилястість паперу, нерівне світло)."""
    small = Image.fromarray(((nrng.random(cells) * 255)).astype(np.uint8))
    big = np.asarray(small.resize((shape[1], shape[0]), Image.BICUBIC)).astype(np.float32) / 255.0
    return 1 + (big - 0.5) * 2 * amp


def _warp(img, rng):
    """Сторінка трохи вигнута, як у розкритому зошиті."""
    w, h = img.size
    A, B, C = rng.uniform(10, 22), rng.uniform(8, 18), rng.uniform(-8, 8)
    ph = rng.uniform(-0.4, 0.4)

    def src(x, y):
        dx = A * math.sin(math.pi * y / h) * (x / w - 0.5) + C * (y / h - 0.5) ** 2
        dy = B * math.sin(math.pi * x / w + ph) * (1.2 - y / h) - B * 0.5
        return x + dx, y + dy

    n = 12
    mesh = []
    for i in range(n):
        for j in range(n):
            x0, x1 = w * i / n, w * (i + 1) / n
            y0, y1 = h * j / n, h * (j + 1) / n
            quad = (*src(x0, y0), *src(x0, y1), *src(x1, y1), *src(x1, y0))
            mesh.append(((int(x0), int(y0), int(x1), int(y1)), quad))
    return img.transform(img.size, Image.MESH, mesh, resample=Image.BICUBIC, fillcolor=(60, 50, 44))


def photo(ink_mask, seed):
    rng = random.Random(seed)
    nrng = np.random.default_rng(seed)
    page = np.asarray(paper()).astype(np.float32)
    m = ink_mask.filter(ImageFilter.GaussianBlur(0.8))
    a = np.asarray(m).astype(np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W]
    shift = 12 * np.sin(xx / 260.0 + rng.uniform(0, 6)) * np.cos(yy / 230.0)
    ink = np.stack([40 + shift * 0.4, 48 + shift * 0.4, 168 + shift], -1)   # синя гелева ручка
    a = np.clip(a * 1.08, 0, 1)
    page = page * (1 - a[..., None] * 0.9) + ink * a[..., None] * 0.9
    page *= _lowfreq(nrng, (H, W), (5, 4), 0.05)[..., None]
    img = Image.fromarray(np.clip(page, 0, 255).astype(np.uint8))

    # зошит: обкладинка/стіл по краях, з правого боку — торці інших аркушів
    pad = 70
    Wc, Hc = W + 2 * pad, H + 2 * pad
    bg = Image.new("RGB", (Wc, Hc), (rng.randint(70, 95), rng.randint(58, 70), rng.randint(48, 58)))
    d = ImageDraw.Draw(bg)
    for k in range(7):  # стос сторінок праворуч і знизу
        c = 205 - k * 14 + rng.randint(-6, 6)
        d.rectangle([pad + 6 + k * 3, pad + 8 + k * 3, pad + W + 8 + k * 4, pad + H + 6 + k * 4], fill=(c, c - 2, c - 10))
    bg.paste(img, (pad, pad))
    bg = _warp(bg, rng)
    bg = bg.rotate(rng.uniform(-1.8, 1.8), resample=Image.BICUBIC, fillcolor=(60, 50, 44))
    c = [rng.uniform(0, 45) for _ in range(8)]
    bg = bg.transform(bg.size, Image.QUAD,
                      (c[0], c[1], c[2], Hc - c[3], Wc - c[4], Hc - c[5], Wc - c[6], c[7]),
                      resample=Image.BICUBIC)
    crop = rng.randint(0, 25)
    bg = bg.crop((crop, crop, Wc - crop, Hc - crop))

    # світло: тепле, нерівне, віньєтка, тінь від руки/телефону
    arr = np.asarray(bg).astype(np.float32)
    h2, w2 = arr.shape[:2]
    yy, xx = np.mgrid[0:h2, 0:w2]
    cx, cy = rng.uniform(0.25, 0.75) * w2, rng.uniform(0.15, 0.6) * h2
    r2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / (w2 ** 2 + h2 ** 2)
    light = (1.06 - 0.45 * r2) * _lowfreq(nrng, (h2, w2), (4, 3), 0.06)
    if rng.random() < 0.6:  # м'яка тінь в одному з кутів
        sx, sy = rng.choice([(0, 0), (w2, 0), (0, h2), (w2, h2)])
        d2 = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2) / max(w2, h2)
        light *= 1 - 0.22 * np.clip(1 - d2 / 0.55, 0, 1) ** 2
    warm = np.array([1.04, 1.0, 0.86]) * rng.uniform(0.92, 1.0)
    arr = arr * light[..., None] * warm
    grey = arr.mean(-1, keepdims=True)
    arr = grey + (arr - grey) * 0.85  # трохи «вигоріла» картинка
    arr += nrng.normal(0, 5, arr.shape) + nrng.normal(0, 3, arr.shape[:2])[..., None]
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    # якість телефонної камери: м'якість, пересвітлення різкості, стиснення
    out = out.resize((int(w2 * 0.64), int(h2 * 0.64)), Image.BILINEAR)
    out = out.filter(ImageFilter.GaussianBlur(rng.uniform(0.7, 1.1)))
    out = out.filter(ImageFilter.UnsharpMask(radius=2, percent=70, threshold=2))
    import io
    for q in (62, 55):
        buf = io.BytesIO()
        out.save(buf, "JPEG", quality=q)
        buf.seek(0)
        out = Image.open(buf).convert("RGB")
    return out
