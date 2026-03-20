"""
Auto-generates /in/input.json by inspecting the files present in /in.
Detects column names directly from the data files.

Detection logic:
  Mode 0 - only /in contains data files (no obs/ or sim/ subdirs, no combined files)
  Mode 1 - /in/obs/ and /in/sim/ subdirectories both exist
  Mode 2 - /in contains exactly two data files (one obs, one sim combined)
"""

import json
import pandas as pd
from pathlib import Path

IN = Path("/in")
EXTENSIONS = {".csv", ".parquet"}

def data_files(path):
    return [f for f in path.iterdir() if f.is_file() and f.suffix in EXTENSIONS]

def read_columns(file):
    if file.suffix == ".parquet":
        return pd.read_parquet(file, engine="pyarrow").columns.tolist()
    return pd.read_csv(file, nrows=0).columns.tolist()

def find_column(columns, keyword):
    return next((c for c in columns if keyword in c.lower()), None)

def detect_and_write():
    obs_dir = IN / "obs"
    sim_dir = IN / "sim"

    if obs_dir.is_dir() and sim_dir.is_dir():
        # Mode 1: separate per-location files
        obs_cols = read_columns(data_files(obs_dir)[0])
        sim_cols = read_columns(data_files(sim_dir)[0])
        index_col = obs_cols[0]
        obs_col   = next(c for c in obs_cols if c != index_col)
        sim_col   = next(c for c in sim_cols if c != index_col)
        suffix    = data_files(sim_dir)[0].suffix
        config = {
            "data": {
                "simulation_data": f"/in/sim/*{suffix}",
                "observation_data": f"/in/obs/*{suffix}",
            }
        }

    else:
        files = data_files(IN)
        if len(files) == 2:
            # Mode 2: two combined files
            obs_file = next((f for f in files if "obs" in f.name.lower()), files[0])
            sim_file = next((f for f in files if f != obs_file), files[1])
            obs_cols = read_columns(obs_file)
            sim_cols = read_columns(sim_file)
            index_col    = obs_cols[0]
            location_col = find_column(obs_cols, "catchment") or find_column(obs_cols, "id") or obs_cols[1]
            obs_col      = next(c for c in obs_cols if c not in [index_col, location_col])
            sim_col      = next(c for c in sim_cols if c not in [index_col, location_col])
            config = {
                "parameters": {"location_column": location_col},
                "data": {
                    "simulation_data": f"/in/{sim_file.name}",
                    "observation_data": f"/in/{obs_file.name}",
                }
            }

        else:
            # Mode 0: per-location files with both columns
            cols      = read_columns(files[0])
            index_col = cols[0]
            obs_col   = find_column(cols, "obs") or cols[1]
            sim_col   = find_column(cols, "sim") or cols[2]
            suffix    = files[0].suffix
            config = {
                "data": {"simulation_data": f"/in/*{suffix}"}
            }

    output = {"simulation_evaluation": {"parameters": {
        "index_column": index_col,
        "observation_column": obs_col,
        "simulation_column": sim_col,
        **config.pop("parameters", {})
    }, **config}}

    out_path = IN / "input.json"
    out_path.write_text(json.dumps(output, indent=2))
    print(f"Wrote {out_path}")
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    detect_and_write()