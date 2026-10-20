# BO4E-Schema-Viewer

Übersichtliche Offline-Ansicht des BO4E-Schemas von
[conuti-gmbh/bo4e-schema](https://github.com/conuti-gmbh/bo4e-schema).

Ein kleines Python-Skript lädt den aktuellen Stand des Schemas direkt von GitHub und erzeugt daraus eine
einzige HTML-Datei. Die Datei öffnet man im Browser – ohne Server, ohne Installation, ohne weitere Abhängigkeiten.
Sie zeigt alle Business-Objekte, Komponenten, Enums und Container mit ihren Feldern, Typen und Beschreibungen,
lässt verschachtelte Objekte direkt aufklappen und durchsuchen und ist rein lesend.

## Voraussetzungen

- Windows mit Python 3.10 oder neuer (nur Standardbibliothek, kein `pip install` nötig)
- Internetzugang zu `api.github.com` beim Erzeugen
- Browser: Edge oder Chrome

## Einrichten und Starten

1. Repo klonen oder als ZIP herunterladen und entpacken.
2. `aktualisieren.bat` doppelklicken.

Das Skript lädt den Stand von `master`, erzeugt `output/BO4E-Schema-Viewer.html` und öffnet die Datei.
Danach lässt sich die HTML-Datei jederzeit direkt öffnen und auch weitergeben.

## Aktualisieren

`aktualisieren.bat` erneut ausführen. Es wird nur dann etwas heruntergeladen, wenn es auf GitHub einen neuen
Commit gibt; der geladene Stand liegt in `cache/`. Welcher Stand angezeigt wird (Commit, Datum), steht oben
rechts im Viewer.

- Ohne Internetverbindung wird der zuletzt geladene Stand aus `cache/` verwendet (Hinweis ⚠ in der Kopfzeile).
  Beim allerersten Lauf ist eine Verbindung nötig.
- Bestimmten Stand anzeigen: `aktualisieren.bat --ref <Branch|Tag|Commit>`
- Andere Ausgabedatei: `aktualisieren.bat --out <datei.html>`

Direkt mit Python: `python build_viewer.py [--ref …] [--repo …] [--out …]`

### GitHub-Token (optional)

Das Schema-Repo ist öffentlich, ein Token ist nicht nötig. Ohne Token erlaubt GitHub 60 Abfragen pro Stunde,
was für normale Nutzung reicht. Wer häufiger aktualisiert, kann einen Token hinterlegen (Fine-grained, nur Lesezugriff):
Umgebungsvariable `BO4E_GITHUB_TOKEN`, `GITHUB_TOKEN` oder `GH_TOKEN`, Eintrag `github_token` in `settings.json`,
oder automatisch über `gh auth token`, wenn die GitHub-CLI angemeldet ist.

### settings.json (optional)

Im Tool-Ordner anlegen, alle Einträge sind optional:

```json
{ "bo4e_repo": "conuti-gmbh/bo4e-schema", "bo4e_ref": "master", "github_token": "" }
```

`settings.json` ist per `.gitignore` vom Einchecken ausgeschlossen.

## Bedienung

| Was | Wie |
|---|---|
| Objekt öffnen | Liste links (Filter, Art BO/COM/ENUM/CDOC) oder Typ-Link in der Tabelle |
| Suche über alles | Feld oben (Taste `/`): Objekte, Felder, Enum-Werte, Beschreibungen und `$comment`. `↑` `↓` `Enter` |
| Verschachtelte Objekte | ▸ klappt BO/COM direkt in der Tabelle auf. „+1 Ebene“ klappt alle sichtbaren eine Ebene weiter auf, „Alle zuklappen“ |
| In Struktur suchen | Durchsucht den ganzen Baum des Objekts (bis 10 Ebenen) und zeigt nur Treffer mit ihrem Pfad |
| Feldpfad kopieren | ⧉ kopiert z. B. `lokationsadresse.postleitzahl` (Listen mit `[]`), mit `Shift` inkl. Objektname |
| Enum-Werte | Erscheinen in der Typ-Spalte (max. 8, alle im Tooltip); Enum öffnen für die vollständige Liste |
| Verwendet in | Direkte Verwendung je Feld und – für COM/ENUM – kürzester Pfad aus jedem BO, das es indirekt enthält |
| Beispiel / Roh-JSON | Beispiel aus `docs/examples` (nur BO) bzw. Original-Schema; `$ref` im Roh-JSON sind klickbar |
| DE / EN | Bezeichner (Objekte, Felder, Enum-Werte) aus `translation/v1/DE_to_EN.yaml`; Beschreibungen bleiben deutsch |
| faker | Checkbox in der Struktur blendet die Testdaten-Hinweise ein |
| Design | 🌞 hell / 🦈 dunkel oben rechts, wird im Browser gemerkt |

Jede Ansicht hat eine eigene Adresse, z. B. `…/BO4E-Schema-Viewer.html#bo/Marktlokation?f=lokationsadresse.postleitzahl`
oder `#enum/Netzebene/werte?v=MSP`. Lesezeichen und Browser-Zurück funktionieren.

Die Übersichtsseite (Logo anklicken) zeigt Kennzahlen und listet Auffälligkeiten im Schema, z. B. `$ref` auf fehlende Dateien.

## Aufbau

| Datei | Zweck |
|---|---|
| `aktualisieren.bat` | Erzeugt den Viewer neu und öffnet ihn |
| `build_viewer.py` | Holt den Stand von GitHub, liest Schemas, Übersetzung und Beispiele, erzeugt die HTML |
| `template.html` | Oberfläche; die Daten werden beim Erzeugen eingebettet |
| `conuti-logo.png` | Logo für die Kopfzeile |
| `cache/` | Geladene Stände (aktueller und vorheriger) mit `current.json` – wird nicht eingecheckt |
| `output/BO4E-Schema-Viewer.html` | Ergebnis – wird nicht eingecheckt |
