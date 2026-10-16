# -*- coding: utf-8 -*-
"""VS-Code-Task: .nxdev/nx_dev.log live verfolgen (Strg+C beendet)."""
import os
import time
from _common import state_file

log = state_file("nx_dev.log")
if not os.path.exists(log):
    open(log, "a").close()
print("Verfolge %s  (Strg+C beendet)" % log, flush=True)
with open(log, encoding="utf-8", errors="replace") as fh:
    lines = fh.readlines()
    print("".join(lines[-50:]), end="", flush=True)
    try:
        while True:
            pos = fh.tell()
            line = fh.readline()
            if line:
                print(line, end="", flush=True)
                continue
            if os.path.getsize(log) < pos:      # Log wurde geleert
                fh.seek(0)
            time.sleep(0.4)
    except KeyboardInterrupt:
        pass
