# -*- coding: utf-8 -*-
"""VS-Code-Task: Debug-Modus des NX-Loaders an/aus."""
import os
from _common import state_file

flag = state_file("debug.flag")
if os.path.exists(flag):
    os.remove(flag)
    print("Debug-Modus AUS")
else:
    open(flag, "w").close()
    print("Debug-Modus AN: naechster Lauf in NX wartet auf 'NX: an laufende Session anhaengen' (F5).")
