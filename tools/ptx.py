#!/usr/bin/python3
"""Мінімальне керування застосунком у віртуальному X-дисплеї (Xvfb) через розширення XTEST — для Cisco Packet
Tracer, який не має CLI-інтерфейсу побудови топології. Використання (системний python3 з python-xlib):

    DISPLAY=:77 tools/ptx.py shot out.png              # знімок усього екрана
    tools/ptx.py click X Y | dclick X Y | rclick X Y   # клацання
    tools/ptx.py drag X1 Y1 X2 Y2                      # перетягування лівою кнопкою
    tools/ptx.py type "текст"                          # набір ASCII-тексту (\\n — Enter)
    tools/ptx.py key Return | ctrl+s | alt+F4 ...      # комбінація клавіш
    tools/ptx.py typefile file.txt [delay]             # набір файлу рядок за рядком (для CLI IOS)
"""
import os
import subprocess
import sys
import time

from Xlib import X, XK, display
from Xlib.ext import xtest

D = display.Display(os.environ.get("DISPLAY", ":77"))
SHIFTED = '~!@#$%^&*()_+{}|:"<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ'
NAMES = {" ": "space", "\n": "Return", "\t": "Tab", "-": "minus", "=": "equal", "[": "bracketleft",
         "]": "bracketright", ";": "semicolon", "'": "apostrophe", ",": "comma", ".": "period", "/": "slash",
         "\\": "backslash", "`": "grave", "~": "asciitilde", "!": "exclam", "@": "at", "#": "numbersign",
         "$": "dollar", "%": "percent", "^": "asciicircum", "&": "ampersand", "*": "asterisk", "(": "parenleft",
         ")": "parenright", "_": "underscore", "+": "plus", "{": "braceleft", "}": "braceright", "|": "bar",
         ":": "colon", '"': "quotedbl", "<": "less", ">": "greater", "?": "question"}


def kc(name):
    code = D.keysym_to_keycode(XK.string_to_keysym(name))
    if not code:
        raise SystemExit(f"no keycode for {name}")
    return code


def press(code, down=True):
    xtest.fake_input(D, X.KeyPress if down else X.KeyRelease, code)


def move(x, y):
    xtest.fake_input(D, X.MotionNotify, x=int(x), y=int(y))
    D.sync()
    time.sleep(0.05)


def button(b, down):
    xtest.fake_input(D, X.ButtonPress if down else X.ButtonRelease, b)
    D.sync()


def click(x, y, b=1, n=1):
    move(x, y)
    for _ in range(n):
        button(b, True); time.sleep(0.04); button(b, False); time.sleep(0.08)
    D.sync()


def drag(x1, y1, x2, y2):
    move(x1, y1); button(1, True); time.sleep(0.15)
    for i in range(1, 11):
        move(x1 + (x2 - x1) * i / 10, y1 + (y2 - y1) * i / 10)
    time.sleep(0.15); button(1, False); D.sync()


_SPARE = []


def spare_code():
    """Вільний keycode для тимчасового призначення Unicode-символу (кирилиця тощо)."""
    if not _SPARE:
        lo, hi = D.display.info.min_keycode, D.display.info.max_keycode
        m = D.get_keyboard_mapping(lo, hi - lo + 1)
        _SPARE.extend(lo + i for i, row in enumerate(m) if not any(row))
    return _SPARE[-1]


def type_unicode(ch, delay=0.02):
    code = spare_code()
    sym = 0x01000000 | ord(ch)
    D.change_keyboard_mapping(code, [(sym, sym)])
    D.sync(); time.sleep(0.05)
    press(code); press(code, False); D.sync()
    time.sleep(delay)


def type_char(ch, delay=0.012):
    if ord(ch) > 126:
        return type_unicode(ch)
    name = NAMES.get(ch, ch)
    shift = ch in SHIFTED
    code = kc(name)
    if shift:
        press(kc("Shift_L"))
    press(code); press(code, False)
    if shift:
        press(kc("Shift_L"), False)
    D.sync()
    time.sleep(delay)


def type_text(s, delay=0.012):
    for ch in s:
        type_char(ch, delay)


def combo(spec):
    keys = [{"ctrl": "Control_L", "alt": "Alt_L", "shift": "Shift_L", "enter": "Return", "esc": "Escape"}
            .get(k.lower(), k) for k in spec.split("+")]
    codes = [kc(k) for k in keys]
    for c in codes:
        press(c)
    for c in reversed(codes):
        press(c, False)
    D.sync()


def shot(path):
    subprocess.run(["import", "-display", os.environ.get("DISPLAY", ":77"), "-window", "root", path], check=True)


def main(a):
    cmd = a[0]
    if cmd == "shot":
        shot(a[1])
    elif cmd in ("click", "dclick", "rclick"):
        click(float(a[1]), float(a[2]), b=3 if cmd == "rclick" else 1, n=2 if cmd == "dclick" else 1)
    elif cmd == "move":
        move(float(a[1]), float(a[2]))
    elif cmd == "drag":
        drag(*map(float, a[1:5]))
    elif cmd == "type":
        type_text(a[1].replace("\\n", "\n"))
    elif cmd == "key":
        for k in a[1:]:
            combo(k); time.sleep(0.1)
    elif cmd == "typefile":
        delay = float(a[2]) if len(a) > 2 else 0.25
        for line in open(a[1], encoding="ascii").read().splitlines():
            type_text(line + "\n")
            time.sleep(delay)
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
