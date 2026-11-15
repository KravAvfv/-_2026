"""DFD рівнів 0 і 1 ПР2 (варіант 8, корпоративна мережа): нотація Йордона — Де Марко, як у прикладі брифу
(процес — коло/еліпс, сховище — циліндр, зовнішня сутність — прямокутник); пунктирні рамки — зони довіри,
потоки, що їх перетинають, перетинають межі довіри TB1–TB4. Одна побудова → PNG для звіту + .drawio."""
import sys
from pathlib import Path
from xml.sax.saxutils import escape  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tsfig import TFig  # noqa: E402
from drawio_lib import hlabel, style  # noqa: E402


class DFig(TFig):
    def ellipse(self, cx, cy, w, h, lines, dash=None, bold_first=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{w / 2}" ry="{h / 2}" fill="#fff" stroke="#000" '
                        f'stroke-width="2"{d}/>')
        self.dw.vertex(cx - w / 2, cy - h / 2, w, h, hlabel(lines),
                       style(ellipse=1, html=1, whiteSpace="wrap", fillColor="#FFFFFF", strokeColor="#000000",
                             strokeWidth=2, dashed=1 if dash else None, **self._font()))
        tmp = self.dw
        from drawio_lib import Drawio
        self.dw = Drawio("_")
        self.text(cx, cy, lines)
        self.dw = tmp

    def cyl(self, cx, cy, w, h, lines):
        x, y, k = cx - w / 2, cy - h / 2, 14
        self.out.append(f'<path d="M{x},{y + k} L{x},{y + h - k} A{w / 2},{k} 0 0 0 {x + w},{y + h - k} '
                        f'L{x + w},{y + k} A{w / 2},{k} 0 0 0 {x},{y + k} Z" fill="#fff" stroke="#000" '
                        'stroke-width="2"/>')
        self.out.append(f'<path d="M{x},{y + k} A{w / 2},{k} 0 0 0 {x + w},{y + k}" fill="none" stroke="#000" '
                        'stroke-width="2"/>')
        self.dw.vertex(x, y, w, h, hlabel(lines),
                       style(shape="cylinder3", boundedLbl=1, size=k, html=1, whiteSpace="wrap", fillColor="#FFFFFF",
                             strokeColor="#000000", strokeWidth=2, **self._font()))
        tmp = self.dw
        from drawio_lib import Drawio
        self.dw = Drawio("_")
        self.text(cx, cy + k / 2, lines)
        self.dw = tmp

    def tag(self, x, y, t):
        """Позначка межі довіри (жирний текст на білому тлі)."""
        self.text(x, y, t, bold=True, bg=True)


DASH = "14 8"


def dfd0(base):
    f = DFig(2300, 1290, fpx=33, name="DFD рівня 0")
    # зони довіри
    f.frame(15, 15, 985, 1260, "Зони користувачів VLAN 10 / 20 / 30", dash=DASH)
    f.frame(1040, 15, 600, 455, "Серверна зона VLAN 99", dash=DASH)
    f.frame(1040, 500, 840, 775, "Зона безпеки й керування", dash=DASH, bottom=True)
    f.frame(1920, 15, 365, 1260, "Інтернет", dash=DASH)
    for y in (475, 885):                                   # межі між VLAN відділів
        f.line([(15, y), (1000, y)], dash=DASH, head=False)
    lanes = [(270, "Е1. Відділ", "кадрів", ["3. Обробка", "кадрових", "даних"], ["D2. Кадрова", "БД"],
              ["кадрові", "дані"]),
             (680, "Е2. Фінан-", "совий відділ", ["4. Обробка", "фінансових", "операцій"], ["D3. Фінансова", "БД"],
              ["платежі"]),
             (1090, "Е3. Адміні-", "страція", ["5. Документо-", "обіг", "адміністрації"], ["D4. Файловий", "ресурс"],
              ["розпоря-", "дження"])]
    for i, (y, a, b, proc, store, lab) in enumerate(lanes):
        f.box(130, y, 225, 120, [a, b])
        f.ellipse(560, y, 270, 190, proc)
        f.cyl(880, y, 226, 130, store)
        f.line([(240, y), (425, y)], lab, (332, y))
        f.line([(695, y), (767, y)], both=True)
        top = y - 60
        cy = 95 if i == 0 else y - 160                       # канал потоку облікових даних до процесу 1
        f.line([(130, top), (130, cy), (1020, cy), (1020, 300), (1100, 300)], head=(i == 0))
        f.text(560 if i == 0 else 470, cy, "облікові дані", bg=True)
    f.tag(930, 475, "TB2"); f.tag(930, 885, "TB2")
    # серверна зона
    f.ellipse(1250, 300, 300, 190, ["1. Автенти-", "фікація та", "авторизація"])
    f.cyl(1520, 300, 200, 130, ["D1. Каталог", "AD"])
    f.line([(1400, 300), (1420, 300)], both=True)
    f.tag(1040, 150, "TB3")
    # зона безпеки
    f.ellipse(1250, 760, 300, 210, ["2. Контроль", "міжсегмент-", "ного доступу"])
    f.line([(1250, 395), (1250, 655)], ["квиток", "Kerberos"], (1250, 560))
    f.cyl(1600, 580, 210, 120, ["D6. Правила", "ACL і МЕ"])
    f.line([(1495, 580), (1345, 580), (1345, 678)])
    f.text(1425, 545, "політика")
    f.line([(560, 680 + 95), (560, 830), (1060, 830), (1060, 780), (1102, 780)], ["платіжні", "доручення"], (850, 830))
    f.ellipse(1250, 1130, 300, 190, ["6. Моніторинг", "і журна-", "лювання"])
    f.line([(1250, 865), (1250, 1035)], ["відхилені", "пакети"], (1250, 950))
    f.cyl(1560, 1130, 200, 120, ["D5. Журнал", "подій"])
    f.line([(1400, 1130), (1460, 1130)])
    f.box(1760, 1010, 220, 120, ["Е4. Систем-", "ний адмін."])
    f.line([(1330, 1052), (1330, 1010), (1650, 1010)], "тривоги", (1490, 1010))
    f.line([(1820, 950), (1820, 580), (1705, 580)], ["правила", "(SSH)"], (1820, 800))
    f.tag(1760, 1110, "TB4")
    # Інтернет
    f.box(2100, 700, 260, 120, ["Е5. Банк"])
    f.box(2100, 880, 260, 120, ["Е6. Інтернет"])
    f.line([(1395, 715), (2970 / 1.5, 715), (1970, 715)], None)
    f.text(1590, 680, "платежі (TLS)", bg=True)
    f.line([(1398, 800), (1600, 800), (1600, 880), (1970, 880)], None)
    f.text(1680, 880, "запити (NAT)", bg=True)
    f.tag(1900, 640, "TB1")
    return f.save(base, orientation="landscape")


def dfd1(base):
    f = DFig(2300, 1180, fpx=33, name="DFD рівня 1: процес 2")
    f.frame(330, 15, 1610, 1150, "Процес 2. Контроль міжсегментного доступу (Firewall, комутатор ядра)", dash=DASH)
    Y = 470
    f.box(150, Y, 260, 170, ["Е1–Е3. Робочі", "станції", "VLAN 10/20/30"])
    f.ellipse(530, Y, 266, 210, ["2.1. Прийняти", "кадр, визна-", "чити VLAN"])
    f.ellipse(930, Y, 266, 210, ["2.2. Маршру-", "тизувати між", "VLAN (SVI)"])
    f.ellipse(1330, Y, 266, 210, ["2.3. Перевір-", "ити ACL між-", "сегментів"])
    f.ellipse(1760, Y, 266, 210, ["2.4. Фільтру-", "вати, NAT", "(МЕ)"])
    f.box(2155, Y, 250, 170, ["Е5, Е6.", "Банк,", "Інтернет"])
    f.line([(280, Y), (405, Y)], "кадри", (342, Y))
    f.line([(655, Y), (805, Y)], ["802.1Q-", "кадри"], (730, Y))
    f.line([(1055, Y), (1205, Y)], ["пакет", "до VLAN"], (1130, Y))
    f.line([(1455, Y), (1635, Y)], ["трафік", "назовні"], (1545, Y))
    f.line([(1885, Y), (2030, Y)], ["дозво-", "лений"], (1957, Y))
    f.cyl(1545, 140, 270, 120, ["D6. Правила", "ACL і МЕ"])
    f.line([(1420, 200), (1420, 393)], ["правила", "ACL"], (1420, 300))
    f.line([(1670, 200), (1670, 393)], ["політика", "МЕ"], (1670, 300))
    f.box(2155, 140, 250, 120, ["Е4. Систем-", "ний адмін."])
    f.line([(2030, 140), (1680, 140)], ["зміна правил", "(SSH)"], (1855, 140))
    f.ellipse(165, 860, 290, 200, ["1. Автенти-", "фікація", "(DFD-0)"], dash="10 6")
    f.line([(1250, 562), (1250, 860), (312, 860)], "запит до AD", (760, 860))
    f.ellipse(1545, 860, 250, 190, ["2.5. Зареєст-", "рувати", "подію"])
    f.line([(1410, 552), (1410, 820), (1428, 820)], ["відхилені", "пакети"], (1410, 690))
    f.line([(1760, 570), (1760, 860), (1670, 860)], ["відхилені", "з’єднання"], (1760, 720))
    f.cyl(2155, 860, 250, 120, ["D5. Журнал", "подій"])
    f.line([(1670, 900), (1820, 900), (1820, 900), (2030, 900)], ["записи"], (1930, 900))
    return f.save(base, orientation="landscape")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "diagrams"
    dfd0(out / "02_dfd0")
    dfd1(out / "03_dfd1")
