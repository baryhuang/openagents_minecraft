#!/usr/bin/env python3
"""Simple X11 mouse click tool using python-xlib"""
import sys
from Xlib import X, display, ext
from Xlib.ext import xtest
import time

def click(x, y, button=1):
    d = display.Display()
    screen = d.screen()
    root = screen.root

    # Move pointer
    root.warp_pointer(x, y)
    d.sync()
    time.sleep(0.1)

    # Click
    xtest.fake_input(d, X.ButtonPress, button, X.CurrentTime)
    d.sync()
    time.sleep(0.05)
    xtest.fake_input(d, X.ButtonRelease, button, X.CurrentTime)
    d.sync()

    print(f"Clicked at ({x}, {y})")

if __name__ == "__main__":
    x = int(sys.argv[1])
    y = int(sys.argv[2])
    click(x, y)
