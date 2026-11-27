# Data Ingest Architecture: Load Forecasting (DE)

**Core idea:** one small connector per source, an immutable raw layer, a validated layer, and an orchestrator that runs it all idempotently. Start simple (Parquet files plus Dagster), and add complexity only through ADRs.

## 1. Flow

```
[Sources] -> [Connectors] -> RAW (immutable Parquet) -> VALIDATED (typed, UTC, checked) -> FEATURE-READY
 SMARD        1 class per      as received + metadata     Pandera/Pydantic contracts        joined by valid_time
 ENTSO-E      source           (source, ingested_at,      gap/unit/DST checks               for training + inference
 DWD/ERA5                      issue_time, hash)
 Calendar
 Redispatch
          \__________ orchestrated by Dagster (schedules, backfills, retries) __________/
```

This follows the medallion pattern (raw, cleaned, curated): https://www.databricks.com/glossary/medallion-architecture

## 2. Sources

| Group | Source | Use | Connector help |
|---|---|---|---|
| Load (target) | SMARD, ENTSO-E | training + lags | https://www.smard.de/ ; https://transparency.entsoe.eu/ ; https://github.com/EnergieID/entsoe-py |
| Production (solar, wind, forecasts) | SMARD, ENTSO-E | residual load | same as above |
| Redispatch | netztransparenz.de | grid state | https://www.netztransparenz.de/ |
| Weather (temperature, radiation/cloud, wind, humidity) | DWD Open Data: measurements and forecasts; ERA5: reanalysis for history | training = measured, inference = forecast | https://opendata.dwd.de/ ; https://wetterdienst.readthedocs.io/ ; https://cds.climate.copernicus.eu/how-to-api |
| Calendar | `holidays` library, school-holiday calendars | features | https://github.com/vacanza/holidays |
| Optional later | Day-ahead prices, Destatis/Eurostat | price model, long-term | https://www-genesis.destatis.de/ ; https://ec.europa.eu/eurostat/web/main/data/web-services |
| Pre-built | Open Power System Data | quick start | https://open-power-system-data.org/ |

Smart Grid data and Redispatch appear in both Load and Production in your notes. Treat them as one connector each, with a `category` column.

## 3. Rules that prevent most bugs

1. **Three timestamps:** `valid_time` (what the value is about), `issue_time` (when a forecast was made), `ingested_at`. Without `issue_time`, you leak the future into training.
2. **Train/serve skew:** weather is trained on measurements/ERA5 but served with forecasts. Store both as separate datasets and track the difference.
3. **UTC everywhere** in storage; convert to local time only in features (DST).
4. **Idempotent loads:** each run overwrites its own partition (`source/date=YYYY-MM-DD/`). Re-runs and backfills are then safe.
5. **Raw is never edited.** Fix problems in the validated layer.
6. **Validate at the boundary:** schema, units (MW vs MWh), gaps, duplicates, ranges. ENTSO-E gaps are known, so make gap handling explicit.

## 4. SOLID mapping (https://en.wikipedia.org/wiki/SOLID)

- **S:** fetch, validate, and store are separate functions or classes.
- **O:** a new source means a new class, with no changes to the pipeline.
- **L/I:** every connector satisfies one small interface.
- **D:** the pipeline depends on the interface, not on `requests` or S3.

```python
from typing import Protocol
import pandas as pd

class Source(Protocol):
    name: str
    def fetch(self, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame: ...

class SmardLoad:
    name = "smard_load"
    def fetch(self, start, end):
        ...  # call API, return raw frame
```

## 5. Stack and layout

- **Orchestration:** Dagster, asset-based and beginner friendly (https://docs.dagster.io/). Alternatives go in an ADR.
- **Storage:** Parquet (https://parquet.apache.org/docs/) on object storage or local disk; query with DuckDB (https://duckdb.org/docs/).
- **Contracts:** Pandera (https://pandera.readthedocs.io/); Pydantic for configs (https://docs.pydantic.dev/).
- **Quality checks (optional):** https://docs.greatexpectations.io/
- **Config and secrets:** env vars, never in code (https://12factor.net/).

```
repo/
  docs/adr/            # decisions (MADR template: https://adr.github.io/madr/)
  src/ingest/
    sources/           # smard.py, entsoe.py, dwd.py, era5.py, calendar.py
    contracts/         # schemas per dataset
    storage/           # parquet writer, paths
    assets.py          # Dagster assets
  tests/               # fake sources, schema tests
```

## 6. First ADRs to write

1. Orchestrator (Dagster vs Prefect vs cron).
2. Storage format and location.
3. Time handling (UTC, `valid_time`/`issue_time`).
4. Weather training source (ERA5 vs DWD measurements).
5. Gap-handling policy.

## 7. Azure Well-Architected mapping (https://learn.microsoft.com/en-us/azure/well-architected/)

- **Reliability:** retries with backoff, idempotent runs, alerts on missing partitions.
- **Security:** API tokens (ENTSO-E needs one) in a secret store.
- **Cost:** incremental loads, partitioned Parquet.
- **Operational excellence:** CI tests, ADRs, run logs.
- **Performance:** only load new windows.

## 8. Learning path for new engineers

- https://github.com/DataTalksClub/data-engineering-zoomcamp
- https://github.com/DataTalksClub/mlops-zoomcamp
- https://docs.dagster.io/ (start with the tutorial)

## Uncertain points (verify)

- SMARD has no official API documentation that I can confirm. Check the SMARD site for the current download/API route.
- The Redispatch data location on netztransparenz.de should be checked against its current data catalog.
- I did not verify current terms of use, rate limits, or the ENTSO-E token process. Read each source's terms before building.
- No source here was retrieved live, so confirm the URLs still resolve.

0RWX: WRITE (AI COLLABORATION) if you review and edit it; EXECUTE (AI MADE) if adopted unreviewed.

Model: Claude Sonnet 5.5
