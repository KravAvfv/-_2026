#!/usr/bin/env python3
"""ЛР1 / ЛР2 «Системи банкової безпеки» (Cisco Packet Tracer), варіант 08.

    .venv/bin/python bank_work/make_lab.py 1 2

На кожну роботу в `Лабораторна робота N/Готово/`:
  * `CLI/*.txt`                — команди для вставки в CLI Packet Tracer (числа варіанта підставлено);
  * `ЛР_N_Інструкція_08.md`    — покрокова інструкція: побудова топології, скриншоти, що куди зберегти;
  * `ЛР_N_Звіт_Варіант_08_Кравченко.docx/.pdf` — шаблон звіту викладача, заповнений; скриншоти беруться з
    `Лабораторна робота N/Скриншоти/1.png … 6.png` (поки їх немає — у комірці стоїть позначка й збірка
    попереджає). MAC-адреси для ЛР2 — `Скриншоти/macs.txt` (рядки «Kasa-2 0001.AAAA.0001»), необов'язково.
"""
import copy
import datetime
import subprocess
import sys
from pathlib import Path

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import labs as L  # noqa: E402

SRC = ROOT / "Системи банкової безпеки"
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def lab_dir(n):
    return SRC / f"Лабораторна робота {n}"


def shot(n, k):
    for ext in IMG_EXT:
        p = lab_dir(n) / "Скриншоти" / f"{k}{ext}"
        if p.exists():
            return p
    return None


def read_macs(n):
    f = lab_dir(n) / "Скриншоти" / "macs.txt"
    if not f.exists():
        return {}
    out = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        parts = line.replace(":", " ").split()
        if len(parts) >= 2:
            mac = parts[-1].upper()
            assert len(mac) == 14 and mac.count(".") == 2, f"MAC у форматі XXXX.XXXX.XXXX: {line!r}"
            out[parts[0]] = mac
    return out


# ------------------------------------------------------------------------------------------------ docx helpers
def set_text(p, text, bold=None):
    """Замінити текст абзацу, зберігши формат першого прогону."""
    runs = p.runs
    if not runs:
        p.add_run(text)
        return p
    runs[0].text = text
    if bold is not None:
        runs[0].bold = bold
    for r in runs[1:]:
        r._element.getparent().remove(r._element)
    return p


def cell_text(cell, text, size=10.5):
    p = cell.paragraphs[0]
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.name = "Times New Roman"
    for extra in cell.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)


def delete(p):
    p._element.getparent().remove(p._element)


def insert_after(p, text="", size=11.5, bold=False, font="Times New Roman", align=None, after=2):
    new = copy.deepcopy(p._element)
    p._element.addnext(new)
    np_ = docx.text.paragraph.Paragraph(new, p._parent)
    for r in list(np_.runs):
        r._element.getparent().remove(r._element)
    r = np_.add_run(text)
    r.font.size = Pt(size)
    r.font.name = font
    r.bold = bold
    pf = np_.paragraph_format
    pf.space_after = Pt(after)
    pf.space_before = Pt(0)
    np_.alignment = align if align is not None else WD_ALIGN_PARAGRAPH.LEFT
    pf.first_line_indent = Cm(0)
    return np_


# ------------------------------------------------------------------------------------------------ report
def build_report(n, data, cli):
    d = docx.Document(lab_dir(n) / f"Лабораторна_{n}_Шаблон_звіту.docx")
    t = d.tables
    head = [L.PIB, L.GROUP, L.VAR, datetime.date.today().strftime("%d.%m.%Y")]
    for row, v in zip(t[0].rows, head):
        cell_text(row.cells[1], v, 11.5)
    for row, (done, note) in zip(t[1].rows[1:], data["steps"]):
        cell_text(row.cells[1], done)
        cell_text(row.cells[2], note, 10)

    missing = []
    caps = [p for p in d.paragraphs if p.text.startswith("Підпис:")]
    assert len(caps) == 6
    for k in range(6):
        cell = t[2 + k].cell(0, 0)
        img = shot(n, k + 1)
        set_text(cell.paragraphs[0], cell.paragraphs[0].text.replace("Вставте зображення. ", ""))
        target = cell.paragraphs[1]
        for extra in cell.paragraphs[2:]:
            delete(extra)
        if img:
            target.alignment = WD_ALIGN_PARAGRAPH.CENTER
            target.add_run().add_picture(str(img), width=Cm(14.6))
        else:
            missing.append(k + 1)
            r = target.add_run(f"[скриншот {k + 1} ще не вставлено: Скриншоти/{k + 1}.png]")
            r.italic = True
        set_text(caps[k], f"Підпис: {data['shots'][k]}")

    chk = t[8]
    for row, vals in zip(chk.rows[1:], data["checks"]):
        for c, v in zip(row.cells[1:], vals):
            cell_text(c, v, 9.5 if n == 1 else 9)
    if n == 2:
        for row, vals in zip(t[9].rows[1:], data["modes"]):
            for c, v in zip(row.cells[1:], vals):
                cell_text(c, v, 9)

    qs = [p for p in d.paragraphs if "[перепишіть запитання" in p.text]
    ans = [p for p in d.paragraphs if p.text.startswith("Відповідь:")]
    assert len(qs) == len(ans) == 5
    for i, (q, a) in enumerate(data["qa"]):
        set_text(qs[i], f"{i + 1}. {q}", bold=True)
        set_text(ans[i], f"Відповідь: {a}")
        ans[i].paragraph_format.space_after = Pt(6)
        ans[i].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    paras = d.paragraphs
    hint = next(i for i, p in enumerate(paras) if p.text.startswith("Що було проблемою"))
    lines = [p for p in paras[hint + 1:] if set(p.text.strip()) == {"_"}]
    assert len(lines) == 4
    set_text(paras[hint], " ".join(data["conclusion"]))
    paras[hint].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for p in lines:
        delete(p)

    # Додаток: введені команди (підтверджують розділ «Виконані кроки»)
    last = paras[hint]
    last = insert_after(last, "Додаток. Команди, введені в CLI (вкладка CLI пристроїв)", 13, True, after=4)
    last.paragraph_format.space_before = Pt(10)
    last.paragraph_format.keep_with_next = True
    for name, cmds in cli.items():
        dev = L.L1_R if "маршрутизатор" in name else (L.L1_SW if n == 1 else L.L2_SW)
        last = insert_after(last, f"{dev} — {name.split('_', 1)[1].replace('_', ' ')}", 11.5, True, after=1)
        last.paragraph_format.keep_with_next = True
        body = [c for c in cmds if c and not c.startswith("show")]
        last = insert_after(last, "\n".join(body), 9.5, font="Courier New", after=6)
    out = lab_dir(n) / "Готово" / f"ЛР_{n}_Звіт_Варіант_{L.VAR}_{L.SURNAME}.docx"
    d.save(out)
    pdf = out.with_suffix(".pdf")
    subprocess.run(["bash", str(ROOT / "tools/docx2pdf.sh"), str(out), str(pdf)], check=True,
                   stdout=subprocess.DEVNULL)
    return out, missing


# ------------------------------------------------------------------------------------------------ guide
def code(lines):
    return ["```", *lines, "```"]


def guide1(cli):
    g = [f"# ЛР 1 — {L.L1['title']} (варіант {L.VAR})", "",
         "Шаблону .pkt від викладача немає, тому спершу будуємо його самі за таблицею брифу (крок А), потім "
         "виконуємо роботу (кроки Б–Д). Команди копіюйте з файлів у папці `CLI/` і вставляйте у вкладку **CLI** "
         "пристрою (Ctrl+V або права кнопка → Paste). Скриншоти — **усе вікно Packet Tracer** з видимою "
         f"приміткою «{L.NOTE}» (Spectacle: «Активне вікно», або Meta+Shift+PrintScreen). Зберігайте їх як "
         "`Лабораторна робота 1/Скриншоти/1.png … 6.png`.", "",
         "Порада: Options → Preferences → Font → збільште шрифт CLI до 14–16, а вікно CLI розтягніть — так текст "
         "буде читатися у звіті.", "",
         "## А. Шаблон (плоска мережа)", "",
         "1. Новий файл. Додайте: маршрутизатор **1941**, комутатор **2960-24TT**, 8 × **PC-PT**, 2 × **Laptop-PT**.",
         f"2. Імена (вкладка Config → Display Name): маршрутизатор `BR-R1`, комутатор `BR-SW1`, "
         "ПК і ноутбуки — як у таблиці нижче.",
         "3. Кабелі — **Copper Straight-Through**: BR-R1 `GigabitEthernet0/0` ↔ BR-SW1 `GigabitEthernet0/1`; "
         "кожен ПК `FastEthernet0` ↔ порт комутатора з таблиці.",
         "4. Адреси «плоскої» мережі (Desktop → IP Configuration → Static, маска 255.255.255.0, шлюз порожній):", "",
         "| Пристрій | Тип | Порт BR-SW1 | Адреса шаблону | Адреса за карткою | Шлюз |", "|---|---|---|---|---|---|"]
    for name, typ, zone, port, flat, ip in L.DEV1:
        g.append(f"| {name} | {typ} | {port} | {flat} | {ip} | {L.gw(L.ZVLAN[zone])} |")
    g += ["", f"5. Інструмент **Place Note** (N) → текст `{L.NOTE}` → поставте біля комутатора.",
          f"6. File → Save As → `Лабораторна робота 1/Готово/ЛР_1_Варіант_{L.VAR}_{L.SURNAME}.pkt`.",
          "7. Зачекайте, поки всі індикатори на лінках стануть зеленими (або натисніть Fast Forward Time).", "",
          "## Б. Скриншот 1 — проблема", "",
          "Guest-1 → Desktop → Command Prompt → `ping 192.168.0.11`. Пінг проходить → **скриншот 1** "
          "(видно вікно Command Prompt і примітку).", "",
          "## В. Питання 1 — VLAN і порти", "",
          f"BR-SW1 → CLI → Enter → вставте `CLI/1_комутатор_VLAN_і_порти.txt`:", "",
          *code(cli["1_комутатор_VLAN_і_порти"]), "",
          "Останньою виконується `show vlan brief` → **скриншот 2** (KASA Fa0/1-2 … GUEST Fa0/9-10; у default — "
          f"Fa0/11–24 і Gig0/2; PARKING {L.NATIVE} порожній).", "",
          "## Г. Питання 2 — магістраль, підінтерфейси, адреси", "",
          f"1. На {L.L1_SW} вставте `CLI/2_комутатор_магістраль.txt`:", "", *code(cli["2_комутатор_магістраль"]),
          "", "   Після `show interfaces trunk` → **скриншот 3** (Gig0/1 on 802.1q, native "
          f"{L.NATIVE}, allowed 19,93,115,126).", "",
          "2. BR-R1 → CLI → на питання «initial configuration dialog» відповідайте `no` → вставте "
          "`CLI/3_маршрутизатор.txt`:", "", *code(cli["3_маршрутизатор"]), "",
          "   Повідомлення CDP про невідповідність native VLAN (якщо з'являться) ігноруйте — так задумано.",
          "3. На всіх 10 ПК поставте адреси з колонок «Адреса за карткою» і «Шлюз» (Desktop → IP Configuration → "
          "Static). Швидше: Command Prompt → `ipconfig <адреса> 255.255.255.0 <шлюз>`, наприклад "
          "`ipconfig 10.206.93.11 255.255.255.0 10.206.93.1`.",
          "4. Розтягніть вікно CLI BR08-R1 так, щоб було видно результат `show ip interface brief` і "
          "`show ip route` (чотири рядки C) → **скриншот 4**.", "",
          "## Д. Питання 3 — Simulation Mode", "",
          "1. Праворуч унизу перемкніться на **Simulation**. Edit Filters → Show All/None → залиште лише **ICMP** і "
          "**ARP**.",
          "2. Інструмент **Add Simple PDU** (конвертик): клік по джерелу, клік по призначенню; далі **Capture / "
          "Forward**, поки пакет не дійде або не зникне. Перед кожною перевіркою — **Reset Simulation**.",
          "3. Перевірки: 1) ABS-1 → Mgr-1 (так); 2) Kasa-1 → ATM-1 (так); 3) Guest-1 → Mgr-1 (ні); "
          "4) Sensor-1 → Kasa-1 (ні); 5) Sensor-1 → Cam-1 (так).",
          "4. **Скриншот 5** — перевірка 1: у Event List клікніть кольоровий квадратик події на ділянці "
          "BR08-SW1 → BR08-R1, відкриється PDU Information; у вкладці Outbound PDU Details видно **802.1Q, TCI / "
          "VLAN: 19** (або 115 на зворотній ділянці). На скриншоті мають бути Event List, вікно PDU і примітка.",
          "5. **Скриншот 6** — перевірка 3: проганяйте Capture / Forward, доки ARP-запит від Guest-1 не дійде до "
          "Guest-2 і там не зникне (Guest-2 його відкидає), а ICMP-конвертик стоїть на Guest-1. Видно місце, де "
          "пакет зник, і Event List.",
          "6. Якщо будь-яка перевірка дала не той результат, що в дужках — напишіть мені, я виправлю таблицю.",
          "7. File → Save (Ctrl+S). Файл .pkt знадобиться на захисті.", "",
          "## Е. Готово", "",
          "Скажіть мені «скриншоти ЛР1 готові» — я вставлю їх у звіт, перевірю й зберу PDF.", ""]
    return g


def guide2(cli):
    g = [f"# ЛР 2 — {L.L2['title']} (варіант {L.VAR})", "",
         "Як і в ЛР1, шаблон будуємо самі (крок А). Команди — у папці `CLI/`, вставляються у вкладку **CLI** "
         f"комутатора. Скриншоти — усе вікно Packet Tracer з приміткою «{L.NOTE}» → "
         "`Лабораторна робота 2/Скриншоти/1.png … 6.png`.", "",
         "## А. Шаблон (незахищений комутатор)", "",
         "1. Новий файл. Додайте: комутатор **2960-24TT** (ім'я `BR-SW1`), концентратор **Hub-PT** (`Hub-1`), "
         "6 × **PC-PT**, 1 × **Laptop-PT** (`Intruder`).",
         "2. Кабелі: ПК ↔ комутатор і ПК ↔ концентратор — **Copper Straight-Through**; Hub-1 ↔ BR-SW1 Fa0/2 — "
         "**Copper Cross-Over** (або інструмент «блискавка» — він сам обере кабель). Порти та адреси (маска "
         "255.255.255.0, шлюз порожній):", "",
         "| Пристрій | Тип | Підключення | IP-адреса |", "|---|---|---|---|"]
    for name, typ, port, ip in L.DEV2:
        g.append(f"| {name} | {typ} | {port} | {ip} |")
    g += ["", f"3. Place Note → `{L.NOTE}`. File → Save As → `Лабораторна робота 2/Готово/"
          f"ЛР_2_Варіант_{L.VAR}_{L.SURNAME}.pkt`. Дочекайтеся зелених індикаторів.", "",
          "## Б. Скриншот 1 — проблема", "",
          "Intruder → Command Prompt → `ping 192.168.1.11` (проходить). Потім BR-SW1 → CLI → Enter → `enable` → "
          f"`show mac-address-table` (є рядок з MAC Intruder на Fa0/22). Розставте вікна так, щоб було видно обидва "
          "→ **скриншот 1**.", "",
          "## В. Питання 1 — вільні порти в карантин", "",
          "Вставте `CLI/1_вільні_порти_карантин.txt`:", "", *code(cli["1_вільні_порти_карантин"]), "",
          f"Результат `show interfaces status` (Fa0/6–24 disabled, VLAN {L.QVLAN}) → **скриншот 2**. Пінг з "
          "Intruder тепер не проходить.", "",
          "## Г. Питання 2 — Port Security", "",
          "1. На **Kasa-2, Kasa-3, ABS-1, SRV-1**: Command Prompt → `ipconfig /all` → рядок Physical Address "
          "(вигляд `0001.4A2B.3C4D`). Надішліть мені ці чотири адреси (або запишіть у "
          "`Лабораторна робота 2/Скриншоти/macs.txt` рядками `Kasa-2 0001.4A2B.3C4D`) — я перегенерую файл "
          "команд з ними. Або просто замініть `<MAC …>` у файлі перед вставкою.",
          "2. Вставте `CLI/2_port_security.txt`:", "", *code(cli["2_port_security"]), "",
          "3. Щоб sticky-порти вивчили адреси: з Kasa-1 `ping 192.168.1.14` (Mgr-1) і з Mgr-1 "
          "`ping 192.168.1.11`; також ABS-1 → `ping 192.168.1.16`.",
          "4. Вставте `CLI/3_перевірка_port_security.txt`. Вивід `show port-security` (CurrentAddr: Fa0/2 = 2) → "
          "**скриншот 3**; вивід `show port-security address` (SecureSticky і SecureConfigured) → **скриншот 4**.",
          "", "## Д. Питання 3 — Intruder на робочих портах", "",
          "Перед кожною перевіркою: Intruder → IP 192.168.1.99 / 255.255.255.0 (вже стоїть). Після кожної — "
          "`show port-security interface fastEthernet 0/<порт>` і `show interfaces status`.", "",
          "1. **Перевірка 1:** Kasa-1 → `ping 192.168.1.14` (проходить).",
          "2. **Перевірка 2:** Intruder у Fa0/22 → `ping 192.168.1.11` (не проходить, порт вимкнений).",
          "3. **Перевірка 3 (shutdown):** видаліть кабель Kasa-1 ↔ Fa0/1, підключіть Intruder до Fa0/1, з Intruder "
          "`ping 192.168.1.14`. Порт стає err-disabled. На комутаторі: `show port-security interface "
          "fastEthernet 0/1` і `show interfaces status` → **скриншот 5**.",
          "4. **Відновлення (одразу після перевірки 3):** видаліть кабель Intruder, поверніть Kasa-1 на Fa0/1, "
          "вставте `CLI/4_відновлення_Fa0_1.txt`, потім з Kasa-1 `ping 192.168.1.14` (проходить) → **скриншот 6** "
          "(видно connected і успішний пінг). Intruder поверніть на Fa0/22.",
          "5. **Перевірка 4 (restrict):** Mgr-1 від Fa0/3 відключіть, Intruder → Fa0/3, `ping 192.168.1.11`; "
          "`show port-security interface fastEthernet 0/3` — порт Secure-up, Security Violation Count > 0. "
          "Зробіть додатковий знімок `Скриншоти/д4.png` (лише для звірки чисел). Поверніть Mgr-1.",
          "6. **Перевірка 5 (protect):** SRV-1 від Fa0/5 відключіть, Intruder → Fa0/5, `ping 192.168.1.11`; "
          "`show port-security interface fastEthernet 0/5` — Secure-up, лічильник 0. Знімок `Скриншоти/д5.png`. "
          "Поверніть SRV-1, Intruder — на Fa0/22.",
          "7. `copy running-config startup-config`, File → Save. Файл .pkt здається разом зі звітом.", "",
          "## Е. Готово", "",
          "Скажіть мені «скриншоти ЛР2 готові» (+ MAC-адреси) — я вставлю все у звіт і перевірю числа з "
          "д4/д5.", ""]
    return g


def main(nums):
    for n in nums:
        data = L.L1 if n == 1 else L.L2
        cli = L.l1_cli() if n == 1 else L.l2_cli(read_macs(n))
        out = lab_dir(n) / "Готово"
        (out / "CLI").mkdir(parents=True, exist_ok=True)
        (lab_dir(n) / "Скриншоти").mkdir(exist_ok=True)
        for name, cmds in cli.items():
            (out / "CLI" / f"{name}.txt").write_text("\n".join(cmds) + "\n", encoding="utf-8")
        g = guide1(cli) if n == 1 else guide2(cli)
        (out / f"ЛР_{n}_Інструкція_{L.VAR}.md").write_text("\n".join(g), encoding="utf-8")
        rep, missing = build_report(n, data, cli)
        print(f"ЛР{n}: {rep.relative_to(ROOT)} (+ .pdf, CLI/, інструкція)")
        if n == 2 and "<MAC" in "\n".join(cli["2_port_security"]):
            print("  ! MAC-адреси Kasa-2, Kasa-3, ABS-1, SRV-1 ще невідомі — у командах стоять <MAC …>")
        if missing:
            print(f"  ! бракує скриншотів: {', '.join(map(str, missing))} → {lab_dir(n).name}/Скриншоти/")


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or [1, 2])
