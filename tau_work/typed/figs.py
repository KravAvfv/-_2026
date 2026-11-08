"""Рисунки до друкованих звітів ПЗ1–6 з ТАУ (варіант 8): структурні схеми й графіки (matplotlib).

Кожен рисунок малюється у фізичному розмірі сторінки (ширина W_CM см), шрифт 12 пт → у Word текст ≈ 12 пт;
PNG 300 dpi. Структурні схеми — власний мінімальний «конструктор» (блоки, суматори, стрілки, вузли).
"""
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle, Wedge  # noqa: E402

OUT = Path(__file__).resolve().parent / "fig"
W_CM = 16.5
CM = 1 / 2.54
FS = 12

plt.rcParams.update({
    "font.family": "Times New Roman", "font.size": FS,
    "mathtext.fontset": "custom", "mathtext.rm": "Times New Roman", "mathtext.it": "Times New Roman:italic",
    "mathtext.bf": "Times New Roman:bold", "mathtext.default": "it",
    "axes.linewidth": 0.8, "axes.labelsize": FS, "xtick.labelsize": FS - 1, "ytick.labelsize": FS - 1,
    "legend.fontsize": FS - 1, "legend.frameon": True, "legend.framealpha": 1, "legend.edgecolor": "0.3",
    "grid.color": "0.82", "grid.linewidth": 0.6, "axes.grid": True, "axes.axisbelow": True,
    "savefig.dpi": 300, "axes.formatter.use_locale": False,
})


def uk(v, d=1):
    """Число з десятковою комою і правильним мінусом."""
    s = f"{v:.{d}f}".replace(".", ",")
    return s.replace("-", "−")


def ukm(v, d=1):
    """Те саме для mathtext: кома в {,}, щоб не з'являвся пробіл."""
    return uk(v, d).replace(",", "{,}")


def comma_axis(ax, which="both", d=None):
    from matplotlib.ticker import FuncFormatter

    def fmt(v, _):
        if d is not None:
            return uk(v, d)
        s = f"{v:g}".replace(".", ",").replace("-", "−")
        return s
    if which in ("x", "both"):
        ax.xaxis.set_major_formatter(FuncFormatter(fmt))
    if which in ("y", "both"):
        ax.yaxis.set_major_formatter(FuncFormatter(fmt))


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{name}.png"
    fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.04, facecolor="white")
    plt.close(fig)
    return p


# ------------------------------------------------------------------ структурні схеми
class Scheme:
    """Координати — у сантиметрах сторінки (1 одиниця = 1 см), тож шрифт 12 пт лишається 12 пт у Word."""

    def __init__(self, w, h):
        self.fig = plt.figure(figsize=(w * CM, h * CM))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, w); self.ax.set_ylim(0, h)
        self.ax.set_aspect("equal"); self.ax.axis("off")

    def block(self, x, y, w, h, text, fs=FS + 1):
        """Блок з центром (x, y)."""
        self.ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fill=False, lw=1.1))
        self.ax.text(x, y, text, ha="center", va="center", fontsize=fs)
        return (x - w / 2, x + w / 2)

    def summer(self, x, y, r=0.32, minus=()):
        """Суматор: коло з хрестом; сектори з `minus` ('s','n','w','e') зафарбовані (від'ємний вхід)."""
        ang = {"e": (-45, 45), "n": (45, 135), "w": (135, 225), "s": (225, 315)}
        for side in minus:
            a, b = ang[side]
            self.ax.add_patch(Wedge((x, y), r, a, b, color="black", lw=0))
        self.ax.add_patch(Circle((x, y), r, fill=False, lw=1.1))
        d = r / math.sqrt(2)
        self.ax.plot([x - d, x + d], [y - d, y + d], color="black", lw=1.0)
        self.ax.plot([x - d, x + d], [y + d, y - d], color="black", lw=1.0)
        return r

    def arrow(self, pts, head=True):
        xs, ys = zip(*pts)
        if len(pts) > 2:
            self.ax.plot(xs[:-1], ys[:-1], color="black", lw=1.1, solid_capstyle="butt")
        a = FancyArrowPatch(pts[-2], pts[-1], arrowstyle="-|>" if head else "-", mutation_scale=12,
                            lw=1.1, color="black", shrinkA=0, shrinkB=0)
        self.ax.add_patch(a)

    def node(self, x, y):
        self.ax.add_patch(Circle((x, y), 0.07, color="black"))

    def text(self, x, y, s, ha="center", va="center", fs=FS + 1):
        self.ax.text(x, y, s, ha=ha, va=va, fontsize=fs)


def fig_link(name):
    s = Scheme(W_CM, 2.6)
    s.block(8.25, 1.3, 3.6, 1.5, "$W(p)$")
    s.arrow([(2.6, 1.3), (6.45, 1.3)])
    s.arrow([(10.05, 1.3), (13.9, 1.3)])
    s.text(4.5, 1.75, r"$x_1(t),\ X_1(p)$")
    s.text(12.0, 1.75, r"$x_2(t),\ X_2(p)$")
    s.text(4.5, 0.85, "вхід", fs=FS)
    s.text(12.0, 0.85, "вихід", fs=FS)
    return save(s.fig, name)


def fig_chain_p1(name):
    s = Scheme(W_CM, 2.6)
    y = 1.3
    s.text(0.75, y + 0.45, r"$X_1(p)$")
    s.arrow([(0.1, y), (1.9, y)])
    s.block(3.0, y, 2.2, 1.4, r"$\dfrac{1}{p}$")
    s.arrow([(4.1, y), (5.6, y)])
    s.block(6.9, y, 2.6, 1.4, r"$p+1$")
    s.arrow([(8.2, y), (9.7, y)])
    s.block(11.25, y, 3.1, 1.4, r"$\dfrac{1}{5p+1}$")
    s.arrow([(12.8, y), (15.6, y)])
    s.text(14.3, y + 0.45, r"$X_2(p)$")
    for x, t in ((3.0, "інтегруюча"), (6.9, "форсуюча"), (11.25, "аперіодична")):
        s.text(x, 0.2, t, fs=FS - 1)
    return save(s.fig, name)


def fig_pz_map(name, zeros, poles, xlim, ylim=(-1, 1), w_cm=W_CM, h_cm=6.0, labels=None):
    fig, ax = plt.subplots(figsize=(w_cm * CM, h_cm * CM))
    ax.axhline(0, color="black", lw=0.8); ax.axvline(0, color="black", lw=0.8)
    ax.plot(np.real(zeros), np.imag(zeros), "o", ms=9, mfc="white", mec="black", mew=1.4, label="нулі")
    ax.plot(np.real(poles), np.imag(poles), "x", ms=10, color="black", mew=1.8, label="полюси")
    ax.set_xlim(*xlim); ax.set_ylim(*ylim)
    ax.set_xlabel(r"$\mathrm{Re}\,p$"); ax.set_ylabel(r"$\mathrm{Im}\,p$")
    comma_axis(ax)
    for k, (z, lab) in enumerate((labels or {}).items()):
        ax.annotate(lab, (z, 0), textcoords="offset points", xytext=(0, 14 if k % 2 else -22), ha="center",
                    fontsize=FS - 1, bbox=dict(fc="white", ec="none", pad=0.5))
    ax.legend(loc="upper left")
    return save(fig, name)


# ------------------------------------------------------------------ ПЗ2
def fig_time(name, t, y, label, asym=None, asym_label=None, ylab="", marks=(), tau=None, ylim=None):
    fig, ax = plt.subplots(figsize=(W_CM * CM, 7.0 * CM))
    ax.plot(t, y, color="black", lw=1.8, label=label)
    if asym is not None:
        ax.plot(t, asym, "--", color="0.35", lw=1.2, label=asym_label)
    for (tx, ty) in marks:
        ax.plot(tx, ty, "o", ms=4.5, color="black")
    if tau:
        ax.axvline(tau, ls=":", color="0.4", lw=1.0)
    ax.set_xlim(t[0], t[-1])
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xlabel(r"$t$, с"); ax.set_ylabel(ylab)
    comma_axis(ax)
    ax.legend(loc="best")
    return save(fig, name)


# ------------------------------------------------------------------ ПЗ3
def fig_scheme_p3(name):
    s = Scheme(W_CM, 5.6)
    y, yb = 3.9, 2.25
    s.text(0.55, y + 0.45, r"$X(p)$")
    s.arrow([(0.1, y), (1.38, y)])
    s.summer(1.7, y, minus=("s",))
    s.text(2.55, y + 0.42, r"$\delta(p)$")
    s.arrow([(2.02, y), (4.18, y)])
    s.node(2.6, y)
    s.summer(4.5, y)
    s.arrow([(2.6, y), (2.6, yb), (3.0, yb)])
    s.block(3.55, yb, 1.1, 0.9, r"$T_2p$")
    s.arrow([(4.1, yb), (4.5, yb), (4.5, y - 0.32)])
    s.arrow([(4.82, y), (5.4, y)])
    s.block(7.55, y, 4.3, 1.45, r"$\dfrac{T_1p+1}{T_3^2p^2+2\zeta T_3p+1}$")
    s.arrow([(9.7, y), (10.6, y)])
    s.block(11.35, y, 1.5, 1.3, r"$\dfrac{k}{p}$")
    s.node(13.3, y)
    s.arrow([(12.1, y), (15.6, y)])
    s.text(14.6, y + 0.45, r"$Y(p)$")
    s.arrow([(13.3, y), (13.3, 0.6), (1.7, 0.6), (1.7, y - 0.32)])
    s.text(0.95, 3.05, r"$Y_{\mathrm{зз}}(p)$")
    for x, t in ((3.55, "$W_{1}'$"), (7.55, "$W_2$"), (11.35, "$W_3$")):
        pass
    s.text(3.55, 1.55, r"$W_{\mathrm{п}}(p)$", fs=FS)
    s.text(7.55, 4.95, r"$W_2(p)$", fs=FS)
    s.text(11.35, 4.95, r"$W_3(p)$", fs=FS)
    return save(s.fig, name)


def fig_series_p3(name):
    s = Scheme(W_CM, 4.4)
    y = 2.9
    s.text(0.55, y + 0.45, r"$X(p)$")
    s.arrow([(0.1, y), (1.38, y)])
    s.summer(1.7, y, minus=("s",))
    s.text(2.35, y + 0.42, r"$\delta(p)$")
    s.arrow([(2.02, y), (3.0, y)])
    s.block(3.9, y, 1.8, 1.0, r"$1+T_2p$")
    s.arrow([(4.8, y), (5.6, y)])
    s.block(7.75, y, 4.3, 1.45, r"$\dfrac{T_1p+1}{T_3^2p^2+2\zeta T_3p+1}$")
    s.arrow([(9.9, y), (10.7, y)])
    s.block(11.45, y, 1.5, 1.3, r"$\dfrac{k}{p}$")
    s.node(13.4, y)
    s.arrow([(12.2, y), (15.6, y)])
    s.text(14.6, y + 0.45, r"$Y(p)$")
    s.arrow([(13.4, y), (13.4, 0.5), (1.7, 0.5), (1.7, y - 0.32)])
    s.text(3.9, 1.95, r"$W_1(p)$", fs=FS)
    s.text(7.75, 1.8, r"$W_2(p)$", fs=FS)
    s.text(11.45, 1.85, r"$W_3(p)$", fs=FS)
    return save(s.fig, name)


def fig_loop(name, label=r"$W_{\mathrm{роз}}(p)$", inp=r"$X(p)$", out=r"$Y(p)$", err=r"$\delta(p)$"):
    s = Scheme(W_CM, 3.4)
    y = 2.25
    s.text(2.0, y + 0.45, inp)
    s.arrow([(1.4, y), (3.28, y)])
    s.summer(3.6, y, minus=("s",))
    s.text(4.45, y + 0.42, err)
    s.arrow([(3.92, y), (6.0, y)])
    s.block(7.8, y, 3.6, 1.2, label)
    s.node(11.4, y)
    s.arrow([(9.6, y), (13.6, y)])
    s.text(12.6, y + 0.45, out)
    s.arrow([(11.4, y), (11.4, 0.5), (3.6, 0.5), (3.6, y - 0.32)])
    return save(s.fig, name)


# ------------------------------------------------------------------ ПЗ4/5: логарифмічні характеристики
def fig_bode_mag(name, w, L_exact, L_asym, corners, wc=None, slopes=(), point=None, ylim=None, xlim=None,
                 h_cm=9.0, legend_loc="upper right"):
    fig, ax = plt.subplots(figsize=(W_CM * CM, h_cm * CM))
    ax.semilogx(w, L_asym, color="black", lw=2.0, label="асимптотична ЛАЧХ")
    ax.semilogx(w, L_exact, "--", color="0.35", lw=1.3, label="точна ЛАЧХ")
    ax.axhline(0, color="black", lw=0.9)
    for wi, lab in corners:
        ax.axvline(wi, ls=":", color="0.3", lw=1.0)
        ax.text(wi, ax.get_ylim()[0] if ylim is None else ylim[0], lab, ha="center", va="bottom",
                fontsize=FS, backgroundcolor="white")
    if wc:
        ax.plot(wc, 0, "o", ms=5, color="black")
        ax.annotate(r"$\omega_{\mathrm{зр}}$", (wc, 0), textcoords="offset points", xytext=(6, 6), fontsize=FS)
    for (wx, Lx, txt) in slopes:
        ax.text(wx, Lx, txt, fontsize=FS - 1, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="0.5", lw=0.6))
    if point:
        wx, Lx, txt = point
        ax.plot([wx, wx], [ylim[0] if ylim else 0, Lx], ":", color="black", lw=1.0)
        ax.plot([w[0], wx], [Lx, Lx], ":", color="black", lw=1.0)
        ax.plot(wx, Lx, "o", ms=5.5, color="black")
        ax.annotate(txt, (wx, Lx), textcoords="offset points", xytext=(8, 6), fontsize=FS)
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xlim(*(xlim or (w[0], w[-1])))
    ax.set_xlabel(r"$\omega$, с$^{-1}$"); ax.set_ylabel(r"$L(\omega)$, дБ")
    ax.grid(True, which="both")
    comma_axis(ax)
    ax.legend(loc=legend_loc)
    return save(fig, name)


def fig_bode_phase(name, w, parts, total, corners, wc=None, w180=None, ylim=None, h_cm=9.0):
    fig, ax = plt.subplots(figsize=(W_CM * CM, h_cm * CM))
    styles = [(0, (1, 1.5)), (0, (5, 2)), (0, (3, 1.5, 1, 1.5)), (0, (8, 2, 1, 2))]
    for (lab, y), ls in zip(parts, styles):
        ax.semilogx(w, y, ls=ls, color="0.4", lw=1.1, label=lab)
    ax.semilogx(w, total, color="black", lw=2.0, label=r"$\varphi(\omega)$ системи")
    ax.axhline(-180, color="black", lw=0.9)
    for wi, lab in corners:
        ax.axvline(wi, ls=":", color="0.3", lw=1.0)
    if wc:
        pc = np.interp(np.log10(wc), np.log10(w), total)
        ax.plot(wc, pc, "o", ms=5, color="black")
        ax.annotate(r"$\varphi(\omega_{\mathrm{зр}})$", (wc, pc), textcoords="offset points", xytext=(6, -16), fontsize=FS)
    if w180:
        ax.plot(w180, -180, "s", ms=5, color="black")
        ax.annotate(r"$\omega_{\pi}$", (w180, -180), textcoords="offset points", xytext=(-24, -18), fontsize=FS)
    if ylim:
        ax.set_ylim(*ylim)
    ax.set_xlim(w[0], w[-1])
    ax.set_xlabel(r"$\omega$, с$^{-1}$"); ax.set_ylabel(r"$\varphi(\omega)$, град")
    ax.grid(True, which="both")
    comma_axis(ax)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, frameon=False)
    return save(fig, name)


# ------------------------------------------------------------------ ПЗ5: сигнали
def fig_signals_p5(name, t, x, e_sim, e_ss):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(W_CM * CM, 10.5 * CM), sharex=True)
    a1.plot(t, x, color="black", lw=1.6, label=r"$x(t)=1{,}2\sin 0{,}5t$")
    a1.set_ylabel(r"$x(t)$")
    a1.legend(loc="upper right")
    a2.plot(t, e_sim, color="0.55", lw=1.2, label=r"$\delta(t)$ — моделювання замкненої системи")
    a2.plot(t, e_ss, "--", color="black", lw=1.5, label=r"$\delta_{\mathrm{уст}}(t)=0{,}125\sin(0{,}5t+68{,}2°)$")
    a2.set_ylabel(r"$\delta(t)$")
    a2.set_xlabel(r"$t$, с")
    a2.set_xlim(t[0], t[-1])
    a2.set_ylim(-0.3, 0.3)
    a2.legend(loc="upper right")
    comma_axis(a1); comma_axis(a2)
    fig.tight_layout(h_pad=0.6)
    return save(fig, name)


# ------------------------------------------------------------------ ПЗ6: годограф Михайлова
def fig_mikhailov(name, coeffs, wmax, mark_w):
    a3, a2, a1, a0 = coeffs
    w = np.linspace(0, wmax, 3000)
    U = a0 - a2 * w ** 2
    V = a1 * w - a3 * w ** 3
    fig, ax = plt.subplots(figsize=(W_CM * CM, 7.0 * CM))
    ax.plot(U, V, color="black", lw=1.8, label=r"$D(j\omega)=U(\omega)+jV(\omega)$")
    ax.axhline(0, color="black", lw=0.8); ax.axvline(0, color="black", lw=0.8)
    for wv, lab, off in mark_w:
        u, v_ = a0 - a2 * wv ** 2, a1 * wv - a3 * wv ** 3
        ax.plot(u, v_, "o", ms=5, color="black")
        ax.annotate(lab, (u, v_), textcoords="offset points", xytext=off, fontsize=FS - 1)
    k = int(len(w) * 0.55)
    ax.annotate("", xy=(U[k + 40], V[k + 40]), xytext=(U[k], V[k]),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2, mutation_scale=14))
    ax.text(-25, 8.4, r"$\omega$ зростає", fontsize=FS - 1, ha="center")
    for x, y, s in ((8, 9.5, "I"), (-90, 9.5, "II"), (-90, -9.5, "III"), (8, -9.5, "IV")):
        ax.text(x, y, s, fontsize=FS, ha="center", va="center", color="0.4")
    ax.set_xlim(-100, 18); ax.set_ylim(-12, 12)
    ax.set_xlabel(r"$U(\omega)$"); ax.set_ylabel(r"$V(\omega)$")
    comma_axis(ax)
    ax.legend(loc="lower left")
    return save(fig, name)


def fig_roots(name, coeffs):
    r = np.roots(coeffs)
    fig, ax = plt.subplots(figsize=(W_CM * CM, 5.5 * CM))
    ax.axhline(0, color="black", lw=0.8); ax.axvline(0, color="black", lw=0.8)
    ax.plot(r.real, r.imag, "x", ms=10, mew=1.8, color="black")
    for z in r:
        lab = (f"$p_1={ukm(z.real, 2)}$" if abs(z.imag) < 1e-9 else
               f"$p_{{{2 if z.imag > 0 else 3}}}={ukm(z.real, 2)}{'+' if z.imag > 0 else '-'}j{ukm(abs(z.imag), 2)}$")
        ax.annotate(lab, (z.real, z.imag), textcoords="offset points",
                    xytext=(-10, 8) if z.imag >= 0 else (-10, -18), fontsize=FS - 1, ha="right",
                    bbox=dict(fc="white", ec="none", pad=0.5))
    ax.fill_betweenx([-8, 8], -60, 0, color="0.93", zorder=0)
    ax.text(-36, 5.8, "ліва півплощина (область стійкості)", fontsize=FS - 1, ha="center", color="0.3")
    ax.set_xlim(-58, 8); ax.set_ylim(-8, 8)
    ax.set_xlabel(r"$\mathrm{Re}\,p$"); ax.set_ylabel(r"$\mathrm{Im}\,p$")
    comma_axis(ax)
    return save(fig, name)


def fig_step_cl(name, t, y, title_label):
    fig, ax = plt.subplots(figsize=(W_CM * CM, 6.5 * CM))
    ax.plot(t, y, color="black", lw=1.6, label=title_label)
    ax.axhline(1, ls="--", color="0.4", lw=1.0, label="задане значення $x=1$")
    ax.set_xlim(t[0], t[-1])
    ax.set_xlabel(r"$t$, с"); ax.set_ylabel(r"$y(t)$")
    comma_axis(ax)
    ax.legend(loc="upper left")
    return save(fig, name)


def fig_hurwitz_k(name, kk, d2, kgr, k0):
    fig, ax = plt.subplots(figsize=(W_CM * CM, 6.5 * CM))
    ax.plot(kk, d2, color="black", lw=1.8, label=r"$\Delta_2(k)=a_2a_1-(1+k)a_3$")
    ax.axhline(0, color="black", lw=0.9)
    ax.axvline(kgr, ls="--", color="0.35", lw=1.1)
    ax.plot(k0, np.interp(k0, kk, d2), "o", ms=5, color="black")
    ax.annotate(r"$k=10$, $\Delta_2=0{,}6956$", (k0, np.interp(k0, kk, d2)), textcoords="offset points",
                xytext=(8, 4), fontsize=FS - 1)
    ax.annotate(r"$k_{\mathrm{гр}}\approx 79{,}6$", (kgr, 0), textcoords="offset points", xytext=(6, 14), fontsize=FS - 1)
    ax.fill_between(kk, d2, 0, where=d2 > 0, color="0.88", label="область стійкості")
    ax.set_xlim(kk[0], kk[-1])
    ax.set_xlabel(r"$k$"); ax.set_ylabel(r"$\Delta_2$")
    comma_axis(ax)
    ax.legend(loc="upper right")
    return save(fig, name)
