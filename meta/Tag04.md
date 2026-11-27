# Tag 4: Container

Material für Tag 4. Entpacken Sie lab4.zip in Ihrem Ordner Kurs, neben dem Ordner mlops-kurs-block1. In VS Code öffnen Sie dann mit File, Open Folder den Ordner `Kurs`. Im Terminal wechseln Sie zuerst in den Ordner, den Sie gerade brauchen, am Vormittag mit `cd lab4/taxi`.

Unter Windows legt „Alle extrahieren“ oft einen Ordner lab4 im Ordner lab4 an. Dann heißt der Befehl `cd lab4/lab4/taxi`. Prüfen Sie mit `ls`: Im richtigen Ordner sehen Sie `train.py` und `requirements.txt`.

| Ordner | Wofür | Wann |
| --- | --- | --- |
| `taxi/` | Annas Training als Skript (Stand nach Tag 2). Daraus bauen wir gemeinsam ein Image. | Vormittag |
| `taxi/loesung/` | Das fertige Dockerfile, falls Sie beim Mitmachen nicht mitkommen | Vormittag |
| `team/` | Startnotebooks für die drei Use Cases und die Pakete für Ihr Entwicklungs-Image | Gruppenarbeit |

## Voraussetzung

Docker läuft: Docker Desktop ist gestartet, unter Linux mit Docker Engine läuft Docker als Dienst (falls nicht: `sudo systemctl start docker`). Prüfen Sie im Terminal von VS Code:

```
docker run hello-world
```

Es soll unter anderem „Hello from Docker!“ erscheinen. Meldet Linux `permission denied` beim Zugriff auf docker.sock: einmal `sudo usermod -aG docker $USER`, dann ab- und wieder anmelden.

## Befehle vom Vormittag

Im Terminal von VS Code. Die Befehle sind unter macOS, Linux und in der Windows-PowerShell gleich. Ein neues Terminal steht im Ordner `Kurs`, darum zuerst in den Ordner taxi wechseln.

```
cd lab4/taxi
docker build -t taxi-train:0.1 .
mkdir models
docker run --rm --mount "type=bind,src=./models,target=/app/models" taxi-train:0.1
docker run --rm -e MONAT=2024-02 --mount "type=bind,src=./models,target=/app/models" taxi-train:0.1
```

Erwartung: RMSE rund 5,07 Minuten für Januar 2024. Das Modell liegt danach im Ordner `models`.

## Datenquellen der Startnotebooks

- Strombedarf: Bundesnetzagentur | SMARD.de (CC BY 4.0) und Deutscher Wetterdienst über die Bright-Sky-API
- GitHub-Issue-Triage: GitHub-API, Issues des Projekts pandas
- Predictive Maintenance: NASA C-MAPSS (Saxena u. a., PHM08, 2008), Download über data.nasa.gov
