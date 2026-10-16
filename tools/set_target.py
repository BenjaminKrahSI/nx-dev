# -*- coding: utf-8 -*-
"""VS-Code-Task: markiert die aktuelle Datei als Ziel fuer den NX-Loader."""
import os
import sys
from _common import state_file

if len(sys.argv) < 2 or not sys.argv[1].lower().endswith(".py"):
    print("Keine .py-Datei: %s" % (sys.argv[1] if len(sys.argv) > 1 else "-"))
    sys.exit(1)
target = os.path.abspath(sys.argv[1])
with open(state_file("target.txt"), "w", encoding="utf-8") as fh:
    fh.write(target)
print("NX-Ziel gesetzt: %s" % target)
print("-> in NX: Menue > NX Dev > Ziel aus VS Code ausfuehren")
