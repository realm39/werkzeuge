# Werkzeuge

Drei Anwendungen, die **vollständig im Browser** laufen — ohne Server, ohne Anmeldung,
ohne dass Daten das Gerät verlassen.

**→ [realm39.github.io/werkzeuge](https://realm39.github.io/werkzeuge/)**

| | |
|---|---|
| **[Kamera-Scan](kamera.html)** | Bildfolge aufnehmen, Schärfe und Bewegung live messen, Paket für die 3D-Rekonstruktion mit [LingBot-Map](https://github.com/Robbyant/lingbot-map) herunterladen |
| **[Berichtshelfer](berichtshelfer.html)** | Zeugnisbemerkungen und Entwicklungsberichte für alle Schularten und Bundesländer — 399 Formulierungen, Word-Export |
| **[KI-Präsentation](praesentation.html)** | Wie ein Sprachmodell lernt — mit vier Live-Demos, die im Browser rechnen |

## Warum ohne Server

Alle drei Anwendungen arbeiten mit Daten, die niemanden sonst etwas angehen:
Kamerabilder, Einschätzungen über Kinder, Unterrichtsmaterial. Deshalb gibt es
hier **keinen Server, an den etwas gesendet werden könnte**.

Probe: WLAN ausschalten — alles funktioniert weiter.

## Technisch

* Je eine HTML-Datei, keine Abhängigkeiten, kein Build
* Der Berichtshelfer bringt seine Schrift als eingebettetes Subset mit (10 KB)
* Der Kamera-Scan baut sein ZIP-Paket selbst, ohne Fremdbibliothek
* Die Präsentation trainiert ihre Sprachmodelle live im Browser

## Tests

```bash
python3 test_pages.py
```

27 Prüfungen über einen lokalen Dateiserver — genau so, wie GitHub Pages ausliefert.
Geprüft werden Kameraaufnahme, Messwerte, ZIP-Inhalt und dass **keine einzige externe
Ressource** nachgeladen wird.

## Der dazugehörige Agent

Diese Seiten können sich optional mit einem lokal laufenden Agenten verbinden
(Adresse und Zugangstoken auf der Kameraseite eintragen). Der Agent selbst liegt
in einem eigenen Repository und läuft nicht hier — GitHub Pages führt kein Python aus.
