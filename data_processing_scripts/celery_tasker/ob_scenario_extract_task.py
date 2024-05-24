import json
import time
import logging
import os
from celery import Celery
import pandas as pd

from get_object_based_scenarios import Object_Based_Scenario_Extractor

#Configuration filepath
TASI_CONFIG="/home/abinmath@ads.iu.edu/TASI/TASI-ESCOOTER/data_processing_scripts/celery_tasker/config_abin_desktop_gpu.json"

# Redis connection details (replace with your values)
BROKER_URL = "redis://:tasi12345!@134.68.77.118:6379/0" 
RESULT_BACKEND = "redis://:tasi12345!@134.68.77.118:6379/0"

# Celery app configuration
app = Celery("ob_scenario_extract_task", broker=BROKER_URL, backend=RESULT_BACKEND)
# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_raw_data_location(video_name, raw_data_tasi_vru1, raw_data_tasi_vru2):
    vru_path2 = os.path.join(raw_data_tasi_vru2, video_name,"processed", "synchronized_timestamps","synchronized_timestamps.csv")
    if os.path.exists(vru_path2):
        return raw_data_tasi_vru2
    return raw_data_tasi_vru1
    

@app.task(bind=True)
def extract_ob_scenario(self, video_name):
    logger.info(f"Processing video: {video_name}")
    # Load the configuration file
    with open(TASI_CONFIG, 'r') as f:
        config = json.load(f)
    if not config:
        logger.error("Error loading configuration file")
        return "Error loading configuration file"
    raw_data_tasi_vru1 = config['raw_data_tasi_vru1']
    raw_data_tasi_vru2 = config['raw_data_tasi_vru2']
    ob_scenario_click_folder = config['ob_scenario_click_folder']
    destination_folder = config['destination_folder']

    raw_data_folder_path = check_raw_data_location(video_name, raw_data_tasi_vru1, raw_data_tasi_vru2)
    print(f"Raw data folder path: {raw_data_folder_path}")

    # Load the scenario file
    ob_scenarios_path = os.path.join(ob_scenario_click_folder, video_name, "object_based_scenarios.csv")
    ob_scenarios_df = pd.read_csv(ob_scenarios_path)

    scenario_count = 0
    video_start_time = time.time()
    all_status = []
    #Process all the scenarios
    for index, row in ob_scenarios_df.iterrows():
        scenario_start_time = time.time()
        scenario_start = row['Start Time']
        scenario_end = row['Stop Time']
        scenario_count += 1
        raw_data_video_folder = os.path.join(raw_data_folder_path, video_name)
        
        extractor = Object_Based_Scenario_Extractor(video_name, raw_data_video_folder, scenario_count, scenario_start, scenario_end, destination_folder, self)
        status = extractor.extract_scenario()
        all_status.append(status)
        scenario_duration = (time.time() - scenario_start_time)/60
        print(f"Processed scenario {scenario_count} in {scenario_duration} mins")

    video_duration = (time.time() - video_start_time)/60
    logger.info(f"Processed video: {video_name} in {video_duration} mins")
    print(f"Processed video: {video_name} in {video_duration} mins")
    print(all_status)
    if set(all_status) == {"Done"}:
        return "All scenarios success"
    else:
        num_failed = len(all_status) - all_status.count("Done")
        raise Exception(f"Failed {num_failed} scenarios out of {len(all_status)}. Check Logs")
        