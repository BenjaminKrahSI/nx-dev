# Variantenkonfiguration KFV und NX-Standardsuche

**Status:** Arbeitsentwurf, 15.10.2026  
**Grundlage:** konsolidiertes Terminprotokoll „Variantenkonfiguration KFV“ und erste Sichtung der NX-Standardsablage.  
**Zielgruppe:** Konstruktion, PLM/ECTR-Team und CAD-Automatisierung.

## Ziel und Empfehlung

Der Variantenprozess soll bestehende Konstruktionen besser wiederverwenden und neue Varianten mit weniger manuellen Wiederholungen ableiten. Der erste technische Schritt ist eine nachvollziehbare Suche nach NX-Fräsbildern anhand von Dateinamen und Ordnern. Dafür ist NX der passende Einstieg: Der Anwender sucht ein `.prt`-Pattern im KFV-Standardsbestand und wählt es im NX-Kontext zur Platzierung in der aktiven Baugruppe aus.

Die Suche nach vorhandenen Mehrfachverriegelungen, Materialnummern, SAP-Dokumenten und PLM-Klassifizierungen ist davon getrennt zu behandeln. Dafür ist ECTR der passende Einstieg, sobald Suchmerkmale und deren Pflege geklärt sind. Eine spätere Integration setzt einen abgestimmten Datenfluss und einen unterstützten Start-/Übergabemechanismus voraus.

Der aktuelle Dateinamen-Prototyp ist ein **erster Wurf**, kein freigegebener Merkmalskatalog und kein Konfigurator. Er zeigt erkannte Kandidatenwerte und erhält unbekannte Tokens, damit Konstrukteure die Zuordnung anschließend korrigieren können.

## Heutiger Prozess

1. Das Produktmanagement liefert eine Liste der benötigten Standardvarianten. Kundenspezifische K-Ausführungen kommen fortlaufend hinzu.
2. Vor einer Neuanlage wird in der Excel-Übersicht nach Materialnummern, Verriegelungsinformationen und einer ähnlichen bestehenden Baugruppe gesucht.
3. Für eine neue Stulp werden Steuerskizzen angelegt, Maße aus der Werksnorm übernommen und der Hauptschlossbereich parametrisch beschrieben. Hochverlinkungen und Ausdrücke steuern die Varianten.
4. Lochungen, Senkungen und wiederverwendbare Bearbeitungen werden aus vorhandenen Pattern beziehungsweise NX-Standards übernommen. Die geeignete Datei wird derzeit über Ordner und Dateiauswahl gesucht.
5. Werte aus einer Excel-Datei werden für Skizzen und Tabellenzeichnungen verwendet. Das Modell enthält Fertigungs- und Detailinformationen.
6. Eine Baugruppe kombiniert Hauptschloss, Zusatzkästen, Stulp, Treibstangen und Verbindungselemente. Änderungen am Hauptschloss können neue Stulpdurchbrüche erfordern; Positionen und Komponenten sind daher nicht unabhängig.
7. Für jede Materialnummer wird eine passende, eigenständige Zeichnung erwartet. Kundenzeichnung, Fertigungszeichnung, Materialnummern, Falle/Nuss und Rendering müssen dem konkreten Variantenstand entsprechen.
8. ECTR verwaltet die Produkt-/Dokumentstruktur und enthält bereits Klassifizierungswerte, derzeit vor allem für Stulpen. Umfang und Pflege der Baugruppenmerkmale sind offen.

### Relevante Variantenregeln aus dem Termin

- B001 und B002 sind Standardausführungen; bei B003 wandert ein Kasten nach oben und die Stulp wird länger.
- Kastenpositionen ändern sich im Baukastensystem typischerweise in 125-mm-Schritten.
- Bei K-Ausführungen wird häufig nur die Stulplänge angepasst; Ausnahmen können andere Treibstangen oder Kastenpositionen erfordern.
- Genannte Stulpdicken: Flachstulp 2,5 mm und 3,5 mm, Profilstulp 2,0 mm. P624 ist eine genannte Profilstulp-Ausprägung.
- Eine Variante kann eigene Zeichnungen, Materialnummern, Komponenten und ein Rendering benötigen. Die Dateisuche allein löst diese Prozessanforderung nicht.

## Zuständigkeit der Suche

| Suchaufgabe | Passender Einstieg | Ergebnis |
|---|---|---|
| NX-Fräsbilder und andere lokale Standards anhand von Dateiname/Ordner finden | NX | Kandidaten-Datei wählen und im NX-Baugruppenkontext platzieren |
| Bestehende Mehrfachverriegelungen und ähnliche Varianten anhand von Material-/PLM-Merkmalen finden | ECTR | ECTR-/SAP-Objekte mit Status, Dokumentbeziehungen und Klassifizierung anzeigen |
| Excel-Matrix als Suche, Klassifizierung oder Konfigurator nutzen | Noch zu entscheiden | Datenhoheit, Aktualität, Verantwortliche und Übergabe klären |
| Variantenmodell, Zeichnung und Rendering erzeugen | NX mit PLM-Prozess | Pilot für Stulp und eigenständige Zeichnung je Materialnummer |

ECTR-README und Makroregeln beschreiben ECTR-Makros für SAP-/ECTR-Abläufe, belegen aber keinen direkten Zugriff dieser Makros auf eine laufende NX-Session. Deshalb wird die erste Dateisuche NX-seitig prototypisiert. ECTR bleibt für SAP-/Materialsuche und PLM-Klassifizierung zuständig.

## KFV-Standardsbestand und erster Suchprototyp

**Konfiguration:** Katalog und NX-Pilot erhalten den Standardsordner über `--root <Ordner>`, ersatzweise über die Umgebungsvariable `KFV_STANDARDS_DIR`. Das Argument hat Vorrang. Fehlt beides, erscheint eine klare Fehlermeldung; es gibt keinen persönlichen Standardpfad und keinen automatischen Netzwerkzugriff. NX muss die Umgebungsvariable beim Start erben.

Die automatisierten Tests verwenden temporäre Ordner und die leeren Namens-Platzhalter unter `kfv/tests/fixtures/`. Diese Dateien sind keine ladbaren NX-Teile. Ein optionaler Test gegen den echten Bestand läuft nur mit gesetztem `KFV_STANDARDS_DIR`.

Der Katalog scannt den gewählten Testordner bei jedem Aufruf read-only und schreibt keine Dateien in den Standardsbestand.

Der Prototyp liegt in `kfv/standards_catalog.py`. Er extrahiert vorläufige Gruppen:

| Gruppe | Beispiele | Einschränkung |
|---|---|---|
| Varianten-/Familiencodes | `B001`, `K091`, `W000`, `T0`, `4ZK` | Rohcode, fachliche Definition noch zu bestätigen |
| Seriencodes | `HS5000`, `HS99`, `AS2608` | Kandidat aus dem Namen, kein verifiziertes ECTR-Merkmal |
| Maßtokens | `92E`, `55_65D`, `25-65D` | Format erkannt, Einheit/Bedeutung nicht automatisch abgeleitet |
| Sprachmarker | `englisch`, `english`, `EN` | Nur erkannte Schreibweisen |
| Zusatzmarker | `neu`, `alt`, `orig`, `vorschlag` | Nicht als Freigabe- oder Gültigkeitsstatus interpretieren |
| Unklassifizierte Tokens | alle übrigen Namensteile | Bleiben in Suchergebnis und Export erhalten |

Zusätzlich gibt es eine primäre, heuristische Dateikategorie für das Dropdown. Eine frühere Sichtung des lokalen Testbestands ergab: Fräsbilder 520, Senkungen 60, Treibstangen 51, Zusatzkästen 55, Hauptschlösser 153, Zeichnungsvorlagen 166 und Sonstiges 331. Mehrdeutige Fälle werden nach einer festen Regel priorisiert; das sind Suchgruppen und keine fachlich freigegebenen Metadaten.

Beispiele zum lokalen Ausführen:

```text
python kfv/standards_catalog.py --root kfv/tests/fixtures B001 HS5000
python kfv/standards_catalog.py --root kfv/tests/fixtures 4ZK 88E
python kfv/standards_catalog.py --root kfv/tests/fixtures --format csv --limit 0
python kfv/standards_catalog.py --root kfv/tests/fixtures --format json
```

Die Suchbegriffe werden ohne Beachtung der Groß-/Kleinschreibung als UND-Suche behandelt. Feldfilter können vorangestellt werden, zum Beispiel `familie:B001 serie:HS5000 mass:92E kategorie:Fräsbilder tag:neu lang:EN`. Unterstützt werden `familie`/`family`, `serie`/`series`, `mass`/`measure`/`dimension`, `kategorie`/`category`/`cat`, `ordner`/`folder`, `sprache`/`lang`/`language`, `art`/`kind`, `tag`/`marker` und `name`/`datei`. Der Dropdownfilter und `kategorie:` verwenden die heuristische Gruppe; `ordner:` filtert nur den tatsächlichen relativen Ordnerpfad. Die Werte bleiben Kandidaten aus Dateiname oder Pfad, keine bestätigte technische Klassifikation.

### NX-Pilotdialog

Der Dialog liegt in `kfv/standards_search.py`; die zugehörige Block-Styler-Datei ist `kfv/standards_search.dlx`. In NX 2412 über **Tools > Journal > Play** (Alt+F8) das Python-Journal starten. Beim ersten Start kann der Dialoggenerator die `.dlx` aus den installierten SNAP-Controlvorlagen neu erzeugen. Voraussetzung ist eine aktive Baugruppe und ein per `--root` oder `KFV_STANDARDS_DIR` konfigurierter Ordner mit echten NX-Teilen.

Der Dialog scannt ausschließlich den konfigurierten Standardsordner beim Öffnen und über **Standards aktualisieren** erneut. Suchtext und Kategorie-Dropdown filtern den eingelesenen Bestand ohne erneuten Dateiscan. Die Trefferliste zeigt höchstens 300 Zeilen; bei mehr Treffern fordert der Status zum weiteren Eingrenzen auf. Beim Auswählen wird nur dieses Teil geladen und sein gespeichertes Modell-Preview angefordert. Ist kein Preview in der Datei vorhanden, zeigt der Dialog dies im Status an. Preview-Parts werden nicht automatisch geschlossen, weil NX sie als geändert melden kann; sie bleiben bis zum Beenden der NX-Session geladen. Über den NX-Punktwähler wird ein Einfügepunkt ausgewählt; **OK** fügt die Komponente an diesem Punkt mit der Orientierung des Baugruppen-WCS ein. Die Baugruppe wird nicht automatisch gespeichert. Der Quellordner bleibt read-only.

Der NX-Live-Lauf mit dem Kategorie-Dropdown ist noch nicht erneut abgenommen. Preview-Darstellung und Platzierung wurden am Testbestand bereits sichtbar ausprobiert; die Preview-Teile werden jetzt bis zum Sitzungsende im Speicher gehalten. Bis der dokumentierte Loader/Menu-Widerspruch beseitigt ist, das Journal direkt über Journal Play starten statt über den NX-Dev-Loader.

`Standards.xls` liegt im Ordner, wurde für diesen Prototyp aber nicht inhaltlich ausgewertet. Ebenso ist noch nicht geklärt, ob die Excel-Übersicht für Verriegelungsvarianten dieselben Merkmale wie die Standards-Dateinamen enthält. Keine der Arbeitsmappen wird ohne Entscheidung über Datenhoheit zur maßgeblichen Suchquelle erklärt.

## ECTR-Übergabe

Für das ECTR-Repo sind die folgenden, vom NX-Dateikatalog getrennten Arbeitspakete vorgesehen:

| ID | ECTR-/PLM-Arbeitspaket | Erwartetes Ergebnis |
|---|---|---|
| A05 | Dynamische Suche nach KFV-Mehrfachverriegelungen prüfen | Abfrage und nachvollziehbare Treffer |
| A06 | Baugruppenklassifizierung und Pflichtmerkmale bestimmen | Merkmalskatalog samt Pflegeprozess |
| A07 | Datenherkunft zwischen Excel, Produkt Base, ECTR und CAD klären | Freigegebenes Datenflussbild und führendes System je Merkmal |
| A08 | Excel-Struktur als ECTR-Suche/Konfigurator bewerten | Optionen mit Aufwand und Nutzen |

Übergabevoraussetzungen sind bestätigte Suchfelder, repräsentative Beispieldatensätze, Umgang mit Revision/Freigabe, Datenverantwortliche und erwartete Treffer. Eine Verbindung zwischen ECTR und NX ist erst zu spezifizieren, wenn geklärt ist, ob ECTR nur einen NX-Befehl startet oder auch Identifikatoren/Filterwerte übergeben muss.

## Offene Entscheidungen

- Welche Dateinamen-Tokens bedeuten verbindlich Serie, Stulpart, Dornmaß, Kastenlage, Länge oder Fräsbild?
- Welche Schreibvarianten und Synonyme sollen zusammenfallen? Wie werden widersprüchliche Tokens behandelt?
- Welche konkrete NX-Aktion soll ein ausgewähltes Pattern ausführen: Baugruppenkomponente platzieren oder Geometrie in ein aktives Teil übernehmen? Für den ersten Wurf ist der Platzierungsdialog vorgesehen.
- Wer bestätigt die vorläufige Klassifikation und pflegt spätere Änderungen an Namenskonventionen?
- Welche Excel-Datei enthält die Filtermerkmale, und welches System ist für jedes Merkmal führend?
- Wie wird je Materialnummer eine eigenständige Zeichnung erzeugt, benannt und mit Materialnummer/Rendering verknüpft?
- Welche der drei bestehenden Makros können gefahrlos zusammengefasst oder beim Speichern ausgeführt werden?
- Welche NXOpen-API und welche Firmenwerkzeuge sind für die Integration in die laufende NX-/ECTR-Session freigegeben?

## Gesamtaufgaben

| ID | Aufgabe | Zuständigkeit laut Protokoll | Abnahmekriterium |
|---|---|---|---|
| A01 | Stulp-Teilefamilie als Pilot aufbauen und bewerten | Stefan Loske | Varianten erzeugbar; Zeichnungsprozess je Variante dokumentiert |
| A02 | Teilefamilien für Baugruppen prüfen | PLM/CAD-Team | Machbarkeit mit Voraussetzungen und Grenzen |
| A03 | Drei Makros analysieren und zusammenfassen oder beim Speichern ausführen | CAD-Automatisierung | Weniger Klickaufwand und stabiler Testlauf |
| A04 | Pattern-/Mustersuche strukturieren | PLM/CAD-Team | Filterkatalog für Fräsbild, Serie, Stulp, Dornmaß, Länge und Kastenlage |
| A05 | Dynamische ECTR-Suche für KFV-Mehrfachverriegelungen konzipieren | ECTR/PLM-Team | Suchabfrage mit nachvollziehbaren Treffern |
| A06 | Klassifizierung für Baugruppen und Pflichtmerkmale festlegen | ECTR/PLM-Team + Produktmanagement | Merkmalskatalog und Pflegeprozess |
| A07 | Datenquellen und Datenhoheit klären | PLM-Team | Freigegebenes Datenflussbild |
| A08 | Excel-Übernahme in ECTR bewerten | ECTR/PLM-Team | Umsetzungsoptionen mit Aufwand/Nutzen |
| A09 | Schriftkopf für Kundenzeichnungen klären | Produktmanagement + Konstruktion | Freigegebener Kundenzeichnungsstandard |
| A10 | Rendering als Variantenoutput aufnehmen | CAD/PLM-Team | Definierter Output und Ablage-/Verknüpfungsregel |

Für alle Aufgaben außer A01 ist in der konsolidierten Arbeitsfassung kein individueller Termin genannt; Termine und Status sind daher noch festzulegen.

## NX-Entwicklungsloop

Das Starter-Repo beschreibt einen VS-Code-zu-NX-Live-Loop: eine Python-Datei als Ziel markieren, über das NX-Menü in der laufenden Session ausführen und Log/Listing Window prüfen; optional kann ein Debugger anhalten. Der Batchlauf über `run_journal.exe` ist GUI-frei und hat laut README keine ECTR-Verbindung. Damit eignet sich Batch nicht für die Abnahme von Dialogen, Platzierung oder Selektion.

Vor Nutzung dieses Loops für die Suchfunktion muss ein lokaler Widerspruch geprüft werden: `nx/startup/nx_dev.men` verweist auf `nx/nx_dev_loader.py`, deren aktueller Inhalt kein Loader ist; die Loader-Logik ist in `templates/nx_dev_loader.py.tpl` vorhanden. Die Dateien wurden für dieses Projekt nicht verändert, weil zunächst geklärt werden muss, ob `nx_dev_loader.py` absichtlich ein Fachskript enthält oder versehentlich ersetzt wurde.

## Verifikation des ersten Wurfs

- Dateikatalog liest rekursiv nur `.prt`-Namen und Ordner unter dem KFV-Pfad; Originaldateien bleiben unverändert.
- Beispiele mit mehreren Codes, zusammengesetzten Maßtokens, Sprache, unbekannten Tokens und fehlenden Feldern werden automatisiert getestet.
- Für die spätere NX-GUI sind Trefferliste, keine Treffer, nicht erreichbarer Share, Auswahl/Abbruch und Platzierung an einer unkritischen Baugruppe zu prüfen.
- Konstrukteure bestätigen oder korrigieren die Namenstoken, bevor daraus verbindliche Merkmale oder eine ECTR-Klassifizierung werden.
- ECTR-A05 bis A08 werden im ECTR-Repo separat geprüft. Ein NX-Batchtest ersetzt keine ECTR-Abnahme.