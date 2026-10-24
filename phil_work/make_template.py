"""Філософія: ПОРОЖНІЙ шаблон читацького щоденника за пам'яткою викладача (тема семінару → першоджерело →
питання / цитати / відповіді та власні розмисли). Рукописні лише заголовки; зміст студент пише сам
(викладач: «LLM не користуємося!»). Аркуші — рівні, для друку (без ефекту фото)."""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tau_work"))
from hand import Hand, paper, LEFT, RIGHT, BOTTOM, CELL, SIZE  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "Філософія" / "Шаблон читацького щоденника"

# назви семінарів скорочено за планом на сайті викладача
SEMINARS = [
    "Вступ до філософії",
    "Онтологія та метафізика античних філософів. Перші теорії буття",
    "Етика та політика античних філософів: Платон, Аристотель, стоїки, епікурейці",
    "Гносеологія пізньоантичних і середньовічних філософів: Августин, Боецій, Аквінат",
    "Ідея університету. Суперечка про універсалії. Мак'явеллі",
    "Теорія пізнання: Бейкон, Декарт, Г'юм, Кант",
    "Етика Канта та утилітаризм Бентама й Міля",
    "Суспільний договір: Гоббс, Лок, Руссо. Геґель, Маркс, Роулз",
    "Шопенгауер, Ніцше, екзистенціалізм Сартра й де Бовуар",
    "Філософія мови та свідомості. Слабкий і сильний ШІ",
    "Філософська антропологія та філософія техніки",
]
SPARE = 3  # чисті аркуші-продовження з тими самими колонками
COLS = ["Питання", "Цитати", "Відповіді та|власні розмисли"]


def columns(h, top):
    """Три колонки пам'ятки від `top` до низу аркуша."""
    w = (RIGHT - LEFT) / 3
    xs = [LEFT + w * i for i in range(4)]
    for i, name in enumerate(COLS):
        lines = name.split("|")
        for k, ln in enumerate(lines):
            h.label_c(ln, xs[i] + w / 2, top + 44 + k * 44, 42)
    head = top + 44 * len(COLS[2].split("|")) + 14
    h.line((LEFT - 6, head), (RIGHT + 6, head), 4)
    for x in xs[1:3]:
        h.line((x, top), (x, BOTTOM - 10), 4, bow=1.0)


def seminar_page(h, n, title):
    h.new_page()
    h.heading(f"Семінар {n}", center=True)
    h.para(f"Тема: {title}", indent=0, size=SIZE - 10)
    h.gap()
    h.text_line([("txt", "Першоджерело: ")], LEFT, SIZE - 8)
    y = h.y - CELL * 0.6
    h.line((LEFT + 330, y), (RIGHT, y), 3)
    h.line((LEFT, y + CELL * 1.6), (RIGHT, y + CELL * 1.6), 3)
    columns(h, y + CELL * 2.4)


def spare_page(h):
    h.new_page()
    h.text_line([("txt", "Семінар №      (продовження)")], LEFT, SIZE - 8)
    columns(h, h.y)


def title_page(h):
    h.gap(3)
    h.heading("Читацький щоденник", center=True, size=SIZE + 14)
    h.text_line([("txt", "з філософії")], LEFT, SIZE, center=True)
    h.gap(2)
    h.text_line([("txt", "Кравченко Петро, ІР-31")], LEFT, SIZE - 6, center=True)
    h.gap(4)
    h.text_line([("txt", "Модель запису (за пам'яткою):")], LEFT, SIZE - 8, underline=True)
    h.gap()
    y = h.y
    boxes = [("тема семінару", LEFT + 10), ("першоджерело", LEFT + 370), ("власна думка", LEFT + 730)]
    for txt, x in boxes:
        h.box(x, y, 320, 90)
        h.label_c(txt, x + 160, y + 58, 40)
    for a, b in ((LEFT + 330, LEFT + 370), (LEFT + 690, LEFT + 730)):
        h.arrow((a, y + 45), (b, y + 45))
    y += 150
    for k, txt in enumerate(["• питання", "• цитати", "• відповіді та власні розмисли"]):
        h.label(txt, LEFT + 380, y + k * 60, 42)
    h.y = y + 4 * 60
    h.gap(2)
    h.para("Записую відповіді на практичні завдання кожного семінару (не теоретичний блок).",
           indent=0, size=SIZE - 14)


def flat(ink):
    """Синя ручка на рівному аркуші в клітинку — для друку."""
    page = np.asarray(paper()).astype(np.float32)
    a = np.asarray(ink.filter(ImageFilter.GaussianBlur(0.8))).astype(np.float32)[..., None] / 255.0
    pen = np.array([40, 48, 168], np.float32)
    page = page * (1 - a * 0.9) + pen * a * 0.9
    return Image.fromarray(np.clip(page, 0, 255).astype(np.uint8))


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    h = Hand(seed=1462)
    title_page(h)
    for n, t in enumerate(SEMINARS, 1):
        seminar_page(h, n, t)
    for _ in range(SPARE):
        spare_page(h)
    imgs = [flat(p) for p in h.pages]
    for old in OUT.glob("стор*.png"):
        old.unlink()
    for i, img in enumerate(imgs, 1):
        img.save(OUT / f"стор{i:02d}.png")
    imgs[0].save(OUT / "Шаблон_читацького_щоденника.pdf", save_all=True, append_images=imgs[1:], resolution=150)
    print(f"{len(imgs)} стор. → {OUT}")
