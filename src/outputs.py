from pathlib import Path
import json
import subprocess
import shutil

from json2args.logger import logger
import gzip
import base64
from typing import Dict, Any
import pandas as pd

def compress_dataset(datasets: Dict[str, Any], index_column: str, observation_column: str, simulation_column: str) -> str:
    """
    Compress catchment datasets for embedding in HTML.
    
    This function prepares the dataset dictionary for compression and embedding.
    The datasets are converted to a JSON-serializable format, then compressed using gzip,
    and finally base64-encoded for safe embedding in JavaScript.
    
    Returns:
        Base64-encoded, gzip-compressed string of the dataset JSON
    
    Example structure of datasets dict before compression:
        {
            "DE110000": {
                "index": ["2020-01-01", "2020-01-02", ...],
                "observation": [1.2, 1.5, ...],
                "simulation": [1.3, 1.4, ...]
            },
            ...
        }
    """
    json_payload = {}

    for name, df in datasets.items():
        index = df[index_column]
        observation = df[observation_column].tolist()
        simulation = df[simulation_column].tolist()

        if pd.api.types.is_datetime64_any_dtype(index):
            index = index.dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
        else:
            index = index.tolist()

        json_payload[name] = {
            "index": index,
            "observation": observation,
            "simulation": simulation
        }
    
    # convert to compact JSON string
    json_string = json.dumps(json_payload, separators=(',', ':'))
    compressed = gzip.compress(json_string.encode('utf-8'))

    # base64 encoding
    compressed_string = base64.b64encode(compressed).decode('utf-8')
    return compressed_string


def create_metrics_output(data_names: list[str], catchment_metrics: Dict[str, Dict[str, float]]) -> None:
    """
    Create metrics output files (CSV and JSON).
    
    This function generates the metrics summary files that are written to /out.
    It's separated from plot generation to allow independent execution.
    
    Args:
        data_names: List of catchment names
        catchment_metrics: Dictionary mapping catchment names to metric dictionaries
    """
    results = []
    for name in data_names:
        if name in catchment_metrics:
            results.append({'Catchment': name, **catchment_metrics[name]})
    
    results_df = pd.DataFrame(results)
    results_df.to_csv("/out/metrics_summary.csv", index=False)
    results_df.to_json("/out/metrics_summary.json", orient="records", indent=4)
    
    logger.info(f"Created metrics output files for {len(results)} catchments")


def create_output_resources_compressed(
    data_names: list[str],
    catchment_datasets: Dict[str, pd.DataFrame],
    catchment_metrics: Dict[str, Dict[str, float]],
    index_column: str,
    observation_column: str,
    simulation_column: str
) -> None:
    """
    Create output resources with compressed dataset embedding.
    
    This function generates the JavaScript modules needed for the Svelte report,
    including the compressed dataset data that will be embedded in the HTML.
    
    Args:
        data_names: List of catchment names
        catchment_datasets: Dictionary mapping catchment names to DataFrames
        catchment_metrics: Dictionary mapping catchment names to metric dictionaries
        index_column: Name of the datetime index column
        observation_column: Name of the observation data column
        simulation_column: Name of the simulation data column
    """
    logger.info("#Tcreate output ressources - simulation evaluation (compressed)")
    report_root = Path("report")
    lib_dir = report_root / "src" / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)

    # 1) Compress the dataset
    compressed_data = compress_dataset(
        catchment_datasets,
        index_column,
        observation_column,
        simulation_column
    )
    
    # 2) Create the compressed dataset module
    # This will contain the base64-encoded, gzip-compressed dataset
    (lib_dir / "dataset_compressed.js").write_text(
        f"export const datasetCompressed = '{compressed_data}';\n",
        encoding="utf-8"
    )

    # 3) Create metrics and names module (unchanged)
    (lib_dir / "report_data.js").write_text(
        "export const names = " + json.dumps(data_names, ensure_ascii=False, separators=(',', ':')) + ";\n"
        "export const metrics = " + json.dumps(catchment_metrics, ensure_ascii=False, separators=(',', ':')) + ";\n",
        encoding="utf-8"
    )

    # 4) Create config module
    (lib_dir / "config.js").write_text(
        'export const config = { title: "Simulation Evaluation Report" };\n',
        encoding="utf-8"
    )

    # 5) Update library barrel to export compressed dataset
    (lib_dir / "index.ts").write_text(
        "export { names, metrics } from './report_data.js';\n"
        "export { datasetCompressed } from './dataset_compressed.js';\n"
        "export { config } from './config.js';\n",
        encoding="utf-8"
    )
    
    logger.info("#Tcreate output ressources - End")


def build_report():
    logger.info("build Report- simulation evaluation")
    try:
        report_src = Path(".") / "report"

        subprocess.run(["npm", "install"], cwd=report_src, check=True)
        subprocess.run(["npm", "run", "build"], cwd=report_src, check=True)

        # creates /out/report.html from gulpfile.js
        subprocess.run(["npx", "gulp", "build"], cwd=report_src, check=True)

        if not Path("/out/report.html").is_file():
            raise FileNotFoundError("Expected bundled report not found: /out/report.html")

        shutil.copy("/out/report.html", "/out/simulation_report.html")

        if not Path("/out/simulation_report.html").is_file():
            raise FileNotFoundError("simulation_report.html was not created")

    except Exception as e:
        logger.exception(f"Failed to build report: {e}")
        raise
