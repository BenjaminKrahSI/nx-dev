# -*- coding: utf-8 -*-
# (Hinweis: Docstring als raw string wegen Windows-Pfaden)
r"""
Batch-Bootstrap fuer run_journal.exe (generiert von setup.ps1)
Aufruf: run_journal.exe nx_batch_bootstrap.py -args <ziel.py> [weitere Argumente]

Ergaenzt sys.path um src\ und den Ordner der Zieldatei, OHNE PYTHONPATH
anzufassen - den setzt NX selbst (ugii_env_ug.dat -> nxbin\python, Python311.zip),
ein eigener Wert wuerde import NXOpen brechen.
"""
import os
import sys
import runpy
import traceback

DEV_ROOT = r"{{DEV_ROOT}}"
sys.dont_write_bytecode = True


def main():
    args = list(sys.argv[1:])
    if not args:
        print("Aufruf: run_journal nx_batch_bootstrap.py -args <ziel.py> [args]")
        return 2
    target = os.path.abspath(args[0])
    for p in (os.path.join(DEV_ROOT, "src"), os.path.dirname(target)):
        if p not in sys.path:
            sys.path.insert(0, p)
    sys.argv = [target] + args[1:]
    try:
        runpy.run_path(target, run_name="__main__")
    except SystemExit as e:
        return e.code or 0
    except Exception:
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    rc = main()
    if rc:
        sys.exit(rc)
