"""Pipeline für unser Team-Projekt: Strombedarfsanalyse.

Aufruf im Team-Image von Tag 4 (im Ordner mit dieser Datei):
docker run --rm --mount "type=bind,src=.,target=/work" team-dev:0.1 python pipeline.py

Hinweise:
- KI-Kennzeichnung (0RWX, https://0rwx.com/): WRITE (AI COLLABORATION).
  Erstellt mit Claude Sonnet 5.5 und Claude Opus 5.5 aus Startnotebook und Vorlage.
- Ungetestet: nur auf Syntax geprüft, nicht gegen die laufenden APIs ausgeführt.
  Vor Verwendung prüfen, auch anhand der Seminarunterlagen.
- Abweichungen vom Startnotebook: Zeitraum fest aus EINSTELLUNGEN (daten_bis
  eingeschlossen) statt "die letzten 104 Wochen"; TEST_WOCHEN ist
  EINSTELLUNGEN["test_wochen"]. Durch die Lags (168 h) fällt die erste Woche weg.
- Datenquellen: Stromverbrauch (Netzlast) von Bundesnetzagentur | SMARD.de,
  Lizenz CC BY 4.0 (https://www.smard.de); Lufttemperatur vom Deutschen
  Wetterdienst über die Bright-Sky-API (https://brightsky.dev).
- Prompts (Anhang: Startnotebook als .py):
  1. "merge this: (pasted) into this: [Vorlage pipeline.py, hier nicht wiederholt]"
  2. "put the disclaimers in the python as well"
  3. "can you rewrite it for the same structure, but shorter using the same
     libraries? put all prompts in the disclaimer"
"""
import hashlib
import json
import os
import pickle
import platform
from datetime import datetime, timezone
import requests
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_percentage_error, root_mean_squared_error

__version__ = "0.1.0"

# Alle Einstellungen an einer Stelle. Den Datenzeitraum fest eintragen.
EINSTELLUNGEN = {"seed": 42, "daten_von": "2025-01-01", "daten_bis": "2025-12-31", "test_wochen": 8}
STAEDTE = {"Hamburg": (53.55, 9.99), "Berlin": (52.52, 13.40), "Köln": (50.94, 6.96),
           "Frankfurt": (50.11, 8.68), "München": (48.14, 11.58)}  # Temperatur: Mittel
SMARD = "https://www.smard.de/app/chart_data/410/DE"  # Filter 410: Netzlast Deutschland
FEATURES = ["stunde", "wochentag", "monat", "temperatur", "last_vor_2_tagen", "last_vor_1_woche"]


def pruefsumme(df):
    """Prüfsumme einer Tabelle. Gleiche Daten ergeben immer dieselbe Zeichenkette."""
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values.tobytes()).hexdigest()


def holen(url, **params):
    antwort = requests.get(url, params=params, timeout=120)
    antwort.raise_for_status()
    return antwort.json()


def laden():
    """Lädt Netzlast (SMARD) und Temperatur (DWD) für den Zeitraum aus EINSTELLUNGEN."""
    von = pd.Timestamp(EINSTELLUNGEN["daten_von"], tz="UTC")
    bis = pd.Timestamp(EINSTELLUNGEN["daten_bis"], tz="UTC") + pd.Timedelta(days=1)

    # SMARD: Wochenpakete, eine Woche früher beginnen
    ms = lambda t: t.timestamp() * 1000
    pakete = [ts for ts in holen(f"{SMARD}/index_hour.json")["timestamps"]
              if ms(von - pd.Timedelta(weeks=1)) <= ts < ms(bis)]
    last = pd.concat(pd.DataFrame(holen(f"{SMARD}/410_DE_hour_{ts}.json")["series"],
                                  columns=["zeit", "last_mwh"]) for ts in pakete).dropna()
    last["zeit"] = pd.to_datetime(last["zeit"], unit="ms", utc=True)
    last = last.drop_duplicates("zeit").set_index("zeit").sort_index()

    # Bright Sky: Stücke von 180 Tagen, sonst lehnt der Server manchmal ab
    grenzen = [d.strftime("%Y-%m-%d") for d in sorted({*pd.date_range(von, bis, freq="180D"), bis})]

    def temperatur(lat, lon):
        w = pd.concat(pd.DataFrame(holen("https://api.brightsky.dev/weather", lat=lat, lon=lon,
                                         date=a, last_date=b)["weather"])
                      for a, b in zip(grenzen, grenzen[1:]))
        w["zeit"] = pd.to_datetime(w["timestamp"], utc=True)
        return w.drop_duplicates("zeit").set_index("zeit")["temperature"]

    temp = pd.concat([temperatur(*k) for k in STAEDTE.values()], axis=1).mean(axis=1).rename("temperatur")
    df = last[(last.index >= von) & (last.index < bis)].join(temp, how="inner")
    return df, {"quelle": "SMARD.de (CC BY 4.0), Filter 410; DWD über Bright Sky",
                "von": df.index.min().isoformat(), "bis": df.index.max().isoformat(),
                "zeilen": len(df), "sha256": pruefsumme(df)}


def vorbereiten(daten):
    """Merkmale bauen (nur am Vortag bekannte Werte) und zeitlich in Training und Test teilen."""
    lokal = daten.index.tz_convert("Europe/Berlin")
    df = daten.assign(stunde=lokal.hour, wochentag=lokal.dayofweek, monat=lokal.month,
                      last_vor_2_tagen=daten["last_mwh"].shift(48),
                      last_vor_1_woche=daten["last_mwh"].shift(168)).dropna()
    test = df.index > df.index.max() - pd.DateOffset(weeks=EINSTELLUNGEN["test_wochen"])
    return {"X_train": df.loc[~test, FEATURES], "X_test": df.loc[test, FEATURES],
            "y_train": df.loc[~test, "last_mwh"], "y_test": df.loc[test, "last_mwh"]}


def trainieren(teile):
    """Trainiert das Modell auf den Trainingsdaten und gibt es zurück."""
    return HistGradientBoostingRegressor(random_state=EINSTELLUNGEN["seed"]).fit(teile["X_train"], teile["y_train"])


def bewerten(modell, teile):
    """MAPE und RMSE für Modell und naive Prognose (wie vor einer Woche zur selben Stunde)."""
    y = teile["y_test"]
    prognosen = {"modell": modell.predict(teile["X_test"]), "naiv": teile["X_test"]["last_vor_1_woche"]}
    masse = {"mape": mean_absolute_percentage_error, "rmse": root_mean_squared_error}
    return {f"{p}_{m}": f(y, wert) for p, wert in prognosen.items() for m, f in masse.items()}


def speichern(modell, metadaten, ziel="models"):
    """Speichert Modell und Metadaten nebeneinander im Ordner models."""
    os.makedirs(ziel, exist_ok=True)
    with open(os.path.join(ziel, "modell.pkl"), "wb") as f:
        pickle.dump(modell, f)
    with open(os.path.join(ziel, "modell.json"), "w", encoding="utf-8") as f:
        json.dump(metadaten, f, indent=2, ensure_ascii=False)


def main():
    daten, datenstand = laden()
    print("Datenstand:", datenstand)
    teile = vorbereiten(daten)
    modell = trainieren(teile)
    kennzahlen = bewerten(modell, teile)
    for name, wert in kennzahlen.items():
        print(f"{name}: {wert:.4f}")

    metadaten = {
        "erstellt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "code": __version__,
        "daten": datenstand,
        "einstellungen": EINSTELLUNGEN,
        "kennzahlen": {name: round(float(wert), 4) for name, wert in kennzahlen.items()},
        "umgebung": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__,
            "prozessor": platform.machine(),
        },
    }
    speichern(modell, metadaten)
    print("Gespeichert: models/modell.pkl und models/modell.json")


if __name__ == "__main__":
    main()
