# -*- coding: utf-8 -*-
"""
VS-Code-Task: Datei per run_journal.exe im Batch ausfuehren.
Laeuft ueber nx/nx_batch_bootstrap.py (src/ auf sys.path); PYTHONPATH bleibt
unangetastet, weil NX ihn selbst setzt. Lizenzvariablen aus .nxdev/nx_env.json.
Batch = keine GUI, keine ECTR-Verbindung, Parts nur per Dateipfad.
"""
import json
import os
import subprocess
import sys
from _common import ROOT, state_file

if len(sys.argv) < 2:
    sys.exit("Aufruf: run_batch.py <ziel.py> [args]")
with open(state_file("paths.json"), encoding="utf-8-sig") as fh:
    paths = json.load(fh)
rj = paths.get("run_journal")
if not rj or not os.path.isfile(rj):
    sys.exit("run_journal.exe nicht gefunden: %s" % rj)

env = dict(os.environ)
env_file = state_file("nx_env.json")
if os.path.isfile(env_file):
    with open(env_file, encoding="utf-8-sig") as fh:
        for k, v in json.load(fh).items():
            if k.upper() != "PYTHONPATH":
                env[k] = v

boot = os.path.join(ROOT, "nx", "nx_batch_bootstrap.py")
cmd = [rj, boot, "-args", os.path.abspath(sys.argv[1])] + sys.argv[2:]
print("run_journal: %s" % sys.argv[1], flush=True)
sys.exit(subprocess.call(cmd, env=env))
