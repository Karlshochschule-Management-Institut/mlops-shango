# Shango-Power-Prediction

Our model predicts the expected electricity demand for the next day.
Users who need a simple electricity demand forecast.

## Daten

- Quelle: https://www.smard.de/app/chart_data/410/DE
- Lizenz oder Nutzungsbedingungen: <zum Beispiel CC BY 4.0>
- Zeitraum: <von bis, fest eingetragen in EINSTELLUNGEN>
- Umfang: <Zeilen, Stunden oder Issues>
- Prüfsumme: <die ersten 8 Zeichen von sha256 aus models/modell.json>

## Voraussetzungen

- Docker (Docker Desktop, unter Linux auch die Docker Engine)
- <Internet für den Download der Daten? Ein Token? Wie lange dauert ein Lauf?>

## Reproduzieren

Im Ordner mit diesem README. Jeden Befehl so hinschreiben, dass man ihn kopieren kann.

```
docker build -t <team-name>:0.1 .
docker run --rm --mount "type=bind,src=.,target=/work" <team-name>:0.1 python pipeline.py
```

Nur Linux: Kommt beim Schreiben in models `Permission denied`, läuft der Container als Benutzer mit der Nummer 1000 und eurer Benutzer hat eine andere (`id -u`). Dann vor dem Image-Namen `--user "$(id -u)" -e HOME=/tmp` ergänzen.

## Erwartetes Ergebnis

| Kennzahl | Wert | Erlaubte Abweichung |
| --- | --- | --- |
| <Modell, zum Beispiel MAPE> | <Wert> | <zum Beispiel ± 0,2 Prozentpunkte> |
| <einfache Prognose> | <Wert> | <...> |

<Warum kann die Zahl abweichen? Zum Beispiel: Die Quelle ergänzt alte Daten, anderer Prozessor.>

<Wo liegen Modell und Metadaten nach dem Lauf?>

## Aufbau

| Datei | Aufgabe |
| --- | --- |
| `pipeline.py` | <...> |
| `requirements.txt` | <...> |
| `Dockerfile` | <...> |

## Grenzen und bekannte Abweichungen

- <Was kann das Modell nicht?>
- <Was kann sich beim Nachbauen unterscheiden, und warum?>

## Team

<Namen>
