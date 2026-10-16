# -*- coding: utf-8 -*-
"""
NXOpen VS Code Setup (Python-Variante - kein cmd/PowerShell noetig)

Aufruf (im Starter-Ordner):
    py setup.py
    py setup.py --extra "D:\\Uebungen" "D:\\Beispiele" --install-extensions --install-debugpy --register-menu
oder setup.py doppelklicken (interaktiv).

Pfadsuche (erste Quelle gewinnt):
  1. Argumente (--nx-base, --stubs, --python ...)
  2. %USERPROFILE%\\nx_discovery.json   (aus nx\\nx_discover.py in NX)
  3. nx_discovery.syslog.json          (Vorbelegung aus der Syslog)
  4. Umgebungsvariablen / Dateisystem
  5. Rueckfrage

Schreibt nur in den Dev-Ordner; mit --register-menu zusaetzlich die
Benutzervariable UGII_USER_DIR (HKCU\\Environment). Kein Admin, kein Share.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
IS_WIN = os.name == "nt"


# ------------------------------------------------------------------ Ausgabe
def _p(tag, msg):
    print("[%s] %s" % (tag, msg), flush=True)


def info(m): _p("..", m)
def ok(m):   _p("OK", m)
def warn(m): _p("!!", m)


def fwd(p):
    return p.replace("\\", "/").rstrip("/") if p else ""


def jstr(s):
    """String fuer das Einsetzen in JSON-Templates escapen."""
    return json.dumps(s or "")[1:-1]


# ------------------------------------------------------------------ Helfer
class Ctx:
    no_prompt = False


def ask(q):
    if Ctx.no_prompt:
        return None
    try:
        a = input(q + ": ").strip().strip('"')
    except EOFError:
        return None
    return a or None


def choose(title, items):
    if len(items) == 1 or Ctx.no_prompt:
        return items[0]
    print(title)
    for i, it in enumerate(items, 1):
        print("  [%d] %s" % (i, it))
    n = ask("Nummer")
    try:
        return items[int(n) - 1]
    except (TypeError, ValueError, IndexError):
        return items[0]


def is_nx_base(p):
    return bool(p) and os.path.isfile(os.path.join(p, "NXBIN", "ugraf.exe"))


def py_version(exe):
    try:
        out = subprocess.run([exe, "-c", "import sys;print('%d.%d' % sys.version_info[:2])"],
                             capture_output=True, text=True, timeout=20)
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def find_stub_root(base):
    ugopen = os.path.join(base, "UGOPEN")
    if not os.path.isdir(ugopen):
        return None
    cands = [os.path.join(ugopen, "pythonStubs")]
    cands += glob.glob(os.path.join(ugopen, "*")) + glob.glob(os.path.join(ugopen, "*", "*"))
    for c in cands:
        if os.path.isfile(os.path.join(c, "NXOpen", "__init__.pyi")) or \
           os.path.isfile(os.path.join(c, "NXOpen.pyi")):
            return c
    return None


def load_json(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def g(d, *keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\r\n" if IS_WIN else "\n") as fh:
        fh.write(text)


# ------------------------------------------------------------------ Windows-Umgebung
def set_user_env(name, value):
    import winreg
    import ctypes
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)
    # Aenderung an laufende Prozesse (Explorer) melden
    HWND_BROADCAST, WM_SETTINGCHANGE, SMTO_ABORTIFHUNG = 0xFFFF, 0x1A, 0x2
    ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0,
                                             "Environment", SMTO_ABORTIFHUNG, 3000, None)


# ------------------------------------------------------------------ Hauptablauf
def main():
    ap = argparse.ArgumentParser(description="NXOpen VS Code Setup")
    ap.add_argument("--dev-root", default=HERE)
    ap.add_argument("--nx-base")
    ap.add_argument("--stubs")
    ap.add_argument("--python", help="lokales python.exe mit NX-Version (fuer Debugger)")
    ap.add_argument("--extra", nargs="*", default=[], help="Uebungs-/Beispielordner (nur lesend)")
    ap.add_argument("--install-extensions", action="store_true")
    ap.add_argument("--install-debugpy", action="store_true")
    ap.add_argument("--register-menu", action="store_true")
    ap.add_argument("--no-prompt", action="store_true")
    ap.add_argument("--force", action="store_true", help="erzeugte Dateien ueberschreiben")
    a = ap.parse_args()
    Ctx.no_prompt = a.no_prompt

    print("\n=== NXOpen VS Code Setup (Python %s) ===" % sys.version.split()[0])
    dev = os.path.abspath(a.dev_root)
    info("Dev-Ordner: %s" % dev)
    if " " in dev:
        warn("Dev-Ordner enthaelt Leerzeichen - NX-Menue-ACTIONS koennen daran scheitern.")
    if dev.startswith("\\\\") or "ugsshare" in dev.lower():
        warn("Dev-Ordner liegt auf einem Share - lokal empfohlen.")

    # 1. Discovery
    disc, disc_src = None, None
    for c in (os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), "nx_discovery.json"),
              os.path.join(dev, "nx_discovery.json"),
              os.path.join(HERE, "nx_discovery.syslog.json")):
        if os.path.isfile(c):
            try:
                disc, disc_src = load_json(c), c
                ok("Discovery: %s (%s)" % (c, disc.get("created")))
                break
            except (OSError, ValueError) as e:
                warn("Discovery unlesbar (%s): %s" % (c, e))
    if not disc:
        warn("Keine Discovery - Fallback auf Umgebung/Dateisuche.")

    # 2. NX-Basis
    base = a.nx_base or g(disc, "nx", "base_dir") or os.environ.get("UGII_BASE_DIR")
    if not is_nx_base(base):
        cands = []
        for root in (os.environ.get("ProgramFiles"), r"C:\Program Files", r"D:\Program Files"):
            if root:
                cands += [p for p in glob.glob(os.path.join(root, "Siemens", "NX*")) if is_nx_base(p)]
        cands = sorted(set(cands))
        base = choose("Mehrere NX-Installationen:", cands) if cands else ask("NX-Installationsordner (enthaelt NXBIN)")
    if not is_nx_base(base):
        sys.exit("[XX] NX-Installation nicht gefunden - Aufruf mit --nx-base <Pfad>.")
    ok("NX: %s" % base)
    run_journal = os.path.join(base, "NXBIN", "run_journal.exe")
    if os.path.isfile(run_journal):
        ok("run_journal: %s" % run_journal)
    else:
        warn("run_journal.exe fehlt - Batch-Task nicht nutzbar.")
        run_journal = ""

    # 3. Python-Version von NX
    pyver = g(disc, "python", "version_short")
    if not pyver:
        for dll in glob.glob(os.path.join(base, "NXBIN", "**", "python3*.dll"), recursive=True):
            m = re.match(r"python3(\d+)\.dll$", os.path.basename(dll), re.I)
            if m:
                pyver = "3." + m.group(1)
                break
    pyver = pyver or ask("Python-Version von NX (z.B. 3.11)")
    if not pyver:
        sys.exit("[XX] NX-Python-Version unbekannt - Discovery-Journal in NX ausfuehren.")
    ok("NX-Python: %s" % pyver)

    # 4. Stubs & Samples
    stubs = a.stubs or g(disc, "nx", "stubs_root")
    if not stubs or not os.path.isdir(stubs):
        stubs = find_stub_root(base) or ask("Ordner der NXOpen-Stubs (enthaelt NXOpen\\__init__.pyi)")
    if not stubs or not os.path.isdir(stubs):
        sys.exit("[XX] NXOpen-Stubs nicht gefunden - Aufruf mit --stubs <Pfad>.")
    ok("Stubs: %s" % stubs)

    samples = g(disc, "nx", "samples")
    if not samples or not os.path.isdir(samples):
        samples = None
        for c in ("UGOPEN/SampleNXOpenApplications/Python", "UGOPEN/SampleNXOpenApplications"):
            p = os.path.join(base, *c.split("/"))
            if os.path.isdir(p):
                samples = p
                break
    if samples:
        ok("Siemens-Beispiele: %s" % samples)
    else:
        warn("Keine SampleNXOpenApplications gefunden.")

    # 5. Lokales Python gleicher Version (fuer Debugger/Linting)
    cands = [a.python] if a.python else []
    if shutil.which("py"):
        try:
            out = subprocess.run(["py", "-0p"], capture_output=True, text=True, timeout=20).stdout
            cands += re.findall(r"([A-Za-z]:\\.+?\.exe)\s*$", out, re.M)
        except (OSError, subprocess.SubprocessError):
            pass
    nodot = pyver.replace(".", "")
    la = os.environ.get("LOCALAPPDATA", "")
    cands += [os.path.join(la, "Programs", "Python", "Python" + nodot, "python.exe"),
              os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Python" + nodot, "python.exe"),
              r"C:\Python%s\python.exe" % nodot, sys.executable]
    w = shutil.which("python")
    if w:
        cands.append(w)
    pyexe = ""
    seen = set()
    for c in cands:
        if not c or "WindowsApps" in c or c in seen or not os.path.isfile(c):
            continue
        seen.add(c)
        if py_version(c) == pyver:
            pyexe = os.path.abspath(c)
            break
    if pyexe:
        ok("Lokales Python %s: %s" % (pyver, pyexe))
    else:
        warn("Kein lokales Python %s. IntelliSense geht trotzdem (pyrightconfig), fuer Debugging:" % pyver)
        warn("  winget install Python.Python.%s   und Setup erneut ausfuehren." % pyver)

    # Python fuer die VS-Code-Tasks: das, mit dem dieses Setup laeuft
    tool_py = sys.executable
    info("Tasks laufen mit: %s" % tool_py)

    # 6. Zusatzordner
    extra = list(a.extra)
    if not extra and not Ctx.no_prompt:
        print("Weitere Ordner (Uebungen, Beispiele) nur-lesend einbinden - leer lassen zum Beenden:")
        while True:
            f = ask("  Ordner")
            if not f:
                break
            if os.path.isdir(f):
                extra.append(f)
            else:
                warn("existiert nicht: %s" % f)
    extra = list(dict.fromkeys(os.path.abspath(f) for f in extra if os.path.isdir(f)))
    for f in extra:
        ok("Zusatzordner: %s" % f)

    # 7. Dateien erzeugen
    folders = ['    { "path": ".", "name": "NXOpen Dev" }']
    ro = ['      "**/pythonStubs/**": true']
    if samples:
        folders.append('    { "path": "%s", "name": "Siemens Samples" }' % jstr(fwd(samples)))
        ro.append('      "**/SampleNXOpenApplications/**": true')
    for f in extra:
        leaf = os.path.basename(f.rstrip("\\/"))
        folders.append('    { "path": "%s", "name": "%s" }' % (jstr(fwd(f)), jstr(leaf)))
        ro.append('      "%s": true' % jstr("**/%s/**" % leaf))

    vars_ = {
        "DEV_ROOT": dev,
        "DEV_ROOT_FWD": jstr(fwd(dev)),
        "PY_EXE": pyexe,
        "PY_EXE_FWD": jstr(fwd(pyexe)),
        "PY_VERSION": pyver,
        "STUBS_FWD": jstr(fwd(stubs)),
        "TOOL_PY_FWD": jstr(fwd(tool_py)),
        "WORKSPACE_FOLDERS": ",\n".join(folders),
        "READONLY_GLOBS": ",\n".join(ro),
    }

    def render(tpl, out_rel):
        out = os.path.join(dev, *out_rel.split("/"))
        if os.path.exists(out) and not a.force:
            warn("existiert, uebersprungen: %s  (--force ueberschreibt)" % out_rel)
            return
        with open(os.path.join(HERE, "templates", tpl), encoding="utf-8-sig") as fh:
            t = fh.read()
        for k, v in vars_.items():
            t = t.replace("{{%s}}" % k, v)
        left = re.findall(r"\{\{[A-Z_]+\}\}", t)
        if left:
            warn("%s: unbelegte Platzhalter %s" % (out_rel, ", ".join(sorted(set(left)))))
        write_text(out, t)
        ok("geschrieben: %s" % out_rel)

    render("nxopen.code-workspace.tpl", "nxopen.code-workspace")
    render("pyrightconfig.json.tpl", "pyrightconfig.json")
    render("tasks.json.tpl", ".vscode/tasks.json")
    render("launch.json.tpl", ".vscode/launch.json")
    render("nx_dev_loader.py.tpl", "nx/nx_dev_loader.py")
    render("nx_batch_bootstrap.py.tpl", "nx/nx_batch_bootstrap.py")
    render("nx_dev.men.tpl", "nx/startup/nx_dev.men")

    state = os.path.join(dev, ".nxdev")
    os.makedirs(state, exist_ok=True)
    user_dir = g(disc, "nx", "user_dir") if disc else os.environ.get("UGII_USER_DIR")
    paths = {
        "dev_root": dev, "nx_base": base, "run_journal": run_journal, "stubs": stubs,
        "samples": samples, "nx_python_version": pyver, "python_exe": pyexe,
        "tool_python": tool_py, "extra_folders": extra, "ugii_user_dir": user_dir,
        "custom_dir_file": g(disc, "nx", "custom_directory_file"),
        "discovery": disc_src, "generated": datetime.now().isoformat(timespec="seconds"),
    }
    write_text(os.path.join(state, "paths.json"), json.dumps(paths, indent=2, ensure_ascii=False))
    ok("Pfaduebersicht: .nxdev/paths.json")
    env = {k: v for k, v in (g(disc, "env") or {}).items() if k.upper() != "PYTHONPATH"}
    if env:
        write_text(os.path.join(state, "nx_env.json"), json.dumps(env, indent=2, ensure_ascii=False))
        ok("NX-Umgebung fuer Batch gesichert (.nxdev/nx_env.json, %d Variablen)" % len(env))

    # 8. VS-Code-Erweiterungen
    if a.install_extensions:
        code = shutil.which("code")
        if not code:
            warn("'code' nicht im PATH - Erweiterungen manuell installieren (Workspace empfiehlt sie).")
        else:
            for ext in ("ms-python.python", "ms-python.vscode-pylance", "ms-python.debugpy"):
                try:
                    r = subprocess.run([code, "--install-extension", ext, "--force"],
                                       capture_output=True, text=True, timeout=180)
                    (ok if r.returncode == 0 else warn)("Erweiterung %s (rc=%d)" % (ext, r.returncode))
                except (OSError, subprocess.SubprocessError) as e:
                    warn("Erweiterung %s nicht installierbar (%s) - ggf. von Richtlinie blockiert;"
                         " in VS Code manuell installieren." % (ext, e))
                    break

    # 9. debugpy
    if a.install_debugpy:
        if pyexe:
            info("Installiere debugpy fuer Python %s nach _debugpy ..." % pyver)
            r = subprocess.run([pyexe, "-m", "pip", "install", "--upgrade",
                                "--target", os.path.join(dev, "_debugpy"), "debugpy"])
            if r.returncode == 0:
                ok("debugpy installiert")
            else:
                warn("pip fehlgeschlagen (Proxy?). Manuell: %s -m pip install --target \"%s\" debugpy"
                     % (pyexe, os.path.join(dev, "_debugpy")))
        else:
            warn("debugpy braucht ein lokales Python %s - uebersprungen." % pyver)

    # 10. NX-Menue
    print()
    nx_dir = os.path.join(dev, "nx")
    if a.register_menu:
        if user_dir:
            ud = user_dir.lower()
            if "ugsshare" in ud or ud.startswith("\\\\") or ud.startswith("g:"):
                warn("UGII_USER_DIR zeigt auf einen Share (%s) - wird NICHT angefasst. Siehe README." % user_dir)
            elif os.path.normcase(os.path.abspath(user_dir)) == os.path.normcase(nx_dir):
                ok("UGII_USER_DIR zeigt bereits auf %s" % nx_dir)
            else:
                dst = os.path.join(user_dir, "startup")
                os.makedirs(dst, exist_ok=True)
                shutil.copy2(os.path.join(nx_dir, "startup", "nx_dev.men"), dst)
                ok("Menue kopiert nach %s" % dst)
        elif IS_WIN:
            try:
                set_user_env("UGII_USER_DIR", nx_dir)
                ok("Benutzervariable UGII_USER_DIR = %s gesetzt." % nx_dir)
                warn("ECTR UND NX komplett neu starten - NX erbt die Umgebung von ECTR.")
                warn("Kontrolle in der Syslog: 'No user customizations read from UGII_USER_DIR' darf nicht mehr erscheinen.")
            except OSError as e:
                warn("Benutzervariable nicht setzbar (%s). Plan B: nx\\startup\\nx_dev.men nach %%TEMP%%\\startup kopieren." % e)
        else:
            warn("--register-menu nur unter Windows.")
    else:
        info("NX-Menue nicht registriert. Optionen:")
        info("  py setup.py --register-menu   (setzt UGII_USER_DIR = %s)" % nx_dir)
        info("  oder ohne Registrierung: in NX Alt+F8 -> %s" % os.path.join(nx_dir, "nx_dev_loader.py"))

    print()
    ok("Fertig. In VS Code oeffnen: %s" % os.path.join(dev, "nxopen.code-workspace"))


if __name__ == "__main__":
    try:
        main()
    finally:
        # Bei Doppelklick bleibt das Fenster offen
        if IS_WIN and "--no-prompt" not in sys.argv:
            try:
                input("\nEnter zum Schliessen ...")
            except EOFError:
                pass
