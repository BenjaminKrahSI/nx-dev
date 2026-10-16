# Git-Arbeitsweise (ectr-dev / nxopen-dev)

Gilt für beide Repositorys. Werkzeug: VS Code, Ansicht **Quellcodeverwaltung** (Strg+Umschalt+G).

## Grundregeln

1. **Ein Stand = ein Commit, nicht eine Dateikopie.** Keine `_NEU`, `_alt`, `_v2`, `(1)`. Die alte Fassung steckt in der Historie.
2. **Eine Datei pro Makro/Werkzeug.** Varianten (z. B. anderer `DOCUMENT_TYPE`) sind Parameter am Dateianfang, keine zweite Datei.
3. **Kleine Commits mit klarer Nachricht.** Ein Commit = eine Absicht. Nachricht im Format `Bereich: was und warum`, z. B.
   `wkv: Smart-List-Ausgabe optional, Standard bleibt Objektliste`.
4. **Erst Ist-Stand committen, dann ändern.** Gilt besonders für ECTR-Konfiguration unter `config/`.
5. **Nicht ins Repo:** Passwörter, CAD-Daten (`.prt`), `node_modules`, generierte Dateien mit persönlichen Pfaden. Die `.gitignore` regelt das.
6. **Abends pushen.** Erst nach dem Push liegt der Stand auf dem Firmenserver (= Backup).

## Täglicher Ablauf in VS Code

| Schritt | Wo | Was |
|---|---|---|
| Arbeitsbeginn | Statusleiste unten links | Synchronisieren-Pfeil anklicken (holt Änderungen vom Server) |
| Arbeiten | Editor | Wie bisher |
| Prüfen | Quellcodeverwaltung | Geänderte Datei anklicken → Vergleich alt/neu |
| Festhalten | Quellcodeverwaltung | `+` bei den gewünschten Dateien, Nachricht eintragen, **Commit** |
| Sichern | Quellcodeverwaltung | **Änderungen synchronisieren** bzw. **Push** |

## Rollout nach ECTR / NX kennzeichnen (Tag)

Wenn ein Stand produktiv geht (Makro in ECTR-Dokument kopiert, NX-Tool verteilt):

```
git tag -a wkv-0kb-1.0 -m "Rollout P01, ECTR-Dok. <Dokumentnummer>/<Teil>/<Version>"
git push --tags
```

So ist jederzeit nachvollziehbar, welcher Quellstand in welchem ECTR-Dokument steckt.

## Größere Änderung ausprobieren (Branch)

Nur wenn ein funktionierender Stand weiterlaufen muss, während etwas Riskantes entsteht:

1. Statusleiste unten links auf den Branch-Namen `main` klicken → **Neuen Branch erstellen** → z. B. `tdo-neue-abfrage`.
2. Dort arbeiten und committen.
3. Fertig: zurück auf `main` wechseln, Befehlspalette (Strg+Umschalt+P) → **Git: Branch zusammenführen** → `tdo-neue-abfrage`.
4. Verworfen: Branch einfach löschen, `main` ist unberührt.

## Notfälle

| Situation | Lösung |
|---|---|
| Datei kaputt editiert, noch nicht committet | Quellcodeverwaltung → Rechtsklick auf Datei → **Änderungen verwerfen** |
| Alten Stand einer Datei ansehen | Datei öffnen → Explorer-Bereich **Zeitachse** (unten) → Eintrag anklicken |
| Letzten Commit falsch beschriftet, noch nicht gepusht | Quellcodeverwaltung → `…` → **Commit** → **Letzten Commit rückgängig machen**, neu committen |
| Neu klonen auf anderem PC | `git clone <URL>`, danach NX: `py setup.py` · ECTR: `Setup.cmd` |