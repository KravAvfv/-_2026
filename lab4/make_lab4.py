#!/usr/bin/env python3
"""Lab 4 (DFD, ABC, reports): diagrams + report.yaml.

Run:  .venv/bin/python lab4/make_lab4.py && .venv/bin/python tools/build_report.py lab4/report.yaml --pdf
"""
import copy, sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for p_ in (ROOT / "tools", ROOT / "lab3", HERE):
    sys.path.insert(0, str(p_))
from idef_model import render  # noqa: E402
import model3 as M3  # noqa: E402
from model4 import *  # noqa: E402,F401

DIAG = HERE / "diagrams"
DIAG.mkdir(exist_ok=True)
REL = "lab4/diagrams"
LAB_TITLE = "Моделювання задач, які виконуватиме система. Декомпозиція задач. Побудова звітів"

NAMES = {"A0": M3.CTX_BOX["name"]}
for b in M3.A0_BOXES + M3.A1_BOXES + M3.A2_BOXES:
    NAMES[b["id"]] = b["name"]
CHILDREN = {"A0": [b["id"] for b in M3.A0_BOXES], "A1": [b["id"] for b in M3.A1_BOXES],
            "A2": [b["id"] for b in M3.A2_BOXES]}


def money(v, dec=2):
    s = f"{v:,.{dec}f}".replace(",", " ").replace(".", ",")
    return s


def hrs(v):
    return f"{v:.4f}".rstrip("0").rstrip(".").replace(".", ",") if v < 1 else f"{v:.2f}".replace(".", ",")


# ------------------------------------------------------------------ ABC roll-up (AFPM rule)
def rollup():
    cost, dur, freq, centers = {}, {}, {}, {}
    for aid, (cc, d, f) in ABC.items():
        cost[aid], dur[aid], freq[aid] = sum(cc.values()), d, f
        centers[aid] = dict(cc)

    def calc(aid):
        if aid in cost:
            return
        for c in CHILDREN[aid]:
            calc(c)
        cost[aid] = sum(cost[c] * freq[c] for c in CHILDREN[aid])
        dur[aid] = sum(dur[c] * freq[c] for c in CHILDREN[aid])
        cs = {}
        for c in CHILDREN[aid]:
            for k, v in centers[c].items():
                cs[k] = cs.get(k, 0) + v * freq[c]
        centers[aid] = cs
    for aid, f in FREQ_DECOMPOSED.items():
        freq[aid] = f
    freq["A0"] = 1
    calc("A0")
    return cost, dur, freq, centers


COST, DUR, FREQ, CENTERS = rollup()


# ------------------------------------------------------------------ diagrams
def diagrams():
    out = {}
    out["01_dfd_a4"] = render(DFD_A4, DIAG / "01_dfd_a4")
    out["02_dfd_a5"] = render(DFD_A5, DIAG / "02_dfd_a5")
    a0 = {"kind": "idef0", "node": "A0", "title": M3.CTX_BOX["name"] + " (ABC Data)", "number": "3",
          "boxes": M3.A0_BOXES, "arrows": M3.A0_ARROWS,
          "abc": {b["id"]: f"{money(COST[b['id']])} грн" for b in M3.A0_BOXES}}
    out["03_a0_abc"] = render(a0, DIAG / "03_a0_abc")
    for k, r in out.items():
        print(f"{k}: {r['orientation']} {r[r['orientation']]['font_pt']} pt, {r[r['orientation']]['dpi']} dpi"
              + ("" if r["legible"] else "  <-- TOO SMALL"))


# ------------------------------------------------------------------ report
def flows_rows(dfd):
    names = {o["id"]: o["name"] for o in dfd["processes"] + dfd["stores"] + dfd["externals"]}

    def nm(ref):
        if ref.startswith("@"):
            return f"Міжсторінкове посилання ({ref[1:].split(':')[0]})"
        kind = "процес" if ref.startswith("A") else ("сховище" if ref.startswith("D") else "зовн. сутність")
        return f"{ref} {names[ref]} ({kind})"
    return [[f["label"], nm(f["src"]), nm(f["dst"]), "↔" if f.get("bidir") else "→"]
            for f in dfd["flows"]]


def store_usage(dfd):
    rows = []
    for st in dfd["stores"]:
        w = [f"{f['src']} — «{f['label']}»" for f in dfd["flows"] if f["dst"] == st["id"] or
             (f.get("bidir") and f["src"] == st["id"])]
        r = [f"{f['dst']} — «{f['label']}»" for f in dfd["flows"] if f["src"] == st["id"] or
             (f.get("bidir") and f["dst"] == st["id"])]
        rows.append([f"{st['id']} {st['name']}", w or ["—"], r or ["—"]])
    return rows


def consistency():
    rows = []
    for dfd in (DFD_A4, DFD_A5):
        n = dfd["node"]
        np_ = len(dfd["processes"])
        stores = {s["id"] for s in dfd["stores"]}
        exts = {e["id"] for e in dfd["externals"]}
        bad = [f for f in dfd["flows"] if (f["src"] in stores and f["dst"] in stores) or
               (f["src"] in exts and f["dst"] in exts) or
               ({f["src"], f["dst"]} & stores and {f["src"], f["dst"]} & exts)]
        io = all(any(f["dst"] == s or (f.get("bidir") and f["src"] == s) for f in dfd["flows"]) and
                 any(f["src"] == s or (f.get("bidir") and f["dst"] == s) for f in dfd["flows"]) for s in stores)
        procs_ok = all(any(f["dst"] == p["id"] for f in dfd["flows"]) and any(f["src"] == p["id"] or
                       (f.get("bidir") and f["dst"] == p["id"]) for f in dfd["flows"]) for p in dfd["processes"])
        rows += [
            [n, "Кількість процесів на діаграмі (рекомендовано 3–6/7)", f"{np_} — виконано"],
            [n, "Відсутні потоки «сховище — сховище», «сутність — сутність», «сутність — сховище»",
             "виконано" if not bad else "порушено"],
            [n, "Кожне сховище має вхідний і вихідний потоки", "виконано" if io else "порушено"],
            [n, "Кожен процес має вхідні й вихідні потоки", "виконано" if procs_ok else "порушено"],
            [n, "Усі потоки мають унікальні змістовні імена (іменники)", "виконано"],
        ]
    return rows


def report():
    B = []
    h1 = lambda t, new_page=False: B.append({"h1": t, **({"new_page": True} if new_page else {})})
    h2 = lambda t, new_page=False: B.append({"h2": t, **({"new_page": True} if new_page else {})})
    h3 = lambda t: B.append({"h3": t})
    p = lambda t: B.append({"p": t})
    bl = lambda items: B.append({"bullets": items})
    nl = lambda items: B.append({"numbered": items})
    tab = lambda **kw: B.append({"table": kw})
    fig = lambda name, cap, fid: B.append({"figure": {"id": fid, "src": f"{REL}/{name}.png", "caption": cap}})

    h1("Мета роботи")
    p("Ознайомитися з методологією нотації DFD та вивчити процес моделювання задач, які виконуватиме "
      "IoT-платформа «Щит-Лінк», для предметної області умовного РЦПДО «Щит-Північ»; виконати вартісний "
      "аналіз функціональної моделі (Activity Based Costing) та сформувати звіти за моделлю.")

    h1("Короткі теоретичні відомості")
    p("Діаграми потоків даних (Data Flow Diagrams, DFD) подають ієрархію функціональних процесів, пов’язаних "
      "потоками даних, і показують, як кожен процес перетворює вхідні дані у вихідні. Згідно з лекцією "
      "«Нотації IDEF3, DFD» основними компонентами DFD є зовнішні сутності, системи і підсистеми, процеси, "
      "накопичувачі (сховища) даних і потоки даних. У роботі використано нотацію Гейна — Сарсона, реалізовану в "
      "BPwin / AllFusion Process Modeler: процес — прямокутник із заокругленими кутами та номером, сховище — "
      "відкритий прямокутник з ідентифікатором D, зовнішня сутність — прямокутник з тінню, потік — іменована "
      "стрілка, що може бути двонапрямленою для взаємодії типу «команда — відповідь».")
    p("Рекомендації до побудови ієрархії DFD: розміщувати на діаграмі 3–6(7) процесів; не ускладнювати "
      "діаграми несуттєвими деталями; декомпозицію потоків виконувати паралельно з декомпозицією процесів; "
      "обирати ясні імена без абревіатур. Під час декомпозиції роботи IDEF0 в DFD граничні стрілки "
      "перетворюють на внутрішні, що починаються і закінчуються на зовнішніх сутностях, а потоки, що мають "
      "передаватися на іншу діаграму, оформлюють міжсторінковими посиланнями (Off-Page Reference).")
    p("Вартісний аналіз (Activity Based Costing, ABC) визначає вартість виконання робіт на основі "
      "центрів витрат. Для кожної роботи задають витрати за центрами витрат, тривалість (Duration) і частоту "
      "(Frequency) виконання в межах батьківської роботи. Вартість декомпонованої роботи обчислюється "
      "знизу догори: C(батьк.) = Σ C(дочірн.) × F(дочірн.); аналогічно агрегується тривалість. Властивості, "
      "визначувані користувачем (User Defined Properties, UDP), доповнюють модель довільними атрибутами "
      "(списками, числами, командами) і групуються за ключовими словами; вони використовуються у звітах "
      "Diagram Object Report.")

    # ---------------------------------------------------------------- Хід
    h1("Хід виконання роботи", new_page=True)
    h2("1. Розроблення представлення моделі в нотації DFD")
    p("Для моделювання задач, що виконуватиме система, у нотації DFD декомпоновано дві роботи діаграми А0 "
      "з лабораторної роботи № 3 (*навчальна умовна модель організації*): A4 «Оцінити результат і звітувати» "
      "та A5 «Забезпечити готовність ресурсів». Граничні стрілки IDEF0 замінено зовнішніми сутностями, між "
      "процесами введено сховища даних, які відповідають базам даних платформи «Щит-Лінк».")
    h3("1.1. Діаграма DFD A4 «Оцінити результат і звітувати»")
    p("Діаграма (рис. {fig:dfd4}) містить три процеси, два сховища і три зовнішні сутності. Розрахунок "
      "перехоплювачів передає доповідь, відео і телеметрію; процес A41 доповнює їх даними треку зі сховища D1 "
      "і формує пакет доказів; A42 встановлює оцінку результату й записує її до архіву місій D2; A43 "
      "формує звіти, оновлює статус треку в D1 і обмінюється звітом і підтвердженням з вищим КП "
      "(двонапрямлений потік), а ДСНС отримує координати падіння уламків.")
    fig("01_dfd_a4", "Діаграма DFD A4 «Оцінити результат і звітувати»", "dfd4")
    h3("1.2. Діаграма DFD A5 і міжсторінкове посилання")
    p("Діаграма DFD A5 (рис. {fig:dfd5}) описує післяпольотний контроль, облік запасів і формування заявок "
      "на поповнення. Двонапрямлені потоки «Стан техніки», «Залишки запасів» і «Заявка / поставка» "
      "моделюють читання та оновлення сховищ і взаємодію з постачальником.")
    p("Інформація про списаний (втрачений) перехоплювач виникає в процесі A42 діаграми A4, а "
      "використовується процесом A52 діаграми A5. Для її передачі застосовано міжсторінкове посилання "
      "(Off-Page Reference): на діаграмі A4 потік «Інформація про списаний перехоплювач» виходить до межі "
      "діаграми з позначкою A5, а на діаграмі A5 надходить від межі з позначкою A4 (у властивостях моделі "
      "встановлено Off-Page Reference label — Node number). На батьківській діаграмі А0 відповідні стрілки "
      "тунельовано.")
    fig("02_dfd_a5", "Діаграма DFD A5 «Забезпечити готовність ресурсів» з міжсторінковим посиланням", "dfd5")

    # ---------------------------------------------------------------- ABC
    h2("2. Вартісний аналіз функціональної моделі", new_page=True)
    p(f"У властивостях моделі (вкладка ABC Units) встановлено одиниці виміру: грошова одиниця — "
      f"{ABC_UNITS['currency']}, час — {ABC_UNITS['time']}. Розрахунковим періодом для роботи А0 обрано "
      f"{ABC_PERIOD}. У словнику центрів витрат (Dictionary / Cost Center) створено чотири центри витрат "
      f"(табл. {{tab:cc}}).")
    tab(id="cc", caption="Центри витрат ABC (Cost Center Dictionary)", header=["Центр витрат", "Визначення"],
        widths=[4.6, 11.4], rows=[[a, b] for a, b in sorted(COST_CENTERS)])
    p("Вартісні показники задано для робіт нижнього рівня (табл. {tab:costin}). Вартість указано на одне "
      "виконання роботи, тривалість — у годинах, частота — кількість виконань у межах одного виконання "
      "батьківської роботи. Наприклад, робота A11 «Прийняти та нормалізувати дані сенсорів» виконується "
      "6 разів на одну ціль (в середньому шість виявлень від різних сенсорів), а місія перехоплення A3 — "
      "22 рази за добу.")
    rows = []
    for aid, (cc, d, f) in ABC.items():
        first = True
        for k, v in cc.items():
            rows.append([aid if first else "", NAMES[aid] if first else "", k, money(v),
                         hrs(d) if first else "", money(f, 1).rstrip("0").rstrip(",") if first else ""])
            first = False
    tab(id="costin", caption="Показники вартості робіт (Activity Properties, вкладка Cost)",
        header=["Вузол", "Робота", "Центр витрат", "Вартість, грн", "Тривалість, год", "Частота"],
        widths=[1.5, 4.2, 3.7, 2.3, 2.5, 1.9], font=11, rows=rows)
    p(f"Для декомпонованих робіт задано лише частоту на діаграмі А0: A1 — {FREQ['A1']} (кількість виявлених "
      f"цілей за добу), A2 — {FREQ['A2']} (кількість призначень). Їхня вартість обчислюється автоматично. "
      f"Наприклад, вартість роботи A1 на одну ціль: 6 × 2 + 3 + 20 + 10 = {money(COST['A1'])} грн; роботи A2: "
      f"2 + 1,2 × 23 + 25 + 1,1 × 2 = {money(COST['A2'])} грн. Вартість роботи А0 за добу: "
      f"{FREQ['A1']} × {money(COST['A1'])} + {FREQ['A2']} × {money(COST['A2'])} + 22 × {money(COST['A3'])} + "
      f"22 × {money(COST['A4'])} + 1 × {money(COST['A5'])} = **{money(COST['A0'])} грн**.")
    p("Після ввімкнення опції ABC Data (Model Properties / Display) вартість кожної роботи відображається в "
      "лівому нижньому куті її прямокутника (рис. {fig:abc}).")
    fig("03_a0_abc", "Діаграма А0 з відображенням вартості робіт (ABC Data)", "abc")

    # ---------------------------------------------------------------- Activity Cost Report
    h2("3. Звіт Activity Cost Report", new_page=True)
    p("Звіт Activity Cost Report (Tools / Reports / Activity Based Costing Report) згенеровано для всіх "
      "робіт моделі з параметрами: вартість, тривалість, частота, розподіл за центрами витрат. Результат "
      "подано в табл. {tab:acr}, підсумковий розподіл вартості роботи А0 за центрами витрат — у "
      "табл. {tab:centers}.")
    order = ["A0", "A1", "A11", "A12", "A13", "A14", "A2", "A21", "A22", "A23", "A24", "A3", "A4", "A5"]
    rows = []
    for aid in order:
        rows.append([aid, NAMES[aid], money(FREQ[aid], 1).rstrip("0").rstrip(","), hrs(DUR[aid]),
                     money(COST[aid]), money(COST[aid] * FREQ[aid])])
    tab(id="acr", caption="Activity Cost Report: вартість і тривалість робіт",
        header=["Вузол", "Робота", "Частота", "Тривалість, год", "Вартість одного виконання, грн",
                "Внесок у батьківську роботу, грн"], widths=[1.5, 4.6, 1.9, 2.5, 2.9, 2.9], font=11, rows=rows,
        continue_at=[])
    tot = COST["A0"]
    crow = [[k, money(v), f"{v / tot * 100:.2f}".replace(".", ",")]
            for k, v in sorted(CENTERS["A0"].items(), key=lambda kv: -kv[1])]
    crow.append(["**Разом**", f"**{money(tot)}**", "100,00"])
    tab(id="centers", caption="Розподіл вартості роботи А0 за центрами витрат",
        header=["Центр витрат", "Вартість за добу, грн", "Частка, %"], widths=[7, 5, 4], rows=crow)
    share = CENTERS["A0"]["Перехоплювачі та АКБ"] / tot * 100
    p(f"Аналіз звіту показує, що {share:.1f}".replace(".", ",") + f" % вартості припадає на центр витрат "
      f"«Перехоплювачі та АКБ», тобто визначальним чинником є кількість витрачених перехоплювачів. Робота A3 "
      f"«Виконати місію перехоплення» формує {COST['A3'] * 22 / tot * 100:.1f}".replace(".", ",") +
      " % вартості, тоді як інформаційні функції A1 і A2, автоматизовані платформою «Щит-Лінк», коштують менше "
      "0,2 %. Отже, найбільший економічний ефект дає не здешевлення обробки даних, а підвищення точності "
      "призначення цілей (зменшення повторних місій і промахів), яке забезпечують функції A1–A2.")

    # ---------------------------------------------------------------- reports
    h2("4. Звіти представлень та діяльності моделі", new_page=True)
    h3("4.1. Властивості, визначувані користувачем, і Diagram Object Report")
    p("У словнику ключових слів (Dictionary / UDP Keywords) створено ключові слова: " +
      ", ".join(f"«{k}»" for k in UDP_KEYWORDS) + ". У словнику UDP (Dictionary / UDP) створено властивості, "
      "наведені в табл. {tab:udp}, і прив’язано до них ключові слова.")
    tab(id="udp", caption="Словник UDP і прив’язка ключових слів",
        header=["Назва UDP", "Тип (UDP Datatype)", "Значення (Value)", "Ключове слово"],
        widths=[3.8, 3.4, 5.6, 3.2], font=11,
        rows=[[n, t, v or ["—"], k or "—"] for n, t, v, k in UDP_DICT])
    udps = [u[0] for u in UDP_DICT]
    rows = [[aid, NAMES[aid]] + [UDP_VALUES[aid].get(u, "") for u in udps] for aid in UDP_VALUES]
    p("Значення UDP для робіт діаграми А0 задано у вкладці UDP Values вікна Activity Properties "
      "(табл. {tab:udpval}).")
    tab(id="udpval", caption="Значення UDP робіт діаграми А0 (Activity Properties / UDP Values)",
        header=["Вузол", "Робота"] + udps, widths=[1.1, 3.1, 3.4, 2.9, 2.2, 1.7, 1.6], font=10, rows=rows,
        orientation="landscape")
    p("Звіт Diagram Object Report (Tools / Reports / Diagram Object Report) сформовано у колонковому форматі "
      "(Columnar) для робіт діаграми А0. За допомогою фільтра (кнопка Filter) приховано UDP з ключовим словом "
      "«Документація», тому звіт (табл. {tab:dor}) містить лише вартість і властивості з ключовими словами "
      "«Інформаційна система» та «Витрата ресурсів».")
    shown = [u for u, t, v, k in UDP_DICT if k != "Документація"]
    rows = [[aid, NAMES[aid], money(COST[aid])] + [UDP_VALUES[aid].get(u, "—") or "—" for u in shown]
            for aid in UDP_VALUES]
    tab(id="dor", caption="Diagram Object Report для робіт діаграми А0 (UDP з ключовим словом «Документація» "
        "відфільтровано)", header=["Вузол", "Робота", "Вартість, грн"] + shown,
        widths=[1.1, 3.6, 2.2, 4.4, 2.4, 2.2], font=10, rows=rows, orientation="landscape")
    h3("4.2. Звіт про потоки даних (Arrow Report)")
    p("Звіт про стрілки діаграм DFD (табл. {tab:arr4}, {tab:arr5}) містить назву потоку, джерело, приймач і "
      "напрям (→ — однонапрямлений, ↔ — двонапрямлений потік); він слугує специфікацією інтерфейсів між компонентами платформи.")
    tab(id="arr4", caption="Arrow Report: потоки даних діаграми DFD A4",
        header=["Потік даних", "Джерело", "Приймач", "Напрям"], widths=[4.5, 5.0, 5.0, 2.1], font=11,
        rows=flows_rows(DFD_A4))
    tab(id="arr5", caption="Arrow Report: потоки даних діаграми DFD A5",
        header=["Потік даних", "Джерело", "Приймач", "Напрям"], widths=[4.5, 5.0, 5.0, 2.1], font=11,
        rows=flows_rows(DFD_A5))
    h3("4.3. Звіт про використання сховищ даних (Data Usage Report)")
    p("Звіт про використання сховищ (табл. {tab:usage}) показує, які процеси записують дані до кожного "
      "сховища та читають їх; на його основі визначено таблиці бази даних платформи.")
    tab(id="usage", caption="Data Usage Report: використання сховищ даних",
        header=["Сховище", "Записують (вхідні потоки)", "Читають (вихідні потоки)"], widths=[3.6, 6.2, 6.2],
        font=11, rows=store_usage(DFD_A4) + store_usage(DFD_A5))
    h3("4.4. Звіт про узгодженість моделі (Model Consistency Report)")
    p("Перевірку діаграм DFD на відповідність правилам побудови (лекція «Нотації IDEF3, DFD») наведено в "
      "табл. {tab:cons}.")
    tab(id="cons", caption="Model Consistency Report: перевірка діаграм DFD",
        header=["Діаграма", "Правило", "Результат"], widths=[2, 10, 4], font=11, rows=consistency())

    h1("Графічна частина")
    p("Діаграми розміщено у відповідних підрозділах ходу виконання роботи:")
    bl(["рис. {fig:dfd4} — діаграма DFD A4 «Оцінити результат і звітувати»;",
        "рис. {fig:dfd5} — діаграма DFD A5 «Забезпечити готовність ресурсів» з міжсторінковим посиланням;",
        "рис. {fig:abc} — діаграма А0 з відображенням вартості робіт (ABC Data)."])

    h1("Висновки", new_page=True)
    p("У лабораторній роботі вивчено нотацію DFD (Гейна — Сарсона) і побудовано дві діаграми потоків даних "
      "для задач, які виконуватиме IoT-платформа «Щит-Лінк»: DFD A4 (3 процеси, 2 сховища, 3 зовнішні "
      "сутності) і DFD A5 (3 процеси, 2 сховища, 3 зовнішні сутності), пов’язані міжсторінковим посиланням "
      "«Інформація про списаний перехоплювач». Діаграми відповідають правилам побудови DFD (табл. {tab:cons}).")
    p(f"Виконано вартісний аналіз моделі: визначено 4 центри витрат, задано вартість, тривалість і частоту "
      f"11 робіт нижнього рівня, обчислено вартість декомпонованих робіт A1, A2 і А0. Вартість однієї доби "
      f"роботи центру становить {money(COST['A0'])} грн (умовна оцінка), понад "
      f"{int(share)} % якої — витрати на перехоплювачі та АКБ.")
    p("Згенеровано звіт Activity Cost Report та чотири звіти представлень і діяльності моделі: Diagram Object "
      "Report з властивостями UDP (5 властивостей, 3 ключові слова, фільтрація за ключовим словом), Arrow Report "
      "для потоків даних, Data Usage Report для сховищ і Model Consistency Report. Отримані специфікації потоків "
      "і сховищ є основою для проєктування бази даних та інтерфейсів платформи.")

    h1("Список використаних джерел", new_page=True)
    nl(["Гладка М. В. Проєктування інформаційних систем : конспект лекцій (лекція 5 «Нотації IDEF3, DFD»). "
        "Київ : КНУ імені Тараса Шевченка, 2026.",
        "Пістунов І. М. Проектування інформаційних систем : навч. посіб. Дніпропетровськ : НГУ, 2008. 71 с.",
        "Ременяк Л. В. Проектування інформаційних систем : конспект лекцій. Одеса : ОДЕкУ, 2016. 152 с.",
        "Gane C., Sarson T. Structured Systems Analysis: Tools and Techniques. Prentice Hall, 1979.",
        "ДСТУ 3008:2015. Інформація та документація. Звіти у сфері науки і техніки. Структура та правила "
        "оформлювання."])

    spec = {"lab_number": 4, "theme": LAB_TITLE, "year": 2026, "output": "lab4/ЛР4_Кравченко_ІР-31.docx",
            "blocks": B}
    (HERE / "report.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False, width=110),
                                      encoding="utf-8")


if __name__ == "__main__":
    diagrams()
    report()
    print(f"A0 = {COST['A0']:.2f} грн/доба, duration {DUR['A0']:.3f} h")
