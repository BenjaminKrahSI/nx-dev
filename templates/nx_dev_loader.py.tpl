# -*- coding: utf-8 -*-
"""
NX Dev Loader  (generiert von setup.ps1 - Aenderungen gehen bei -Force verloren)
-------------------------------------------------------------------------------
Fuehrt die Datei aus, die in VS Code per Task "NX: aktuelle Datei als Ziel setzen"
markiert wurde - IMMER mit frischem Code:

* Module aus dem Dev-Ordner und dem Ordner der Zieldatei werden vor jedem Lauf
  aus sys.modules entfernt (das eingebettete NX-Python lebt die ganze Session).
* Der Ordner der Zieldatei kommt temporaer auf sys.path (Geschwister-Importe
  funktionieren wie bei einem normalen Skript).
* Existiert .nxdev\\debug.flag, wartet der Loader auf den VS-Code-Debugger.
* Fehler landen im Listing Window und in .nxdev\\nx_dev.log.
"""
import os
import sys
import time
import runpy
import importlib
import traceback

import NXOpen

DEV_ROOT = r"{{DEV_ROOT}}"
DEBUG_PYTHON = r"{{PY_EXE}}"
DEBUG_PORT = 5678

STATE = os.path.join(DEV_ROOT, ".nxdev")
SRC = os.path.join(DEV_ROOT, "src")
DEBUGPY_DIR = os.path.join(DEV_ROOT, "_debugpy")
LOG_FILE = os.path.join(STATE, "nx_dev.log")

# Keine .pyc fuer Dev-Code: sonst kann eine Aenderung gleicher Groesse in derselben
# Sekunde vom alten Bytecode verdeckt werden.
sys.dont_write_bytecode = True


def _log(level, text):
    try:
        os.makedirs(STATE, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write("%s %-7s loader: %s\n" % (time.strftime("%H:%M:%S"), level, text))
    except OSError:
        pass


def _lw(text):
    lw = NXOpen.Session.GetSession().ListingWindow
    lw.Open()
    lw.WriteLine(text)


def _norm(p):
    return os.path.normcase(os.path.abspath(p))


def _purge(roots):
    roots = [_norm(r) + os.sep for r in roots if r]
    keep = _norm(DEBUGPY_DIR) + os.sep
    removed = 0
    for name, mod in list(sys.modules.items()):
        if name == "__main__":
            continue
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        nf = _norm(f)
        if nf.startswith(keep):
            continue
        if any(nf.startswith(r) for r in roots):
            del sys.modules[name]
            removed += 1
    return removed


def _maybe_debug():
    if not os.path.exists(os.path.join(STATE, "debug.flag")):
        return
    if not os.path.isdir(DEBUGPY_DIR):
        _lw("debug.flag gesetzt, aber _debugpy fehlt -> setup.ps1 -InstallDebugpy")
        return
    if DEBUGPY_DIR not in sys.path:
        sys.path.insert(0, DEBUGPY_DIR)
    import debugpy
    if not getattr(sys, "_nxdev_debug_listening", False):
        if DEBUG_PYTHON and os.path.isfile(DEBUG_PYTHON):
            # sys.executable ist hier ugraf.exe - der Adapter braucht ein echtes python.exe
            debugpy.configure(python=DEBUG_PYTHON)
        debugpy.listen(("127.0.0.1", DEBUG_PORT))
        sys._nxdev_debug_listening = True
        _log("INFO", "debugpy lauscht auf Port %d" % DEBUG_PORT)
    if not debugpy.is_client_connected():
        _log("INFO", "warte auf VS Code Attach (NX ist bis dahin blockiert) ...")
        debugpy.wait_for_client()


def main():
    target_file = os.path.join(STATE, "target.txt")
    try:
        with open(target_file, encoding="utf-8-sig") as fh:
            target = fh.read().strip()
    except OSError:
        _lw("Kein Ziel gesetzt. In VS Code: Task 'NX: aktuelle Datei als Ziel setzen'.")
        return
    if not os.path.isfile(target):
        _lw("Ziel nicht gefunden: %s" % target)
        return

    tdir = os.path.dirname(os.path.abspath(target))
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    n = _purge([DEV_ROOT, tdir])
    importlib.invalidate_caches()

    try:
        _maybe_debug()
    except Exception:
        _lw("Debugger-Start fehlgeschlagen:\n" + traceback.format_exc())

    added = tdir not in sys.path
    if added:
        sys.path.insert(0, tdir)
    old_argv = getattr(sys, "argv", None)
    sys.argv = [target]
    t0 = time.time()
    _log("INFO", "Start %s (%d Module neu geladen)" % (os.path.basename(target), n))
    try:
        runpy.run_path(target, run_name="__main__")
        _log("INFO", "OK  %s (%.2f s)" % (os.path.basename(target), time.time() - t0))
    except SystemExit:
        pass
    except Exception:
        tb = traceback.format_exc()
        _log("ERROR", tb)
        _lw(tb)
    finally:
        if old_argv is not None:
            sys.argv = old_argv
        if added:
            try:
                sys.path.remove(tdir)
            except ValueError:
                pass


if __name__ == "__main__":
    main()
