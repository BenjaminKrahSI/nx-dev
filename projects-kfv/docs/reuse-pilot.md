# KFV-Muster: lokaler Reuse-Pilot

**Stand: 16.10.2026, Arbeitsstand zum Tagesabschluss.**

## Kurzfassung und Zielbild

Gesucht ist eine KFV-Musterbibliothek mit Kategorien, Codesuche und Vorschaubildern. Ausgewaehlte Fraesbilder sollen als Legacy-Pattern im Zielteil landen, nicht als Baugruppenkomponenten. Das Wunschbild ist eine seitliche Bibliothek mit Bildkacheln und Drag-and-drop auf das Modell beziehungsweise die Zeichnung.

Der lokale Pilot ist als Einstieg in die native Wiederverwendungsbibliothek eingebunden. Das Ausfuehren des Python-Journals aus dieser Bibliothek oeffnet unseren Suchdialog; dies wurde vom Anwender mit Screenshot bestaetigt. Echtes Drag-and-drop mit eigener Pattern-Platzierungsaktion ist dadurch noch nicht nachgewiesen.

## Bestaetigter Stand und offene Abnahme

| Bereich | Stand / Beleg |
|---|---|
| Start des Piloten ueber Alt+F8 | Vom Anwender als funktionierend bestaetigt. |
| Native Bibliothek KFV-Muster (Pilot) | Im NX-Screenshot sichtbar, Journalstarter wird angeboten. |
| Python-Journalstart aus der Reuse Library | Vom Anwender mit geoeffnetem Suchdialog und Vorschau bestaetigt, auch im Zeichnungskontext sichtbar. |
| Suchkatalog | 1.336 lokale Dateien in der bisherigen Messung; Namen und Pfade, keine fachlich bestaetigte Klassifizierung. |
| Codeauswahl | Im Code sofort wirksamer Zusatzfilter; Kombination mehrerer Codes ueber Suchbausteine. Automatisiert geprueft. |
| Vorschau | Vom Anwender im Pilotdialog sichtbar gezeigt; Bild und Vorschaubereich wurden gegenueber dem ersten Stand verdoppelt. |
| Einfuegen | Komponentenbuilder entfernt, stattdessen UF-Pattern-Import implementiert und mit simulierter NX-API getestet. Vollstaendige Gleichwertigkeit zu Muster (Alt) noch nicht abgenommen. |
| Native Bildkacheln fuer einzelne Pattern mit eigener Drop-Aktion | Nicht implementiert; kein allgemeiner unterstuetzter Hook nachgewiesen. |
| Automatisierte Tests | Letzter vollstaendiger Lauf: 26 Tests, davon 25 erfolgreich und einer mangels KFV_STANDARDS_DIR uebersprungen. Keine echte NX-Session in diesen Tests. |

## Umfang

- Pilotdatei: `Desktop\Test_Standards\Standards\Fraesbild_3ZK_B001_HS3050.prt` im aktuellen Benutzerprofil.
- Bibliotheksordner: `C:\dev\nxopen-dev\projects-kfv\reuse-pilot`.
- Journal: [KFV_Mustersuche.py](../reuse-pilot/KFV_Mustersuche.py). Es startet den vorhandenen [Suchdialog](../standards_search.py) mit einer Namenssuche nach der Pilotdatei.
- Die Originaldatei wird weder kopiert noch gespeichert. Keine Installation und keine Firmenbibliothek wurde veraendert.
- Die Suche bleibt vollstaendig nutzbar: Das Leeren der Startanfrage gibt den restlichen lokalen Testbestand frei.

## In NX ausprobieren

1. Ein unkritisches, beschreibbares Zielteil aktivieren.
2. Falls noch nicht eingebunden: In der Wiederverwendungsbibliothek ueber das Zahnrad die Verwaltung oeffnen und die vorbereitete [KRX-Konfiguration](reuse-pilot-library.krx) ueber Konfiguration laden aufnehmen. Das Haeckchen "Die aktuelle Liste ueberschreiben, wenn die Konfiguration geladen wird" ausgeschaltet lassen. Bestehende Firmenbibliotheken nicht ersetzen. Der Anwender hat diesen Einbindungsweg erfolgreich ausprobiert. Nicht den Standardsordner mit den `.prt`-Dateien als Ersatz fuer den Journalordner aufnehmen.
3. In der Bibliothek `KFV-Muster (Pilot)` das Journal `KFV_Mustersuche` ausfuehren. Dieser Start ist in der aktuellen NX-Konfiguration bestaetigt.
4. Im Suchdialog muss die Anfrage `name:Fraesbild_3ZK_B001_HS3050.prt` stehen. Den passenden Treffer auswaehlen, Musterposition setzen und OK druecken.
5. Pruefen: Legacy-Pattern im Zielteil, keine neue Baugruppenkomponente. Lage, Orientierung, Groesse und Verhalten in Zeichnungen gegen Muster (Alt) vergleichen. Vor dem Speichern das Ergebnis bewerten; die Platzierung besitzt einen Undo-Schritt.

Falls eure Bibliotheksverwaltung ueber eine zentrale KRX-Konfiguration erfolgt, enthaelt `reuse-pilot-library.krx` einen separaten Root-Eintrag fuer diesen Ordner. Den Eintrag nur in eine lokale Kopie der bestehenden Konfiguration uebernehmen und diese ueber die dafuer vorgesehene NX-Kundenkonfiguration aktivieren. Nicht die komplette Firmenkonfiguration durch diese kleine Pilotdatei ersetzen und keine Datei unter der Siemens-Installation ueberschreiben. Der Projektpfad im KRX-Eintrag muss bei einem Umzug angepasst werden.

Zum getrennten Test des Starters kann `reuse-pilot/KFV_Mustersuche.py` auch ueber Alt+F8 gestartet werden. Ein erfolgreicher Alt+F8-Lauf belegt noch nicht den Start aus der Reuse Library.

## Voraussetzungen und Grenzen

Der Ansatz folgt der mitgelieferten Siemens-Bibliothek `Journal File Example Library` (nativer Ordner, Typ 2); deren Beispiele sind VB-Journale und verlangen installierte NX-Programmierwerkzeuge. Der eigene Python-Starter wurde inzwischen im Zeichnungskontext erfolgreich gestartet. Benoetigte Lizenzen fuer eine Verteilung auf weitere Arbeitsplaetze sind noch nicht gesondert geklaert.

Das Platzieren erfolgt ausschliesslich ueber die Pattern-Schnittstelle des bestehenden Suchdialogs. Keine gespeicherten Pattern-Daten oder eine fehlende Python-UF-Schnittstelle fuehren zu einer Meldung, nicht zu einer Komponente. Vorschau-Teile bleiben wie bisher geladen. Der Pilot ist ein Journal-Eintrag mit vorgeschalteter Suche, kein neuer nativer `.prt`-Objekttyp und keine zugesagte Drag-and-drop-Erweiterung.

Die Python-Journalausfuehrung und Anzeige im Zeichnungskontext sind fuer den Rechner des Anwenders inzwischen bestaetigt. Daraus folgt keine allgemeine Aussage zu benoetigten Lizenzen oder anderen NX-Installationen. Im Screenshot wird ausserdem ein `__pycache__`-Ordner in der Bibliothek angeboten; dessen Ausblendung beziehungsweise Vermeidung ist noch offen.

## Warum der Komponentenweg falsch war

Das vom Anwender bereitgestellte NX-Log zeigt den Legacy-Befehl `UG_ARRANGE_PATTERN` mit den Dialogen `Patterns`, `Retrieve Pattern`, Dateiauswahl und anschliessender Punktpositionierung. Dabei wurden WCS, Massstab 1 und Auto Scale verwendet. Das ist nicht der Vorgang des Hinzufuegens einer Baugruppenkomponente.

Der fruehere `CreateAddComponentBuilder`-Aufruf erzeugte eine Komponente und wurde deshalb entfernt. Der neue Pfad verwendet `NXOpen.UF.UFSession.GetUFSession().Patt.Import`:

- Quelle: die ausgewaehlte `.prt`-Datei mit gespeicherten Pattern-Daten.
- Patternname: Dateiname ohne Erweiterung.
- Transformation: neun Werte fuer die Zielteil-WCS-Orientierung, drei fuer die gewaehlte Position, ein Wert fuer Massstab 1.
- Autoskalierung bei unterschiedlichen Einheitensystemen: eingeschaltet (Option 1).
- Ziel: aktives Work Part; eine aktive Baugruppe ist nicht erforderlich.
- Undo: eigener Schritt; bei Importfehlern wird eine Ruecknahme versucht.
- Keine automatische Speicherung und kein Komponenten-Fallback.

Quelle fuer diese Semantik ist die installierte NX-2412-Datei `UGOPEN/uf_patt.h`: `uc5823` ist als `UF_PATT_import` gewrappt und liest Pattern-Daten als ein Pattern-Objekt. Die installierte Managed-API-Dokumentation nennt die Bindung `UFPatt.Import`. Python-Verhalten und Gleichwertigkeit zur interaktiven Funktion muessen weiterhin am echten Zielteil bewertet werden.

Im Log erscheinen Fehler 641044 zu drei nicht gefundenen Teilen bereits vor dem Pilotlauf. Diese Meldungen nicht ohne weitere Analyse dem Pattern-Import zurechnen. Auch `Could not find object` vor `OpenBase` kann zur Suche nach einem noch nicht geladenen Preview-Teil gehoeren; im gezeigten Log wurde die betreffende lokale Datei anschliessend geladen.

## Suche und Kategorien

Der [Dateikatalog](../standards_catalog.py) liest rekursiv `.prt`-Namen und relative Ordner. Die primaere Kategorie entsteht ausschliesslich aus dem Dateinamen. Die erste passende Regel gewinnt, in dieser Reihenfolge: Fraesbilder, Senkungen, Treibstangen, Zusatzkaesten, Hauptschloesser, Zeichnungsvorlagen, Sonstiges. Ein Fraesbild mit HS-Code bleibt deshalb in Fraesbilder. Kategorien sind Suchhilfen, keine freigegebenen technischen Merkmale und kein Nachweis gespeicherter Pattern-Daten.

Codegruppen enthalten vorlaeufig erkannte Varianten-/Familiencodes, Seriencodes, Masscodes, Sprach- und Zusatzmarker sowie weitere Namensteile. Die Definitionen muessen Anwender bestaetigen, insbesondere die gemeinsame Gruppe fuer beispielsweise B001, T0 und 4ZK. `neu` und `alt` sind keine Freigabestatus.

- Kategorie und Suchanfrage bilden den Grundfilter. Die Codeauswahl zeigt dazu passende Werte mit Dateianzahl.
- Auswaehlen eines Codes filtert sofort zusaetzlich; andere passende Codewerte bleiben waehlbar.
- `Baustein hinzufuegen` schreibt den Code in die Suchanfrage. Weitere Bausteine werden mit UND verknuepft.
- Beispiel: `serie:HS4050 mass:92E`. Codefilter sind exakt; 92E findet nicht 192E.
- Alternativen innerhalb eines Begriffs: `familie:B001|B002`. Platzhalter: `*` fuer beliebig viele, `?` fuer ein Zeichen.
- Freitext sucht Teilzeichenfolgen in Namen, Pfaden und abgeleiteten Suchfeldern, nicht in NX-Attributen, Excel oder SAP-/ECTR-Beschreibungen.
- Das breite NX-String-Control muss ueber `WideValue` gelesen und geschrieben werden. Das vorherige Lesen von `Value` erklaerte die trotz sichtbarer Anfrage ungefilterte Trefferliste.
- `Suchen` wendet die Anfrage explizit an; `Suche zuruecksetzen` leert Anfrage und Codeauswahl und setzt die Kategorie zurueck.

## Performance und Datenzugriff

Eine Messung ausserhalb von NX mit Python 3.14 ergab fuer den lokalen Bestand rund 55 ms fuer den Namensscan und 3 ms fuer eine beispielhafte Suche. Das ist keine Messung der gesamten Fensteroeffnungszeit in NX. Deren vom Anwender beobachtete Verzoegerung ist weiterhin nicht aufgeschluesselt.

Nur beim Oeffnen und bei `Standards aktualisieren` wird neu gescannt; Filter arbeiten im Speicher. Hoechstens 300 Treffer werden angezeigt. Teil und gespeichertes Preview werden erst beim Anklicken geladen. Preview-Teile bleiben geladen, da NX sie beim Laden als geaendert melden kann; ihr automatisches Schliessen wurde deshalb vermieden.

Ein CSV-Cache wurde bisher bewusst nicht eingebaut: Der lokale Namensscan ist schnell, ein Cache kann veralten. Falls ein spaeterer Share-Scan langsam wird, benoetigt ein Index mindestens relative Pfade, eine eindeutige Quellenzuordnung und einen definierten Aktualisierungsablauf; Dateinamen allein reichen nicht. Der vorhandene CSV-Export ist kein Cache.

## Recherche: native Reuse Library und Drag-and-drop

Untersucht wurden die mit NX 2412 installierten C++-Header, UF-Header, Reuse-Beispiele, KRX-Dateien und ein Beispiel fuer eigene Ressourcenleisten-Tabs. Es wurde kein Eingriff in Siemens- oder Firmenkonfigurationen vorgenommen. Ein nicht gefundener Hook ist kein Beweis technischer Unmoeglichkeit.

| Ansatz | Beleg | Bewertung |
|---|---|---|
| Nativer Ordner mit Journalstarter | `NXPARTS/Reuse Library/Journal File Example Library`; Root-Eintrag Typ 2; eigener Live-Pilot | Funktionierender Einstieg in unseren Dialog. |
| Bilder in Reuse-Metadaten | KRX-Beispiel `Hex Bolt, AI.krx` mit `KnowledgeReuse/ItemData/DetailImage`; separate BMP/JPG-Dateien in Reuse-Beispielen | Bilder fuer native Objekte belegt. Bildkacheln fuer Python-Journale und deren Erzeugung nicht live verifiziert. |
| `Tooling.ReuseLibraryNavigator` und `ReuseLibraryNavigatorNode` | Installierte Header markieren die Schnittstellen als intern und jederzeit aenderbar | Kein belastbarer oeffentlicher Erweiterungspunkt fuer einen neuen Pattern-Drop-Handler. |
| `BlockStyler.Tree`-Drag-and-drop | Callbacks nennen Quell- und Zielknoten | Betrifft Baumknoten, belegt keinen Drop auf Modell oder Zeichnungsflaeche. |
| `LineDesigner.ReuseLibraryDragData` | Spezialisierte API mit Lizenzanforderung `ld_line_designer` | Kein nachgewiesener allgemeiner Pattern-Hook; nicht als Umweg eingeplant. |
| Eigene seitliche Palette | Oeffentliche Windows-API `ResourceBarManager`: `Create`, `RegisterActivationCallback`, `GetWindowHandle` | Unterstuetzter Weg zu einem eigenen NX-Ressourcenleisten-Tab mit gehostetem Fenster. |
| Siemens-Palettenbeispiel | `UGOPEN/SampleNXOpenApplications/C++/CustomResourceBarTab/CustomResourceBarTab.cpp` | Konkrete Grundlage fuer einen eigenen Tab; kein bereits fertiger Pattern-Browser. |

Das Anlegen einer weiteren KRX-Kategorie allein ersetzt die Standard-Platzierung einer `.prt` nicht durch `UF.Patt.Import`. Die Ressourcenleisten-API liefert einen Fensterplatz, aber keinen automatischen grafischen Drop-Punkt. Auch fuer eine eigene Palette bleibt echtes Drag-and-drop deshalb ein gesonderter Machbarkeitsnachweis.

Zusaetzlicher Online-Abgleich: [UFPatt-API-Referenz, NX2022.1](https://nxopencsdocumentation.thescriptingengineer.com/NX2022_1/NXOpen.UF.UFPatt.html). Dies ist eine extern gehostete, aeltere .NET-Referenz; fuer NX 2412 wurden vorrangig die lokal installierten Siemens-Dateien verwendet.

## Empfohlener Wiedereinstieg

1. Den funktionierenden lokalen Journal-Piloten als Rueckfalloption erhalten. Keine interne Navigator-API und keine unbelegte KRX-Option einbauen.
2. Pattern-Import an einem unkritischen Zielteil gegen Muster (Alt) abnehmen: Objekttyp statt Komponente, Zielteil, Position, Orientierung, Massstab, Einheiten, Zeichnungs-/Ansichtsabhaengigkeit, Undo und Abbruch. Fehlende Pattern-Daten ebenfalls pruefen.
3. Mit dem Anwender drei typische Suchaufgaben und erwartete Dateien sammeln; Kategorien, Codegruppen und Schreibvarianten fachlich korrigieren.
4. Fuer Kategorien und Bildkacheln einen eigenen Ressourcenleisten-Tab nach dem Siemens-Beispiel untersuchen. Erster Ablauf: Bild anklicken, Punkt waehlen, Pattern importieren. Bestehenden Katalog und Importpfad wiederverwenden; noch kein Framework oder Add-in angelegt.
5. Fuer echtes natives Drag-and-drop eine gezielte Siemens-Supportfrage stellen: Gibt es in NX 2412 einen freigegebenen Handler fuer eigene Reuse-Eintragstypen, der Datei und Drop-Position sowie Zielteil/Ansicht bereitstellt und einen UF-Pattern-Import statt Komponentenplatzierung erlaubt?
6. Vor Performance-Umbauten die NX-Zeiten getrennt messen: Dialogerzeugung, Initialisierung, Scan, Listenaufbau und Preview-Laden.

## Zugehoerige Unterlagen

- [Prozess- und Variantenkontext](variantenkonfiguration-kfv.md)
- [Bearbeitbare Anwender-Kurzanleitung](standardsuche-kurzanleitung.html)
- [PDF fuer die Anwender-Vorstellung](standardsuche-kurzanleitung.pdf): Export liegt vor; die letzte Druck-/Layoutpruefung konnte in dieser Sitzung nicht abschliessend bestaetigt werden. Fuer inhaltliche Aktualitaet diese Doku und die HTML-Fassung heranziehen.