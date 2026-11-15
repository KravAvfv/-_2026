#!/usr/bin/python3
"""Список / зміна розміру вікон у віртуальному дисплеї (без віконного менеджера).
    ptwin.py list            ptwin.py fit "Packet Tracer" [W H]    ptwin.py geom ID X Y W H"""
import os, sys
from Xlib import display, X
d = display.Display(os.environ.get("DISPLAY", ":77"))
root = d.screen().root


def wins():
    out = []
    for w in root.query_tree().children:
        try:
            a = w.get_attributes()
            if a.map_state != X.IsViewable:
                continue
            g = w.get_geometry()
            name = w.get_wm_name() or ""
            if not name:
                prop = w.get_full_property(d.intern_atom("_NET_WM_NAME"), d.intern_atom("UTF8_STRING"))
                name = prop.value if prop else ""
            if isinstance(name, bytes):
                name = name.decode("utf-8", "replace")
            out.append((w, name, g.x, g.y, g.width, g.height))
        except Exception:
            pass
    return out


a = sys.argv[1:]
if a[0] == "list":
    for w, n, x, y, ww, hh in wins():
        print(hex(w.id), repr(n), x, y, ww, hh)
elif a[0] == "fit":
    W, H = (int(a[2]), int(a[3])) if len(a) > 3 else (1600, 1000)
    for w, n, *_ in wins():
        if a[1] in n:
            w.configure(x=0, y=0, width=W, height=H); d.sync(); print("fit", n)
elif a[0] == "geom":
    w = d.create_resource_object("window", int(a[1], 16))
    w.configure(x=int(a[2]), y=int(a[3]), width=int(a[4]), height=int(a[5])); d.sync()
elif a[0] == "raise":
    w = d.create_resource_object("window", int(a[1], 16)); w.configure(stack_mode=X.Above); d.sync()
elif a[0] == "close":                      # закрити вікно за назвою (WM_DELETE_WINDOW, як кнопка «×»)
    from Xlib.protocol import event
    P, DEL = d.intern_atom("WM_PROTOCOLS"), d.intern_atom("WM_DELETE_WINDOW")
    for w, n, *_ in wins():
        if n == a[1] or (len(a) > 2 and a[2] == "sub" and a[1] in n):
            w.send_event(event.ClientMessage(window=w, client_type=P, data=(32, [DEL, X.CurrentTime, 0, 0, 0])))
            d.sync(); print("closed", n)
elif a[0] == "place":                      # place NAME X Y W H — за назвою
    for w, n, *_ in wins():
        if n == a[1]:
            w.configure(x=int(a[2]), y=int(a[3]), width=int(a[4]), height=int(a[5]), stack_mode=X.Above); d.sync()
