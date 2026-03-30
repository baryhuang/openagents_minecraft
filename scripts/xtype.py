#!/usr/bin/env python3
"""X11 keyboard input using python-xlib"""
import sys
import time
from Xlib import X, XK, display
from Xlib.ext import xtest

def type_key(d, keyname):
    keysym = XK.string_to_keysym(keyname)
    keycode = d.keysym_to_keycode(keysym)
    if keycode == 0:
        print(f"Unknown key: {keyname}")
        return
    xtest.fake_input(d, X.KeyPress, keycode)
    d.sync()
    time.sleep(0.02)
    xtest.fake_input(d, X.KeyRelease, keycode)
    d.sync()
    time.sleep(0.05)

def type_string(d, s):
    for c in s:
        if c == ':':
            # Shift + semicolon
            keysym = XK.string_to_keysym('colon')
            keycode = d.keysym_to_keycode(keysym)
            shift_keycode = d.keysym_to_keycode(XK.string_to_keysym('Shift_L'))
            xtest.fake_input(d, X.KeyPress, shift_keycode)
            d.sync()
            xtest.fake_input(d, X.KeyPress, keycode)
            d.sync()
            time.sleep(0.02)
            xtest.fake_input(d, X.KeyRelease, keycode)
            d.sync()
            xtest.fake_input(d, X.KeyRelease, shift_keycode)
            d.sync()
        elif c == '/':
            keysym = XK.string_to_keysym('slash')
            keycode = d.keysym_to_keycode(keysym)
            xtest.fake_input(d, X.KeyPress, keycode)
            d.sync()
            time.sleep(0.02)
            xtest.fake_input(d, X.KeyRelease, keycode)
            d.sync()
        elif c == '.':
            keysym = XK.string_to_keysym('period')
            keycode = d.keysym_to_keycode(keysym)
            xtest.fake_input(d, X.KeyPress, keycode)
            d.sync()
            time.sleep(0.02)
            xtest.fake_input(d, X.KeyRelease, keycode)
            d.sync()
        elif c == ' ':
            type_key(d, 'space')
        elif c.isupper():
            shift = d.keysym_to_keycode(XK.string_to_keysym('Shift_L'))
            xtest.fake_input(d, X.KeyPress, shift)
            d.sync()
            type_key(d, c.lower())
            xtest.fake_input(d, X.KeyRelease, shift)
            d.sync()
        else:
            type_key(d, c)
        time.sleep(0.03)

if __name__ == "__main__":
    d = display.Display()
    cmd = sys.argv[1]
    if cmd == "key":
        type_key(d, sys.argv[2])
        print(f"Pressed key: {sys.argv[2]}")
    elif cmd == "type":
        text = sys.argv[2]
        type_string(d, text)
        print(f"Typed: {text}")
    elif cmd == "click":
        from Xlib.ext import xtest as xt
        x, y = int(sys.argv[2]), int(sys.argv[3])
        root = d.screen().root
        root.warp_pointer(x, y)
        d.sync()
        time.sleep(0.1)
        xt.fake_input(d, X.ButtonPress, 1)
        d.sync()
        time.sleep(0.05)
        xt.fake_input(d, X.ButtonRelease, 1)
        d.sync()
        print(f"Clicked ({x}, {y})")
