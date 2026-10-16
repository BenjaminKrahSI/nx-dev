# -*- coding: utf-8 -*-
"""
NX-Discovery-Journal
--------------------
In NX ausfuehren (Alt+F8 / Datei > Ausfuehren > Journal). Erfasst die ECHTE
Laufzeitumgebung der NX-Session (Startskript/ECTR setzen oft Variablen, die
ausserhalb von NX nicht existieren) und schreibt sie nach
    %USERPROFILE%\\nx_discovery.json
setup.ps1 liest diese Datei und erzeugt daraus die VS-Code-Konfiguration.

Aendert nichts an NX, am Part oder an Dateien ausser der JSON-Datei.
"""
import os
import sys
import json
import glob
import platform
import datetime

import NXOpen

KEEP_PREFIX = ("UGII_", "UGS_", "SPLM_", "UG_", "NX_")


def _stub_root(base):
    """Ordner, der das NXOpen-Stub-Paket enthaelt (fuer extraPaths)."""
    if not base:
        return None
    ugopen = os.path.join(base, "UGOPEN")
    candidates = [os.path.join(ugopen, "pythonStubs")]
    for pattern in ("*", os.path.join("*", "*")):
        candidates += glob.glob(os.path.join(ugopen, pattern))
    for c in candidates:
        if os.path.isfile(os.path.join(c, "NXOpen", "__init__.pyi")) or \
           os.path.isfile(os.path.join(c, "NXOpen.pyi")):
            return c
    return None


def _samples(base):
    if not base:
        return None
    for c in (os.path.join(base, "UGOPEN", "SampleNXOpenApplications", "Python"),
              os.path.join(base, "UGOPEN", "SampleNXOpenApplications")):
        if os.path.isdir(c):
            return c
    return None


def _custom_dirs(env):
    f = env.get("UGII_CUSTOM_DIRECTORY_FILE")
    if not f or not os.path.isfile(f):
        return []
    try:
        with open(f, encoding="utf-8", errors="replace") as fh:
            return [l.strip() for l in fh if l.strip() and not l.strip().startswith("#")]
    except OSError:
        return []


def main():
    lw = NXOpen.Session.GetSession().ListingWindow
    lw.Open()

    env = {k: v for k, v in os.environ.items()
           if k.upper().startswith(KEEP_PREFIX) or "LICENSE" in k.upper()}
    base = env.get("UGII_BASE_DIR") or os.environ.get("UGII_ROOT_DIR", "")
    if base and os.path.basename(os.path.normpath(base)).upper() == "UGII":
        base = os.path.dirname(os.path.normpath(base))

    run_journal = os.path.join(base, "NXBIN", "run_journal.exe") if base else None
    py_dlls = []
    if base:
        for pat in ("python3*.dll", os.path.join("python", "python3*.dll"),
                    os.path.join("*", "python3*.dll")):
            py_dlls += glob.glob(os.path.join(base, "NXBIN", pat))

    info = {
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "python": {
            "version": sys.version,
            "version_short": "%d.%d" % sys.version_info[:2],
            "executable": sys.executable,
            "prefix": sys.prefix,
            "architecture": platform.architecture()[0],
            "sys_path": list(sys.path),
            "dlls": py_dlls,
        },
        "nx": {
            "base_dir": base,
            "run_journal": run_journal if run_journal and os.path.isfile(run_journal) else None,
            "stubs_root": _stub_root(base),
            "samples": _samples(base),
            "user_dir": env.get("UGII_USER_DIR"),
            "site_dir": env.get("UGII_SITE_DIR"),
            "custom_directory_file": env.get("UGII_CUSTOM_DIRECTORY_FILE"),
            "custom_dirs": _custom_dirs(env),
        },
        "env": env,
        "user": {
            "userprofile": os.environ.get("USERPROFILE"),
            "temp": os.environ.get("TEMP"),
        },
    }

    out = os.path.join(os.path.expanduser("~"), "nx_discovery.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=2, ensure_ascii=False)

    w = lw.WriteLine
    w("=== NX Discovery ===")
    w("Python      : %s (%s)" % (info["python"]["version_short"], info["python"]["architecture"]))
    w("NX Basis    : %s" % base)
    w("Stubs       : %s" % info["nx"]["stubs_root"])
    w("Samples     : %s" % info["nx"]["samples"])
    w("run_journal : %s" % info["nx"]["run_journal"])
    w("UGII_USER_DIR: %s" % info["nx"]["user_dir"])
    w("Custom-Dirs : %s" % (", ".join(info["nx"]["custom_dirs"]) or "-"))
    w("")
    w("Geschrieben : %s" % out)
    w("Naechster Schritt: run_setup.cmd im Starter-Ordner ausfuehren.")


if __name__ == "__main__":
    main()
