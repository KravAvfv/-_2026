#!/usr/bin/python3
"""Високорівневі дії в Cisco Packet Tracer 9 (Xvfb :77, вікно PT 1600×1000) поверх tools/ptx.py і tools/ptwin.py.
Координати палітр і вкладок виміряні на знімках цього дисплея. Імпортується з системного python3."""
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("DISPLAY", ":77")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ptx  # noqa: E402

TOOLS = Path(__file__).resolve().parent
SELECT = (18, 83)                    # інструмент «Select»
DEV_GEOM = (300, 60, 900, 700)       # стандартне місце вікна пристрою
TAB_X = {"Physical": 352, "Config": 428, "Desktop": 505, "CLI": 495, "Programming": 618, "Attributes": 726}


def wins():
    out = subprocess.run([str(TOOLS / "ptwin.py"), "list"], capture_output=True, text=True).stdout
    return [line.split("'")[1] for line in out.splitlines() if "'" in line]


def wait_win(name, timeout=8.0, gone=False):
    t = time.time()
    while time.time() - t < timeout:
        present = name in wins()
        if present != gone:
            return True
        time.sleep(0.2)
    raise RuntimeError(f"window {name!r} {'still open' if gone else 'not found'}; have {wins()}")


def place(name, geom=DEV_GEOM):
    subprocess.run([str(TOOLS / "ptwin.py"), "place", name, *map(str, geom)], check=True)
    time.sleep(0.4)


def close(name):
    subprocess.run([str(TOOLS / "ptwin.py"), "close", name], check=True, capture_output=True)
    wait_win(name, gone=True)


def pixel(x, y):
    from Xlib import X
    img = ptx.D.screen().root.get_image(x, y, 1, 1, X.ZPixmap, 0xFFFFFFFF)
    b, g, r = img.data[0], img.data[1], img.data[2]
    return r, g, b


def ensure_toolbar():
    """Інколи PT ховає другу панель інструментів (Logical-смуга піднімається на y≈84) — увімкнути знову."""
    r, g, b = pixel(700, 88)
    if r > 200 and g > 180 and b < 160:                  # жовта смуга Logical на місці панелі
        for _ in range(2):
            ptx.click(160, 11); time.sleep(0.5); ptx.click(200, 66); time.sleep(0.5); ptx.click(545, 94)
            time.sleep(0.8)
            r, g, b = pixel(700, 88)
            if not (r > 200 and g > 180 and b < 160):
                break


def select_tool():
    ensure_toolbar()
    ptx.combo("Escape"); time.sleep(0.1)
    ptx.click(*SELECT); time.sleep(0.2)


def open_dev(xy, name, geom=DEV_GEOM):
    """Відкрити вікно пристрою кліком у робочій області."""
    if name in wins():
        place(name, geom)
        return
    select_tool()
    ptx.click(*xy)
    wait_win(name)
    time.sleep(0.4)
    place(name, geom)


def tab(name, geom=DEV_GEOM):
    x0 = geom[0] - 300
    ptx.click(TAB_X[name] + x0, 89 + geom[1] - 60)
    time.sleep(0.7)


def rename(xy, old, new):
    open_dev(xy, old)
    tab("Config")
    ptx.click(870, 194); time.sleep(0.2)
    ptx.combo("ctrl+a"); ptx.type_text(new + "\n"); time.sleep(0.5)
    wait_win(new)
    close(new)


def shot(path):
    ptx.shot(str(path))


def cli_type(text, line_delay=0.35):
    """Набрати команди IOS у вже відкритій вкладці CLI (курсор у полі консолі)."""
    for line in text.splitlines():
        ptx.type_text(line + "\n", delay=0.008)
        time.sleep(line_delay)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "rename":
        x, y, old, new = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
        rename((x, y), old, new)
    elif cmd == "open":
        open_dev((int(sys.argv[2]), int(sys.argv[3])), sys.argv[4])
    elif cmd == "tab":
        tab(sys.argv[2])
    elif cmd == "close":
        close(sys.argv[2])
    elif cmd == "select":
        select_tool()


def prompt(xy, name, geom=DEV_GEOM, icon=(910, 170)):
    """Відкрити Desktop → Command Prompt пристрою (якщо вже відкритий — перевідкрити)."""
    open_dev(xy, name, geom)
    tab("Desktop", geom)
    dx, dy = geom[0] - 300, geom[1] - 60
    ptx.click(1158 + dx, 127 + dy); time.sleep(0.5)      # «X» відкритої підпрограми (якщо є)
    ptx.click(icon[0] + dx, icon[1] + dy); time.sleep(1.2)   # іконка Command Prompt (планшет/сервер: 742,180)
    ptx.click(750 + dx, 600 + dy); time.sleep(0.2)


def pc_cmd(xy, name, cmds, wait=1.0, keep=False, geom=DEV_GEOM, icon=(910, 170)):
    prompt(xy, name, geom, icon)
    for c in cmds:
        ptx.type_text(c + "\n", delay=0.01)
        time.sleep(wait)
    if not keep:
        close(name)


def note(xy, text):
    """Інструмент Place Note: клік у робочій області, фокус на редактор-підказку, набір тексту, фіксація."""
    from Xlib import X
    ptx.click(174, 87); time.sleep(0.5)
    ptx.click(*xy); time.sleep(0.8)
    for w in ptx.D.screen().root.query_tree().children:
        a, g = w.get_attributes(), w.get_geometry()
        if a.map_state == X.IsViewable and g.height < 40 and g.width < 400:
            w.set_input_focus(X.RevertToParent, X.CurrentTime); ptx.D.sync()
    time.sleep(0.3)
    ptx.type_text(text); time.sleep(0.3)
    ptx.click(*SELECT); time.sleep(0.4)                  # клік поза редактором фіксує примітку
    hide_popups()


def hide_popups():
    """Порожні редактори приміток (150×25) лишаються видимими без віконного менеджера — прибрати за екран."""
    from Xlib import X
    for w in ptx.D.screen().root.query_tree().children:
        try:
            g = w.get_geometry()
            if w.get_attributes().map_state == X.IsViewable and g.width == 150 and g.height == 25:
                w.configure(x=3000, y=3000); ptx.D.sync()
        except Exception:
            pass


def focus(name):
    """Передати клавіатурний фокус вікну верхнього рівня з цією назвою (немає віконного менеджера)."""
    from Xlib import X
    for w in ptx.D.screen().root.query_tree().children:
        try:
            if w.get_attributes().map_state == X.IsViewable and (w.get_wm_name() or "") == name:
                w.configure(stack_mode=X.Above)
                w.set_input_focus(X.RevertToParent, X.CurrentTime); ptx.D.sync(); return True
        except Exception:
            pass
    return False


def save_as(path):
    """File → Save As: повний шлях у поле File name, Enter."""
    ptx.click(20, 11); time.sleep(0.5)
    ptx.click(70, 178); time.sleep(1.5)
    wait_win("Save File")
    focus("Save File"); time.sleep(0.3)
    ptx.combo("ctrl+a"); ptx.type_text(str(path) + "\n"); time.sleep(2.5)


def save():
    ptx.click(20, 11); time.sleep(0.5)
    ptx.click(50, 150); time.sleep(2.0)


def cli(xy, name, text, geom=DEV_GEOM, first=False, line_delay=0.3, keep=True):
    """Вкладка CLI мережевого пристрою: клік у консоль, (Enter для старту), набір команд."""
    open_dev(xy, name, geom)
    tab("CLI", geom)
    dx, dy = geom[0] - 300, geom[1] - 60
    ptx.click(750 + dx, 500 + dy); time.sleep(0.3)
    if first:
        ptx.type_text("\n"); time.sleep(1.0)
    cli_type(text, line_delay)
    if not keep:
        close(name)


def set_gateway(xy, name, gw):
    """Config → Global Settings → Default Gateway (команда ipconfig у PT 9 ігнорує 3-й аргумент)."""
    open_dev(xy, name)
    tab("Config")
    ptx.click(408, 156); time.sleep(0.4)                 # GLOBAL → Settings
    ptx.click(897, 369); time.sleep(0.2)
    ptx.combo("ctrl+a"); ptx.type_text(gw + "\t"); time.sleep(0.3)
    close(name)


def delete_link(pt):
    select_tool(); ptx.click(95, 87); time.sleep(0.4); ptx.click(*pt); time.sleep(0.6); select_tool()


def link(a, a_menu, b, b_menu):
    """Кабель Copper Straight-Through: клік a → пункт меню a_menu → клік b → пункт меню b_menu."""
    select_tool()
    ptx.click(166, 890); time.sleep(0.4); ptx.click(420, 885); time.sleep(0.4)
    ptx.click(*a); time.sleep(0.7); ptx.click(*a_menu); time.sleep(0.5)
    ptx.click(*b); time.sleep(0.9); ptx.click(*b_menu); time.sleep(2.5)
    select_tool()


def ip_gui(ip, mask, gw):
    """Заповнити відкриту форму Desktop → IP Configuration (Static)."""
    for y, v in ((223, ip), (257, mask), (291, gw)):
        ptx.click(880, y); time.sleep(0.2); ptx.combo("ctrl+a"); ptx.type_text(v + "\t"); time.sleep(0.4)
