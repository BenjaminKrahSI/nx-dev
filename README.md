# NXOpen Dev Starter – VS Code ↔ Siemens NX 2412

Komplett in Python – **keine .cmd- oder PowerShell-Skripte**

Live-Entwicklung von NXOpen-Python in VS Code gegen eine laufende NX-Session
(inkl. ECTR), plus Batch-Läufe über `run_journal.exe`. Kein Eingriff in die
NX-Installation oder den Share `G:\CAD\ugsshare-2412`.

## Deine Umgebung (aus der NX-Syslog vom 29.09.2026)

| Punkt                         | Wert                                             | Konsequenz                                  |
|---                            |---                                               |---                                          |
| NX                            | 2412.8502, `C:\Program Files\Siemens\NX2412`     | vorbelegt                                   |
| NX-Python                     | **3.11** (`python311.dll`, `nxbin\python`)       | pyrightconfig auf 3.11                      |
| Lokales Python                | 3.14 (`AppData\Local\Programs\Python\Python314`) | **3.11 nachinstallieren** fürs Debugging    |
| `PYTHONPATH`                  | von NX gesetzt (`ugii_env_ug.dat`)               | wird nie überschrieben                      |
| `UGII_USER_DIR`               | **nicht gesetzt**                                | frei für das Dev-Menü                       |
| `UGII_CUSTOM_DIRECTORY_FILE`  | auf `G:\…\custom_dirs.dat` (Share)               | wird nicht angefasst                        |
| `HOME`                        | von NX auf `…\AppData\Local\Temp` umgebogen      | Starter nutzt `USERPROFILE`                 |
| NX-Start                      | über ECTR                                        | Umgebungsänderungen erst nach ECTR-Neustart |

## Nach dem Klonen

Im Repository-Ordner ausführen:

```text
py setup.py
```

Loader, Batch-Einstieg, NX-Menü, VS-Code-Tasks, Debug-Konfiguration, Workspace und
Pyright-Konfiguration werden lokal aus `templates/` erzeugt. Sie enthalten
arbeitsplatzabhängige Pfade und sind deshalb nicht im Repository. Das Setup
registriert ohne Zusatzoptionen kein Menü und installiert nichts.
Anschließend `nxopen.code-workspace` öffnen. Für spätere Neugenerierung:
`py setup.py --force --no-prompt`.

Die tägliche Arbeit mit Commits ist in [GIT_ARBEITSWEISE.md](GIT_ARBEITSWEISE.md)
beschrieben. Die nötigen NX-/Python-Voraussetzungen folgen im nächsten Abschnitt.

## Einrichtung (einmalig, ca. 5 Minuten)

1. **Entpacken** nach z. B. `C:\dev\nxopen` – lokal, ohne Leerzeichen, nicht auf `G:`.
2. **Python 3.11 installieren** (für Debugger/Linting; IntelliSense geht auch ohne):
   `winget install Python.Python.3.11`
3. **Optional, aber empfohlen – Discovery in NX:** `Alt+F8` →
   `C:\dev\nxopen\nx\nx_discover.py`. Schreibt `%USERPROFILE%\nx_discovery.json`
  mit Stub-Pfad und exakter Laufzeitumgebung. Ohne diesen Schritt nutzt das Setup
  eine gegebenenfalls lokal vorhandene `nx_discovery.syslog.json` und sucht
  fehlende Angaben selbst. Discovery-Dateien werden nicht versioniert.
4. **Setup:** `setup.py` doppelklicken (interaktiv), oder im VS-Code-Terminal
   (bzw. jedem Terminal) mit allen Extras:
   ```
   py setup.py --extra "D:\Pfad\Uebungen" "D:\Pfad\Beispiele" --install-extensions --install-debugpy --register-menu
   ```
   Statt `py` geht auch `python`. Das Setup merkt sich den Interpreter, mit dem
   es gestartet wurde, und nutzt ihn für die VS-Code-Tasks.
5. **ECTR und NX komplett neu starten** (nur nach `--register-menu`). Danach gibt es
   in NX unter *Menü → NX Dev* zwei Befehle. Mit `Strg+1` (Anpassen) den Befehl
   „Ziel aus VS Code ausfuehren“ auf die Schnellzugriffsleiste ziehen und ggf.
   einen Shortcut vergeben.
6. `nxopen.code-workspace` in VS Code öffnen.

Setup-Parameter: `--nx-base`, `--stubs`, `--python` überschreiben die Suche;
`--force` überschreibt bereits erzeugte Dateien; `--no-prompt` für unbeaufsichtigt.

**Plan B fürs Menü**, falls `UGII_USER_DIR` nicht bis NX durchkommt: In deiner
Custom-Dir-Liste steht `${TEMP}`, NX lädt also `%TEMP%\startup\*.men`.
`nx\startup\nx_dev.men` dorthin kopieren funktioniert, kann aber von
Aufräumtools gelöscht werden.

## Arbeitsablauf

| Aktion                      | Wo      | Wie                                                                                        |
|-------                      |----     |----                                                                                        |
| Datei als Ziel markieren    | VS Code | Task „NX: aktuelle Datei als Ziel setzen“ (Shortcut: `templates\keybindings.example.json`) |
| Ausführen mit frischem Code | NX      | Menü → NX Dev → Ziel ausführen (bzw. QAT-Button)                                           |
| Log live mitlesen           | VS Code | Task „NX: Log live verfolgen“                                                              |
| Batch ohne GUI              | VS Code | Task „NX: Batch ausführen (run_journal)“                                                   |
| Breakpoints                 | VS Code | Task „Debug-Modus umschalten“ → in NX ausführen → `F5` „an laufende Session anhängen“      |

Der Loader wirft vor jedem Lauf alle Module aus dem Dev-Ordner **und** aus dem
Ordner der Zieldatei aus dem Cache. Hilfsmodule neben Übungsdateien werden also
ebenfalls neu geladen – kein NX-Neustart nach Änderungen.

In eigenen Skripten:
```python
from nxdev import get_logger, lw
log = get_logger("mein_tool")   # -> .nxdev\nx_dev.log
lw("ins Listing Window")
```

## Ohne Menü-Registrierung

Funktioniert genauso über `Alt+F8` → `nx\nx_dev_loader.py`. NX merkt sich das
zuletzt gespielte Journal, danach sind es zwei Klicks.

## Einschränkungen (ehrlich)

- **Debugging** hält den NX-UI-Thread an, solange ein Breakpoint steht. `debugpy`
  muss für **3.11** installiert sein (`--install-debugpy` braucht dafür das lokale 3.11).
  Auf NX 2412 nicht von mir verifiziert – Log + Traceback reichen meistens.
- **Batch (`run_journal`)** hat keine GUI und keine ECTR-Verbindung: Parts nur per
  Dateipfad, keine Dialoge, keine Selektion.
- **`code --install-extension`** ruft intern `code.cmd` auf und kann daher von
  der Richtlinie blockiert sein – dann die drei empfohlenen Erweiterungen im
  VS-Code-Marketplace installieren (der Workspace schlägt sie beim Öffnen vor).
- **Menüdatei (`.men`)**: Syntax nach MenuScript-Standard; falls NX sie nicht lädt,
  steht der Grund in der Syslog (Suche nach `nx_dev.men`).
- Wenn ECTR `UGII_USER_DIR` künftig selbst setzt, greift die Benutzervariable nicht
  mehr – dann `--register-menu` erneut ausführen, es kopiert die Menüdatei in den
  dann gesetzten Ordner (Share-Pfade werden verweigert).

## Projektzuordnung

Die gemeinsame NXOpen-Entwicklungsumgebung bleibt unter `nx/`, `tools/`,
`src/` und `templates/`. Fachskripte werden nach Gesellschaft beziehungsweise
Standort getrennt:

| Projektordner | Zuordnung |
|---|---|
| `projects-kfv/` | KFV, eigene Gesellschaft für Türbeschläge; Normteilsuche |
| `projects-siegenia-nd/` | SIEGENIA Niederdielfen, Hauptstandort; Notiz-zu-Kurven |

Hermeskeil (Schiebetüren) hat ebenfalls eine eigene NX-Share-Ablage; ein
Projektordner wird bei Bedarf ergänzt. Jede Gesellschaft beziehungsweise jeder
Standort verwendet die eigene Freigabe. `G:` steht daher nicht überall für
denselben Bestand; der Zugriff von deinem Standort kann über `T:` erfolgen.
Standardsordner immer ausdrücklich konfigurieren, nicht aus dem
Laufwerksbuchstaben ableiten.

## KFV-Normteilsuche

Die Fachskripte liegen getrennt von der Entwicklungsumgebung unter `projects-kfv/`.
Der Standardsordner wird über `--root` angegeben, ersatzweise über
`KFV_STANDARDS_DIR`. Fehlt beides, erscheint eine Fehlermeldung.
Ein Testlauf ohne NX und ohne echten Standardsbestand:

```text
python projects-kfv/standards_catalog.py --root projects-kfv/tests/fixtures B001 HS5000
```

Für den NX-Dialog `projects-kfv/standards_search.py` einen echten Standardsordner
konfigurieren. NX muss `KFV_STANDARDS_DIR` beim Start erben; nach einer
Umgebungsänderung daher gegebenenfalls ECTR und NX neu starten. Die leeren
Fixture-Dateien sind nicht als NX-Teile ladbar.
Details: [KFV-Entwurf](projects-kfv/docs/variantenkonfiguration-kfv.md).

Tests vom Repository-Ordner aus:

```text
python -m pytest tests -q
```

Ohne installiertes pytest: `python -m unittest discover -s tests`.
Die eigentlichen Tests liegen unter `projects-kfv/tests/`; `tests/test_kfv.py` bindet sie
in beide Befehle ein. Der optionale Test gegen einen echten Bestand wird ohne
`KFV_STANDARDS_DIR` übersprungen.

## Struktur

```
setup.py                         Pfadsuche + lokale Generierung
templates/                       Versionierte Vorlagen für das Setup
GIT_ARBEITSWEISE.md               Git-Regeln und täglicher Ablauf
nx/nx_discover.py                 Discovery-Journal (in NX ausführen)
src/nxdev/                       Logger + Listing-Helfer
scratch/hello_nx.py               Rauchtest
tools/*.py                       Task-Helfer (Ziel, Batch, Log, Debug)
projects-kfv/standards_catalog.py          Dateikatalog und CLI, ohne NX testbar
projects-kfv/standards_search.py           NX-Dialog für Normteilsuche und Einfügen
projects-kfv/standards_search.dlx          Versionierte Block-Styler-Dialogressource
projects-kfv/build_standards_search_dlx.py Generator zum Erneuern dieser .dlx
projects-kfv/docs/                        KFV-Fachkonzept und Pilotbeschreibung
projects-kfv/tests/                       Fachtests und leere Namens-Fixtures
projects-siegenia-nd/notiz_zu_kurven.py    Notiz-Skript für Niederdielfen
tests/test_kfv.py                Einstieg für die zentralen Testbefehle

Lokal generiert, nicht versioniert:
nx/nx_dev_loader.py              Live-Loader aus Template
nx/nx_batch_bootstrap.py         Batch-Einstieg aus Template
nx/startup/nx_dev.men            NX-Menü aus Template
.vscode/tasks.json              VS-Code-Tasks aus Template
.vscode/launch.json             Debug-Konfiguration aus Template
nxopen.code-workspace           Workspace aus Template
pyrightconfig.json              Pyright-Konfiguration aus Template
.nxdev/                         Zustand: Ziel, Log, paths.json, nx_env.json
_debugpy/                       Optional lokal installierter Debugger
nx_discovery.syslog.json        Optionale lokale Syslog-Vorbelegung
```
