import os
from datetime import datetime as dt
from time import time
from pathlib import Path

from json2args import get_parameter
from json2args.data import get_data_paths
from json2args.logger import logger

from evaluation import process_data_and_metrics, load_data
from outputs import create_output_resources_compressed, create_metrics_output, build_report

# parse parameters with correct section
kwargs = get_parameter(section="simulation_evaluation", typed=True)
datapaths = get_data_paths(section="simulation_evaluation")

# check if a toolname was set in env
toolname = os.environ.get('TOOL_RUN', 'simulation_evaluation').lower()

# switch the tool
if toolname == 'simulation_evaluation':
    logger.info("#TOOL START - simulation evaluation")
    logger.debug(f"Passed parameters: {kwargs}")
    start = time()

    # Handle simulation and observation data paths
    sim_data_dir = Path(datapaths["simulation_data"])
    #obs_data_dir = Path(datapaths.get("observation_data", "")) if "observation_data" in datapaths else None

    # Load data explicitly using provided parameters
    data = load_data(
        simulation_path=sim_data_dir,
        observation_path=sim_data_dir,
        index_column=kwargs.index_column,
        observation_column=kwargs.observation_column,
        simulation_column=kwargs.simulation_column
    )
    
    data_names = list(data.keys())
    t2 = time()
    logger.debug(f"Loaded {len(data)} datasets in the {sim_data_dir} folder after {t2 - start:.2f} seconds: [{', '.join(data_names)}]")

    # Process data
    catchment_metrics, catchment_datasets = process_data_and_metrics(
        data,
        index_column=kwargs.index_column,
        observation_column=kwargs.observation_column,
        simulation_column=kwargs.simulation_column
    )
    
    t3 = time()
    logger.debug(f"Processed datasets in {t3 - t2:.2f} seconds")
    
    # Create metrics output files
    create_metrics_output(data_names, catchment_metrics)
    t3a = time()
    logger.debug(f"Created metrics output in {t3a - t3:.2f} seconds")

    # Create output resources with compressed datasets
    create_output_resources_compressed(
        data_names,
        catchment_datasets,
        catchment_metrics,
        kwargs.index_column,
        kwargs.observation_column,
        kwargs.simulation_column
    )
    t4 = time()
    logger.debug(f"Created output resources in {t4 - t3a:.2f} seconds")
    
    
    build_report()
    t5 = time()
    logger.debug(f"Built report in {t5 - t4:.2f} seconds")
    
    logger.info("#TOOL FINISHED")
    logger.info(f"total runtime: {time() - start:.2f} seconds.")

else:
    raise AttributeError(f"[{dt.now().isocalendar()}] Either no TOOL_RUN environment variable available, or '{toolname}' is not valid.\n")
