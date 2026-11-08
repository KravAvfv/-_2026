"""Філософія: той самий конспект для самопідготовки (phil_work/make_study_guide.py), але суцільним текстом
рукописним почерком ТАУ (tau_work/hand.py) на рівних аркушах у клітинку — для зручного читання.
Run:  .venv/bin/python phil_work/make_study_guide_hand.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent / "tau_work"), str(HERE)]
from hand import Hand, LEFT, SIZE  # noqa: E402
from make_study_guide import CORRECTIONS, SEMINARS  # noqa: E402
from make_template import flat  # noqa: E402

OUT = HERE.parent / "Філософія" / "Навчальні матеріали" / "Рукописний_конспект_семінари_1-7"
T = SIZE - 16          # основний текст (дрібніший за ТАУ, щоб аркуш вміщав більше)


def esc(s):
    """Екранувати символи розмітки hand.py ({ } ^ _ ~ #)."""
    return re.sub(r"([{}^_~#\\])", r"\\\1", s)


def main():
    h = Hand(seed=2026)
    h.heading("Конспект з філософії", center=True, size=SIZE)
    h.text_line([("txt", "для самопідготовки · семінари 1–7")], LEFT, T, center=True)
    h.gap()
    for num, theme, sources, rows in SEMINARS:
        h.heading(esc(num), size=T + 8)
        h.para(esc(theme), indent=0, size=T + 4)
        h.para(esc(f"Першоджерела: {sources}"), indent=0, size=T - 4)
        h.gap(0.5)
        for q, theses, think in rows:
            h.text_line([("txt", esc(q))], LEFT, T + 2, underline=True) if len(q) < 55 else \
                h.para(esc(q), indent=0, size=T + 2)
            for t in theses:
                h.para(esc("– " + t.replace("Доповнено. ", "(доп.) ")), indent=0, size=T)
            for t in think:
                h.para(esc("→ Подумати: " + t), indent=1, size=T)
            h.gap(0.5)
        h.gap()
    h.heading("Що виправлено в конспекті", size=T + 6)
    for a, b in CORRECTIONS:
        h.para(esc(f"Було: {a}"), indent=0, size=T)
        h.para(esc(f"Насправді: {b}"), indent=1, size=T)
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    imgs = [flat(p) for p in h.pages]
    for i, img in enumerate(imgs, 1):
        img.save(OUT / f"стор{i:02d}.png")
    imgs[0].save(OUT.parent / "Рукописний_конспект_семінари_1-7.pdf", save_all=True, append_images=imgs[1:],
                 resolution=150)
    print(f"{len(imgs)} стор.")


if __name__ == "__main__":
    main()
