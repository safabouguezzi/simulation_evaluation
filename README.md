# Simulation Evaluation

A containerized tool for evaluating hydrological simulations against observations across multiple catchments. It computes standard performance metrics and produces an interactive HTML report with time series plots and statistical summaries.

## How it works

For each catchment, the tool:
1. Auto-detects the input mode from the structure of `/in`
2. Loads observation and simulation time series
3. Computes performance metrics (NSE, KGE, R², MSE, RMSE)
4. Writes a metrics summary to `/out`
5. Generates a self-contained interactive HTML report

---

## Input data

The tool supports three input structures, **auto-detected** at runtime — no `input.json` or mode parameter needed. Just mount your data in `/in` with the right structure.

### Mode 0 — per-location files, both columns in one file

```
/in/
  discharge_5694.csv    ←  columns: date, obs, sim
  discharge_8731.csv
```

### Mode 1 — per-location files, separate obs and sim

```
/in/
  obs/
    discharge_5694.csv    ←  columns: date, obs
    discharge_8731.csv
  sim/
    discharge_5694.csv    ←  columns: date, sim
    discharge_8731.csv
```

Catchments are matched by the last `_`-delimited segment of the filename (`discharge_5694.csv` → `5694`).

### Mode 2 — two combined files, all catchments

```
/in/
  all_observations.csv    ←  columns: date, catchment_id, obs
  all_simulations.csv     ←  columns: date, catchment_id, sim
```

The tool detects Mode 2 when exactly two data files are present in `/in`. It identifies obs vs sim from the filename (expects `obs` to appear in the observation filename). The location column is assumed to be named `catchment_id`.

---

## Column name defaults

The auto-detection script writes `input.json` with these default column names:

| Parameter | Default |
|---|---|
| `index_column` | `date` |
| `observation_column` | `obs` |
| `simulation_column` | `sim` |
| `location_column` | `catchment_id` *(Mode 2 only)* |

If your files use different column names, edit `/in/input.json` after the container starts, or provide your own `input.json` before running — the auto-detection will skip writing a new one if it detects one already exists.

---

## Outputs

| File | Description |
|---|---|
| `/out/metrics_summary.csv` | Per-catchment metrics table |
| `/out/metrics_summary.json` | Same data in JSON format |
| `/out/simulation_report.html` | Self-contained interactive report |

---

## References

**Data:** CAMELS-DE — hydrometeorological time series for 1582 German catchments.
A. Dolich et al. https://doi.org/10.5281/zenodo.13837553

**Model:** Hy2DL — Hybrid Hydrological modeling using Deep Learning.
Eduardo Acuña Espinoza et al. https://github.com/KIT-HYD/Hy2DL/tree/v1.1


