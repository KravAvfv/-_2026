#!/usr/bin/env python3
"""Презентація до захисту курсової роботи з ПІС (вимога методичних вказівок, розд. 5.2–5.3: «робота в текстовому
форматі та презентація до роботи завантажується студентом»; 10–16 слайдів, доповідь до 7 хв).

Слайди будуються з тих самих рисунків, що й пояснювальна записка (coursework_final/diagrams), а числа — з моделі
(cw_model, lab1) і demo.json прототипу, тому презентація не розходиться із запискою.
Run:  .venv/bin/python coursework_final/make_presentation.py   (+ tools/office2pdf.sh для PDF-перегляду)
"""
import json
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

D = json.loads((HERE / "app" / "demo.json").read_text(encoding="utf-8"))
DIAG = HERE / "diagrams"
OUT = HERE / "КР_Кравченко_ІР-31_презентація.pptx"

INK = RGBColor(0x1B, 0x26, 0x33)      # графіт — домінантний (титул, висновки, заголовки)
STEEL = RGBColor(0x4A, 0x5B, 0x6C)    # допоміжний текст
AMBER = RGBColor(0xE0, 0x8E, 0x1B)    # акцент «тривоги / радара»
MIST = RGBColor(0xEE, 0xF1, 0xF4)     # тло карток
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Arial"
W, H = Inches(13.333), Inches(7.5)
M = Inches(0.6)

prs = Presentation()
prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]
N_SLIDES = 16


def tb(slide, x, y, w, h, parts, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
       name=None):
    """parts: рядок або список абзаців; абзац — рядок або список (текст, {bold, color, size})."""
    box = slide.shapes.add_textbox(x, y, w, h)
    if name:
        box.name = name
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    paras = parts if isinstance(parts, list) else [parts]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(6)
        runs = para if isinstance(para, list) else [(para, {})]
        for text, o in runs:
            r = p.add_run()
            r.text = text
            r.font.name = FONT
            r.font.size = Pt(o.get("size", size))
            r.font.bold = o.get("bold", bold)
            r.font.color.rgb = o.get("color", color)
    return box


def card(slide, x, y, w, h, fill=MIST):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    s.adjustments[0] = 0.08
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    return s


def badge(slide, x, y, text, d=Inches(0.62)):
    """Мотив презентації: номер у колі кольору «тривоги»."""
    c = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, d, d)
    c.fill.solid()
    c.fill.fore_color.rgb = AMBER
    c.line.fill.background()
    tf = c.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.name, r.font.size, r.font.bold, r.font.color.rgb = FONT, Pt(16), True, WHITE
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE


def picture(slide, path, x, y, w, h):
    """Рисунок у рамці (x, y, w, h) зі збереженням пропорцій, по центру рамки."""
    iw, ih = Image.open(path).size
    k = min(w / iw, h / ih)
    pw, ph = int(iw * k), int(ih * k)
    pic = slide.shapes.add_picture(str(path), x + (w - pw) // 2, y + (h - ph) // 2, pw, ph)
    pic.name = path.stem
    return pic


def content(title, notes, num):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = WHITE
    tb(s, M, Inches(0.42), W - 2 * M - Inches(1.0), Inches(0.8), title, size=30, bold=True, name="Заголовок")
    tb(s, W - M - Inches(0.9), H - Inches(0.55), Inches(0.9), Inches(0.3), f"{num} / {N_SLIDES}", size=11,
       color=STEEL, align=PP_ALIGN.RIGHT, name="Номер слайда")
    s.notes_slide.notes_text_frame.text = notes
    return s


def dark(notes):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = INK
    s.notes_slide.notes_text_frame.text = notes
    return s


def stat(slide, x, y, w, big, label, color=INK, lab=STEEL):
    tb(slide, x, y, w, Inches(0.9), big, size=40, bold=True, color=color)
    tb(slide, x, y + Inches(0.95), w, Inches(0.8), label, size=14, color=lab)


TOP = Inches(1.45)                    # верх області вмісту
BODY_H = H - TOP - Inches(0.75)

# 1 ------------------------------------------------------------------ титул
s = dark("Добрий день. Тема курсової роботи — проєктування розподіленої IoT-системи обміну телеметрією та "
         "координації дронів-перехоплювачів. Об’єкт — умовний регіональний центр протидронової оборони.")
tb(s, M, Inches(0.7), Inches(9), Inches(0.4), "Курсова робота з дисципліни «Проєктування інформаційних систем»",
   size=16, color=RGBColor(0xC9, 0xD2, 0xDB))
tb(s, M, Inches(1.5), Inches(10.5), Inches(2.6),
   "Проєктування розподіленої IoT-системи обміну телеметрією та координації дронів-перехоплювачів",
   size=38, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
tb(s, M, Inches(4.5), Inches(8), Inches(1.6), [
    [("Виконав: ", {"color": RGBColor(0xC9, 0xD2, 0xDB)}), ("Кравченко Петро Олександрович, гр. ІР-31", {"color": WHITE})],
    [("Керівник: ", {"color": RGBColor(0xC9, 0xD2, 0xDB)}), ("к.т.н., доцент Борисенко Ірина", {"color": WHITE})],
], size=18)
tb(s, M, H - Inches(1.0), Inches(9), Inches(0.4),
   "КНУ імені Тараса Шевченка · Факультет інформаційних технологій · Київ, 2026", size=14,
   color=RGBColor(0xC9, 0xD2, 0xDB))
ring = s.shapes.add_shape(MSO_SHAPE.DONUT, Inches(10.4), Inches(3.9), Inches(2.6), Inches(2.6))
ring.adjustments[0] = 0.08
ring.fill.solid()
ring.fill.fore_color.rgb = AMBER
ring.line.fill.background()
dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(11.55), Inches(5.05), Inches(0.3), Inches(0.3))
dot.fill.solid()
dot.fill.fore_color.rgb = AMBER
dot.line.fill.background()

# 2 ------------------------------------------------------------------ актуальність
s = content("Актуальність теми",
            "За даними Defense News, у 2025 році в Україні вироблено 100 тисяч дронів-перехоплювачів по 3–5 тисяч "
            "доларів, тоді як ракета Patriot коштує понад 3 мільйони. У лютому 2026 року на перехоплювачі "
            "припадало понад 70 % збитих над Києвом Shahed, а головним обмеженням названо сенсори. Отже, потрібна "
            "система, яка зводить дані сенсорів і координує розрахунки.", 2)
cols = [("100 тис.", "дронів-перехоплювачів вироблено в Україні у 2025 р."),
        ("3–5 тис. $", "вартість перехоплювача проти > 3 млн $ за ракету Patriot"),
        ("> 70 %", "збитих над Києвом Shahed у лютому 2026 р. — на рахунку перехоплювачів")]
cw = (W - 2 * M - 2 * Inches(0.4)) / 3
for i, (big, lab) in enumerate(cols):
    x = M + i * (cw + Inches(0.4))
    card(s, x, TOP + Inches(0.2), cw, Inches(2.6))
    stat(s, x + Inches(0.35), TOP + Inches(0.55), cw - Inches(0.7), big, lab, color=AMBER if i == 2 else INK)
tb(s, M, TOP + Inches(3.25), W - 2 * M, Inches(1.4), [
    [("Головне обмеження — сенсори. ", {"bold": True}),
     ("Масове застосування перехоплювачів потребує інформаційної системи, яка в реальному часі зводить дані "
      "розподіленої мережі сенсорів, допомагає обрати розрахунок і залишає рішення на пуск за людиною.", {})]],
   size=18)
tb(s, M, H - Inches(0.6), Inches(9), Inches(0.3), "Джерело: K. Livingstone, Defense News, 05.03.2026.", size=11,
   color=STEEL)

# 3 ------------------------------------------------------------------ мета і завдання
s = content("Мета і завдання роботи",
            "Мета — розробити проєкт системи, що забезпечує безпеку повітряного простору на території, яку вона "
            "покриває. Сім завдань узято з методичних вказівок: від аналізу предметної області до прототипу.", 3)
tb(s, M, TOP, Inches(5.0), Inches(4.6), [
    [("Мета", {"bold": True, "size": 22})],
    "Розробити проєкт розподіленої IoT-системи обміну телеметрією та координації дронів-перехоплювачів, яка "
    "забезпечує безпеку повітряного простору на території, що її покриває система.",
    [("Об’єкт: ", {"bold": True}), ("діяльність умовного РЦПДО «Щит-Північ» з виявлення, супроводу й перехоплення "
                                     "повітряних цілей.", {})],
    [("Предмет: ", {"bold": True}), ("процеси збору й злиття телеметрії та координації розрахунків.", {})],
], size=16)
tasks = ["Дослідити предметну область і діяльність центру", "Визначити проблеми та процеси для автоматизації",
         "Побудувати дерево цілей і WBS", "Виконати функціональне моделювання в BPMN",
         "Виконати об’єктно-орієнтоване проєктування в UML", "Спроєктувати архітектуру, ролі та взаємодію",
         "Розробити прототип для всіх категорій користувачів"]
for i, t in enumerate(tasks):
    y = TOP + i * Inches(0.74)
    badge(s, Inches(6.3), y, str(i + 1), d=Inches(0.52))
    tb(s, Inches(7.05), y + Inches(0.06), Inches(5.7), Inches(0.5), t, size=16, anchor=MSO_ANCHOR.MIDDLE)

# 4 ------------------------------------------------------------------ об’єкт
s = content("Об’єкт дослідження — РЦПДО «Щит-Північ»",
            "Центр прикриває 3 райони, близько 9 тисяч квадратних кілометрів і 14 об’єктів критичної "
            "інфраструктури. Структура лінійно-функціональна. Досліджуваний підрозділ — командний пункт: через "
            "нього проходять усі потоки бойового управління.", 4)
picture(s, DIAG / "01_org_structure.png", Inches(6.6), TOP - Inches(0.15), Inches(6.1), BODY_H + Inches(0.2))
facts = [("3 райони · ≈ 9 000 км²", "14 об’єктів критичної інфраструктури, ≈ 160 осіб, цілодобово"),
         ("120 · 4 · 12", "акустичних сенсорів · РЛС · оптико-електронних постів"),
         ("18 розрахунків", "дронів-перехоплювачів на 9 позиціях"),
         ("Командний пункт", "досліджуваний підрозділ — через нього йдуть усі потоки бойового управління")]
for i, (a, b) in enumerate(facts):
    y = TOP + i * Inches(1.28)
    card(s, M, y, Inches(5.6), Inches(1.12))
    tb(s, M + Inches(0.3), y + Inches(0.14), Inches(5.0), Inches(0.45), a, size=20, bold=True)
    tb(s, M + Inches(0.3), y + Inches(0.6), Inches(5.0), Inches(0.45), b, size=14, color=STEEL)

# 5 ------------------------------------------------------------------ проблеми і вимоги
s = content("Проблеми та вимоги до системи",
            "Аналіз виявив сім проблем: різні канали виявлень, голосове цілевказання із затримкою до 90 секунд, "
            "немає даних про готовність тощо. З них виведено 22 функціональні вимоги, 14 — високого пріоритету.", 5)
probs = ["П1  Виявлення надходять різними каналами → дублікати треків",
         "П2  Голосове цілевказання → затримка 30–90 с",
         "П3  Немає даних про готовність розрахунків",
         "П4  Телеметрія не зберігається централізовано",
         "П5  Ризик ураження дружньої авіації",
         "П6  Подавлення каналів засобами РЕБ",
         "П7  Паперовий облік результатів і витрати"]
tb(s, M, TOP, Inches(7.3), Inches(5), probs, size=17)
card(s, Inches(8.4), TOP, Inches(4.33), Inches(4.9), fill=INK)
stat(s, Inches(8.8), TOP + Inches(0.4), Inches(3.6), "22", "функціональні вимоги «Система повинна…»",
     color=WHITE, lab=RGBColor(0xC9, 0xD2, 0xDB))
stat(s, Inches(8.8), TOP + Inches(1.95), Inches(3.6), "14", "з них — високого пріоритету", color=AMBER,
     lab=RGBColor(0xC9, 0xD2, 0xDB))
stat(s, Inches(8.8), TOP + Inches(3.5), Inches(3.6), "13", "ролей користувачів + машинні актори",
     color=WHITE, lab=RGBColor(0xC9, 0xD2, 0xDB))

# 6 ------------------------------------------------------------------ дерево цілей
n1, n2, n3 = 5, 15, 30                 # як у записці (рисунок 1.2), дерево з ЛР1
s = content("Дерево цілей: від генеральної мети до заходів",
            f"Генеральна мета — безпека повітряного простору території. Метод — дезагрегація цілей: {n1} цілей "
            f"першого рівня, {n2} — другого і {n3} заходів; пунктиром позначено альтернативи «або».", 6)
picture(s, DIAG / "04_goal_tree.png", Inches(4.9), TOP - Inches(0.2), Inches(7.8), BODY_H + Inches(0.25))
tb(s, M, TOP, Inches(4.0), Inches(4.8), [
    [("Метод дезагрегації", {"bold": True, "size": 20})],
    "«і/або»-дерево: суцільна рамка — обов’язковий захід, пунктирна — альтернатива «а»/«б».",
    [(f"1 · {n1} · {n2} · {n3}", {"bold": True, "size": 26, "color": AMBER})],
    "генеральна мета · цілі 1-го рівня · цілі 2-го рівня · заходи",
    "Критерії: призначення ≤ 30 с, доставка завдання ≤ 1 с, 100 % пусків із санкцією другої особи.",
], size=16)

# 7 ------------------------------------------------------------------ WBS
s = content("Робоча структура проєкту (WBS)",
            "WBS має чотири рівні: проєкт, 8 субпроєктів, 20 блоків і 42 робочі пакети. Бюджет 29 330 тисяч "
            "гривень отримано сумуванням вартості пакетів знизу догори.", 7)
picture(s, DIAG / "05_wbs.png", M, TOP - Inches(0.1), Inches(8.6), BODY_H + Inches(0.15))
for i, (big, lab) in enumerate([("8", "субпроєктів"), ("20", "блоків робіт"), ("42", "робочі пакети"),
                                ("29 330", "тис. грн — бюджет (зворотні обчислення)")]):
    y = TOP + i * Inches(1.25)
    tb(s, Inches(9.6), y, Inches(3.2), Inches(0.6), big, size=32, bold=True, color=AMBER if i == 3 else INK)
    tb(s, Inches(9.6), y + Inches(0.62), Inches(3.2), Inches(0.5), lab, size=14, color=STEEL)

# 8 ------------------------------------------------------------------ BPMN карта
s = content("BPMN: п’ять пулів-функцій і зовнішні учасники",
            "Діяльність центру подано п’ятьма пулами-функціями; зовнішні учасники — згорнуті пули. Потоки "
            "повідомлень показують, що передається між функціями: виявлення, ціль, завдання, доповіді.", 8)
picture(s, DIAG / "bpmn_00_interaction_map.png", M, TOP, W - 2 * M, Inches(4.0))
tb(s, M, TOP + Inches(4.3), W - 2 * M, Inches(1.0),
   "P1 моніторинг обстановки · P2 призначення цілі та санкціонування пуску · P3 виконання місії · "
   "P4 оцінка результату · P5 готовність ресурсів", size=16, color=STEEL)

# 9 ------------------------------------------------------------------ BPMN P2
s = content("Призначення цілі за правилом двох осіб",
            "Пул P2: перевірка зон заборони та планів польотів, вибір розрахунку офіцером бойового управління, "
            "санкція оперативного чергового. Пропонує одна особа, санкціонує інша.", 9)
picture(s, DIAG / "bpmn_02_p2_assignment_a.png", M, TOP, W - 2 * M, Inches(4.1))
tb(s, M, TOP + Inches(4.35), W - 2 * M, Inches(1.0), [
    [("Правило двох осіб: ", {"bold": True}),
     ("місію пропонує ОБУ, а санкціонує ОЧ, який не є її автором; у БД — обмеження CHECK approved_by ≠ "
      "proposed_by.", {})]], size=16)

# 10 ----------------------------------------------------------------- UML прецеденти
s = content("UML: варіанти використання бойового управління",
            "Прецеденти UC1–UC12. Запропонувати місію завжди включає підбір розрахунку — це include; "
            "перепризначення розширює санкціонування лише при відмові — це extend.", 10)
picture(s, DIAG / "20_uc_combat.png", M, TOP - Inches(0.1), Inches(8.4), BODY_H + Inches(0.15))
tb(s, Inches(9.4), TOP, Inches(3.4), Inches(4.8), [
    [("include", {"bold": True, "color": AMBER, "size": 20})],
    "UC3 «Запропонувати місію» завжди виконує UC4 «Підібрати розрахунок».",
    [("extend", {"bold": True, "color": AMBER, "size": 20})],
    "UC12 розширює UC5 лише за умови «відмова» розрахунку.",
    "Права ролей на прецеденти — у матриці доступу (розділ 3.6).",
], size=16)

# 11 ----------------------------------------------------------------- UML діяльність і класи
s = content("UML: життєвий цикл місії та діаграма класів",
            "Діаграма діяльності охоплює всі 8 допустимих переходів стану місії. Діаграма класів подає 10 класів "
            "з 20 таблиць; дві асоціації «запропонував» і «санкціонував» — це правило двох осіб.", 11)
half = (W - 2 * M - Inches(0.4)) / 2
picture(s, DIAG / "22_activity.png", M, TOP - Inches(0.1), half, BODY_H - Inches(0.35))
picture(s, DIAG / "24_class_all.png", M + half + Inches(0.4), TOP - Inches(0.1), half, BODY_H - Inches(0.35))
tb(s, M, H - Inches(1.05), half, Inches(0.4), "Діяльність: 8 переходів mission_transition", size=14,
   color=STEEL, align=PP_ALIGN.CENTER)
tb(s, M + half + Inches(0.4), H - Inches(1.05), half, Inches(0.4), "Класи: 10 класів, композиція «Місія — Подія»",
   size=14, color=STEEL, align=PP_ALIGN.CENTER)

# 12 ----------------------------------------------------------------- архітектура
s = content("Архітектура: клієнт-сервер з периферією",
            "Система — інтерактивна супервізорного управління: оператор видає цілевказівки, автоматика виконує. "
            "Ядро в основному й резервному ЦОД — трирівневе, позиції обслуговують периферійні шлюзи. Компоненти з "
            "позначкою «прототип» реалізовано.", 12)
picture(s, DIAG / "31_components.png", Inches(4.9), TOP - Inches(0.1), Inches(7.8), BODY_H + Inches(0.15))
tb(s, M, TOP, Inches(4.0), Inches(4.9), [
    [("Чому так", {"bold": True, "size": 20})],
    "Файл-сервер — без контролю прав; «товсті» клієнти — логіка розпорошена; мікросервіси для ядра — "
    "складні в експлуатації.",
    [("Прототип", {"bold": True, "size": 20})],
    "браузер — Flask 3.1.1 — PostgreSQL 18.6; правила виконують функції й тригери СКБД.",
], size=16)

# 13 ----------------------------------------------------------------- розгортання і мережа
s = content("Розгортання та мережева взаємодія",
            "Два ЦОД з реплікацією, 9 периферійних шлюзів, АРМ і планшети. Протоколи: MQTT 5 для сенсорів, "
            "ASTERIX для РЛС, MAVLink 2 для перехоплювачів, HTTPS і WebSocket для застосунків.", 13)
picture(s, DIAG / "32_deployment.png", M, TOP - Inches(0.1), W - 2 * M, Inches(2.45))
picture(s, DIAG / "33_network.png", M, TOP + Inches(2.5), Inches(6.6), Inches(2.85))
tb(s, Inches(7.6), TOP + Inches(2.7), Inches(5.1), Inches(2.6), [
    [("MQTT 5", {"bold": True}), (" — акустичні сенсори", {})],
    [("ASTERIX", {"bold": True}), (" — РЛС", {})],
    [("MAVLink 2", {"bold": True}), (" — перехоплювачі", {})],
    [("HTTPS, WebSocket", {"bold": True}), (" — застосунки", {})],
    [("WireGuard", {"bold": True}), (" поверх меш-радіо, LTE чи супутника — магістраль", {})],
], size=16)

# 14 ----------------------------------------------------------------- ролі та безпека
s = content("Ролі, права доступу і захист правил",
            "13 ролей і 21 право; адміністратор не має бойових прав, офіцер кібербезпеки читає журнал, але не "
            "змінює його. Правила виконуються тригерами СКБД, тому їх неможливо обійти навіть прямим SQL.", 14)
picture(s, DIAG / "34_interaction.png", Inches(8.5), TOP - Inches(0.15), Inches(4.2), BODY_H + Inches(0.2))
rows = [("13 ролей · 21 право", "RBAC: людські ролі й машинні сутності; бойові права — лише R-01, R-02, R-04, R-05"),
        ("Тригери СКБД", "допустимі переходи, «лише свій розрахунок», заборона санкції автором"),
        ("Журнал аудиту", "ланцюжок хешів SHA-256; змінювати й видаляти записи заборонено"),
        ("Вхід і сеанс", "хеш паролю scrypt, CSRF-маркер, блокування після 5 спроб, тайм-аут 15 хв")]
for i, (a, b) in enumerate(rows):
    y = TOP + i * Inches(1.25)
    badge(s, M, y + Inches(0.15), str(i + 1))
    tb(s, M + Inches(0.85), y + Inches(0.05), Inches(6.8), Inches(0.45), a, size=19, bold=True)
    tb(s, M + Inches(0.85), y + Inches(0.52), Inches(6.8), Inches(0.6), b, size=14, color=STEEL)

# 15 ----------------------------------------------------------------- прототип
s = content("Прототип: працюючий застосунок для всіх ролей",
            "Прототип — працюючий веб-застосунок над PostgreSQL. Ліворуч — повітряна обстановка з мнемосхемою і "
            "чергою загроз, праворуч — картка місії командира розрахунку. Екрани зроблено з працюючого "
            "застосунку.", 15)
half = (W - 2 * M - Inches(0.4)) / 2
picture(s, DIAG / "screens" / "s03_situation.png", M, TOP - Inches(0.1), half, BODY_H - Inches(0.35))
picture(s, DIAG / "screens" / "s08_launched.png", M + half + Inches(0.4), TOP - Inches(0.1), half,
        BODY_H - Inches(0.35))
tb(s, M, H - Inches(1.05), half, Inches(0.4), "Повітряна обстановка: мнемосхема і черга загроз", size=14,
   color=STEEL, align=PP_ALIGN.CENTER)
tb(s, M + half + Inches(0.4), H - Inches(1.05), half, Inches(0.4), "Картка місії під час виконання (R-04)", size=14,
   color=STEEL, align=PP_ALIGN.CENTER)

# 16 ----------------------------------------------------------------- результати
import re  # noqa: E402
tests = int(re.match(r"(\d+) passed", D["pytest"]["summary"]).group(1))   # з прогону run_demo.py
s = dark("Підсумок: пройдено всі етапи — від аналізу до працюючого прототипу. Ядро бізнес-правил працює і "
         "перевірене тестами. Напрями розвитку — периферійні шлюзи з адаптерами, деконфлікція, доставка завдань на "
         "планшет. Дякую за увагу.")
tb(s, M, Inches(0.5), W - 2 * M, Inches(0.8), "Результати та напрями розвитку", size=34, bold=True, color=WHITE)
for i, (big, lab) in enumerate([("20", "таблиць БД"), ("22 · 16", "функції · тригери"), ("27", "маршрутів застосунку"),
                                (str(tests), {1: "автоматизований тест — успішно", 2: "автоматизовані тести — успішно"}.get(
                                    1 if tests % 10 == 1 and tests % 100 != 11 else
                                    2 if tests % 10 in (2, 3, 4) and tests % 100 not in (12, 13, 14) else 5,
                                    "автоматизованих тестів — успішно"))]):
    x = M + i * Inches(3.05)
    stat(s, x, Inches(1.7), Inches(2.8), big, lab, color=AMBER if i == 3 else WHITE,
         lab=RGBColor(0xC9, 0xD2, 0xDB))
tb(s, M, Inches(3.75), Inches(5.8), Inches(3.0), [
    [("Переваги", {"bold": True, "size": 20, "color": WHITE})],
    "правила виконує СКБД, застосунок — без прав суперкористувача;",
    "кожна дія — у незмінному журналі аудиту;",
    "рішення на пуск ухвалює людина.",
], size=16, color=RGBColor(0xE4, 0xE9, 0xEE))
tb(s, Inches(6.9), Inches(3.75), Inches(5.8), Inches(3.0), [
    [("Напрями розвитку", {"bold": True, "size": 20, "color": WHITE})],
    "шлюзи з адаптерами MQTT, ASTERIX, MAVLink;",
    "деконфлікція з планами польотів;",
    "доставка завдань на планшет, сповіщення, 2FA.",
], size=16, color=RGBColor(0xE4, 0xE9, 0xEE))

assert len(prs.slides) == N_SLIDES, len(prs.slides)
prs.core_properties.title = "Захист курсової роботи з ПІС"
prs.core_properties.author = "Петро Кравченко"
prs.save(OUT)
print(OUT, len(prs.slides), "слайдів")
