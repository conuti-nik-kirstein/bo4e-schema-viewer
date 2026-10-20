# BO4E-Schema-Viewer

Offline-Ansicht des BO4E-Schemas aus [conuti-gmbh/bo4e-schema](https://github.com/conuti-gmbh/bo4e-schema),
aufgebaut wie der Schema-Editor im MIG-Mapping-Service (Objektliste links, Feldtabelle rechts), aber nur zum Lesen.

## Einrichten

Repo klonen, dann `aktualisieren.bat` doppelklicken (Windows, Python 3.10+). Das erzeugt
`output/BO4E-Schema-Viewer.html` und öffnet sie. `cache/` und `output/` werden nicht eingecheckt.

## Öffnen

`output/BO4E-Schema-Viewer.html` im Browser öffnen (Edge/Chrome). Kein Server, kein Internet nötig.
Die Datei lässt sich weitergeben, z. B. über OneDrive/Teams.

## Aktualisieren

`aktualisieren.bat` doppelklicken. Das Skript prüft den aktuellen Commit auf GitHub, lädt nur bei einem neuen
Stand das Archiv (`schemas/`, `translation/`, `docs/examples/`) nach `cache/<commit>/`, erzeugt die HTML neu
und öffnet sie. Der aktive Stand (Commit, Datum) steht oben rechts in der Kopfzeile.

- Ohne Verbindung: letzter Stand aus `cache/`, sonst eine lokale Kopie des Schema-Repos (Hinweis ⚠ in der Kopfzeile).
  Gesucht wird `MACOAPP/bo4e-schema-master` (wenn das Tool unter `MACOAPP/Tools/` liegt), dann `../bo4e-schema`
  und `../bo4e-schema-master` neben diesem Ordner; anderer Pfad über `--lokal` oder `bo4e_local_path`.
- Nur lokale Kopie: `aktualisieren.bat --quelle lokal`
- Bestimmten Stand festnageln: `aktualisieren.bat --ref <Branch|Tag|Commit>`
- Token ist nicht nötig (Repo öffentlich), hilft aber gegen das Rate-Limit von 60 Abfragen/h:
  `BO4E_GITHUB_TOKEN` / `GITHUB_TOKEN` / `GH_TOKEN`, `github_token` in `settings.json` oder automatisch `gh auth token`.

Python 3.10+ (nur Standardbibliothek). Direkt: `python build_viewer.py [--quelle github|lokal] [--ref …] [--out …]`.

Optionale `settings.json` im Tool-Ordner:

```json
{ "quelle": "github", "bo4e_repo": "conuti-gmbh/bo4e-schema", "bo4e_ref": "master",
  "bo4e_local_path": "", "github_token": "" }
```

## Bedienung

| Was | Wie |
|---|---|
| Objekt öffnen | Liste links (Filter, Art), oder Typ-Link in der Tabelle |
| Suche über alles | Feld oben (Taste `/`): Objekte, Felder, Enum-Werte, Beschreibungen/`$comment`. `↑` `↓` `Enter` |
| Verschachtelte Objekte | ▸ klappt BO/COM in der Tabelle auf. „+1 Ebene“ klappt alle sichtbaren eine Ebene weiter auf, „Alle zuklappen“ |
| In Struktur suchen | Durchsucht den ganzen Baum des Objekts (bis 10 Ebenen) und zeigt nur Treffer mit Pfad |
| Feldpfad kopieren | ⧉ kopiert z. B. `lokationsadresse.postleitzahl` (Listen mit `[]`), mit `Shift` inkl. Objektname |
| Enum-Werte | Werden in der Typ-Spalte angezeigt (max. 8, alle im Tooltip); Enum öffnen für die vollständige Liste |
| Verwendet in | Direkte Verwendung je Feld und – für COM/ENUM – kürzester Pfad aus jedem BO, das es indirekt enthält |
| Beispiel / Roh-JSON | Beispiel aus `docs/examples` (nur BO) bzw. Original-Schema; `$ref` im Roh-JSON sind klickbar |
| DE / EN | Bezeichner (Objekte, Felder, Enum-Werte) aus `translation/v1/DE_to_EN.yaml`; Beschreibungen bleiben deutsch |
| faker | Checkbox in der Struktur blendet die Testdaten-Hinweise ein |
| Design | 🌞 hell / 🦈 Shark Mode oben rechts, wird im Browser gemerkt |

Jede Ansicht hat eine eigene Adresse, z. B. `…/BO4E-Schema-Viewer.html#bo/Marktlokation?f=lokationsadresse.postleitzahl`
oder `#enum/Netzebene/werte?v=MSP`. Lesezeichen und Browser-Zurück funktionieren.

Die Übersichtsseite (Logo anklicken) listet Auffälligkeiten im Schema, z. B. `$ref` auf fehlende Dateien.

## Dateien

| Datei | Zweck |
|---|---|
| `build_viewer.py` | Holt den Stand, liest Schemas/Übersetzung/Beispiele, erzeugt die HTML |
| `template.html` | Oberfläche (Daten werden beim Erzeugen eingebettet) |
| `conuti-logo.png` | Logo für die Kopfzeile |
| `cache/` | Geladene GitHub-Stände (aktueller + vorheriger), `current.json` |
| `output/BO4E-Schema-Viewer.html` | Ergebnis |

Eigene Erweiterungen aus dem MIG-Mapping-Service (`schema-extensions`) werden bewusst nicht angezeigt – nur das Original.
