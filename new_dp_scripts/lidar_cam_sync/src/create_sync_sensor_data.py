import argparse
from curses import raw
import json
import os
import shutil
from socket import close
import pandas as pd
from datetime import datetime
import logging
import time

import rosbag

#The Class in this script will read the timestamps from all the rosbags for every sensor(eg: camera, radar, lidar) and create a csv file with the timestamps of all the sensors.
#The timestamps are in milliseconds. Each row of the csv file will have the timestamp of all the sensors at that particular time. The lidar timestamps are the reference timestamps to which the other sensor timestamps are synchronized.
#First the lidar timestamps are read and checked for the time difference between consecutive timestamps. If the time difference is greater than 200ms
#then there is a missing timestamp and it will be compensated by adding the missing timestamp with the previous timestamp + 100ms. The column "lidar_inserted" will be set to 1 for the inserted timestamps and 0 for the original timestamps.
#Next, each of the order sensors timestamps are read and for each lidar timestamp, the closest sensor timestamp is found and added to the csv file. Now if a sensor timestamp is repeated, then the column "sensor_name_inserted" will be set to 1 for the inserted timestamps and 0 for the original timestamps.
#Once all the sensor timestamps are added to the csv file, the csv file is saved in the output folder. 
#All input folders and output folders are read from the config file. The config file should be in the json format.
#Each Raw data folder is synchronized one by one and the csv file is created for each folder.
#At the end of each folder processing, a summary of number of missing timestamps and number of inserted timestamps are printed for each sensor.
#The summary is also saved in the output folder.

class SensorTimestampSynchronizer:
    def __init__(self, raw_data_folder_name, parent_folder_path,sensors_to_sync, sensor_config, output_folder_path):
        self.raw_data_folder_name = raw_data_folder_name
        self.parent_folder_path = parent_folder_path
        self.sensors_to_sync = sensors_to_sync
        self.sensor_config = sensor_config
        self.output_folder_path = os.path.join(output_folder_path, self.raw_data_folder_name, 'processed')
        if not os.path.exists(self.output_folder_path):
            os.makedirs(self.output_folder_path, exist_ok=True)
        if not os.path.exists(os.path.join(self.output_folder_path, 'logs')):
            os.makedirs(os.path.join(self.output_folder_path, 'logs'), exist_ok=True)
        self.sync_file_save_path = os.path.join(self.output_folder_path, 'synced_sensor_timestamps.csv')
        
        self.sync_dict = self.init_sync_dict()
        self.sensor_timestamps = {}
        self.setup_logger()



    def setup_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    
        file_handler = logging.FileHandler(os.path.join(self.output_folder_path, 'logs','sensor_timestamp_synchronizer_{}.log'.format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))))
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    
    def init_sync_dict(self):
        sync_dict = {}
        for sensor in self.sensors_to_sync:
            sync_dict[sensor] = []
            if sensor != 'lidar':
                sync_dict[sensor+'_timestamp_diff'] = []
                sync_dict[sensor+'_inserted'] = []
        return sync_dict
    
    def sync_all_sensors(self):

        for sensor in self.sensors_to_sync:
            self.sync_sensor(sensor)
        self.logger.info("Saving the synchronized timestamps to csv file")
        self.create_5FPS_synced_timestamps()
        self.save_sync_dict_to_csv()
    
    def sync_sensor(self, sensor):
        if sensor == 'lidar':
            self.sync_lidar()
        else:
            self.sync_individual_sensor(sensor)
        
    def sync_lidar(self):
        #Read all the lidar bags and get the timestamps and store in sync_dict['lidar'], then calculate the time difference between consecutive timestamps and if the time difference is greater than 200ms, 
        #then add the missing timestamp as previous + current timestamp/2. Also add the missing timestamp to the sync_dict with inserted column as 1.

        lidar_timestamps = self.retreive_timsestamps('lidar')
        self.sync_dict['lidar'] = lidar_timestamps
        self.logger.info("Lidar timestamps retrieved")
        self.logger.info(f"Total lidar timestamps: {len(lidar_timestamps)}") # type: ignore

    def sync_individual_sensor(self, sensor):
        #Read all the camera bags and get the timestamps and store in sync_dict[camera], then for each lidar timestamp, find the closest camera timestamp and add it to the sync_dict with inserted column as 1.
        sensor_timestamps = self.retreive_timsestamps(sensor)
        self.sensor_timestamps[sensor] = sensor_timestamps
        self.logger.info(f"{sensor} timestamps retrieved")
        self.logger.info(f"Total {sensor} timestamps: {len(list(self.sensor_timestamps[sensor]))}")
        self.find_closest_timestamps_to_lidar(sensor)


    def retreive_timsestamps(self, sensor):
        sensor_folder = os.path.join(self.parent_folder_path, self.raw_data_folder_name, self.sensor_config[sensor]['dir'])
        sensor_files = os.listdir(sensor_folder)
        if not sensor_files:
            self.logger.error(f"No {sensor} files found in the folder: {sensor_folder}")
            return
        sensor_files = [f for f in sensor_files if f.endswith('.bag')]
        sensor_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
        sensor_timestamps = []
        for sensor_file in sensor_files:
            sensor_file_path = os.path.join(sensor_folder, sensor_file)
            self.logger.info(f"Processing {sensor} file: {sensor_file}")
            bag = rosbag.Bag(sensor_file_path)
            topic_name = self.sensor_config[sensor]['topic']
            for topic, msg, t in bag.read_messages(topics=[topic_name]):  # type: ignore 
                timestamp_nsecs = str(msg.header.stamp.nsecs)
                # if nsecs has less than 9 digits, add zeros to the front 
                if len(str(msg.header.stamp.nsecs)) < 9:
                    timestamp_nsecs = str(msg.header.stamp.nsecs).zfill(9)
                full_timestamp = str(msg.header.stamp.secs) + timestamp_nsecs
                timestamp_ms = int(int(full_timestamp)/1e6)
                sensor_timestamps.append(timestamp_ms)     
        return sensor_timestamps
    
    def find_closest_timestamps_to_lidar(self, sensor):

        sensor_timestamps = self.sensor_timestamps[sensor]
        lidar_timestamps = self.sync_dict['lidar']
        closest_sensor_timestamps = []
        sensor_inserted = []
        sensor_timestamp_diff_with_lidar = []

        for lidar_timestamp in lidar_timestamps:
            closest_timestamp = min(sensor_timestamps, key=lambda x: abs(x-lidar_timestamp))
            if closest_timestamp in closest_sensor_timestamps:
                sensor_inserted.append(1)
            else:
                sensor_inserted.append(0)
            closest_sensor_timestamps.append(closest_timestamp)
            sensor_timestamp_diff_with_lidar.append(abs(closest_timestamp-lidar_timestamp))
        self.sync_dict[sensor] = closest_sensor_timestamps
        self.sync_dict[sensor+'_inserted'] = sensor_inserted
        self.sync_dict[sensor+'_timestamp_diff'] = sensor_timestamp_diff_with_lidar
        self.logger.info(f"Closest {sensor} timestamps found for lidar timestamps")
    
    def create_5FPS_synced_timestamps(self):
        #Use camera timestamps to create 5FPS timestamps since it is at 5FPS and other sensors are greater
        self.sync_dict_5FPS = {}
        reference_camera_timestamps = self.sensor_timestamps['front_left']
        self.sync_dict_5FPS['front_left'] = reference_camera_timestamps
        for sensor in self.sensors_to_sync:
            if sensor == 'front_left':
                continue
            self.sync_dict_5FPS[sensor] = []
            self.sync_dict_5FPS[sensor+'_timestamp_diff'] = []

        for cam_timestamp in reference_camera_timestamps:
            for sensor in self.sensors_to_sync:
                if sensor == 'front_left':
                    continue
                closest_sensor_timestamp = min(self.sync_dict[sensor], key=lambda x: abs(x-cam_timestamp))
                self.sync_dict_5FPS[sensor].append(closest_sensor_timestamp)
                self.sync_dict_5FPS[sensor+'_timestamp_diff'].append(abs(closest_sensor_timestamp-cam_timestamp))
        self.logger.info("5FPS synced timestamps created")

    def save_sync_dict_to_csv(self):
        df = pd.DataFrame(self.sync_dict)
        df.to_csv(self.sync_file_save_path, index=False)
        self.logger.info(f"Saved the synchronized timestamps to csv file: {self.sync_file_save_path}")
        if self.sync_dict_5FPS:
            df_5FPS = pd.DataFrame(self.sync_dict_5FPS)
            df_5FPS.to_csv(os.path.join(self.output_folder_path, 'synced_sensor_timestamps_5FPS.csv'), index=False)
            self.logger.info(f"Saved the 5FPS synchronized timestamps to csv file: {os.path.join(self.output_folder_path, 'synced_sensor_timestamps_5FPS.csv')}")
        # self.print_summary()
    
    def print_summary(self):
        for sensor in self.sensors_to_sync:
            sensor_timestamp_diff = self.sync_dict[sensor+'_timestamp_diff']
            self.logger.info(f"Summary for sensor: {sensor}")
            self.logger.info(f"Average timestamp difference: {sum(sensor_timestamp_diff)/len(sensor_timestamp_diff)}")
            print(f"Summary for sensor: {sensor}")
            print(f"Average timestamp difference: {sum(sensor_timestamp_diff)/len(sensor_timestamp_diff)}")

def read_config_file(path):
        with open(path) as json_file:
            data = json.load(json_file)
        return data

def get_folders_to_process(folder_list_file):
    with open(folder_list_file, 'r') as file:
        folders = file.readlines()
        if not folders:
            raise Exception("No folders to process")
        folders = [f.strip() for f in folders]
    return folders

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Sensor Timestamp Synchronizer')
    parser.add_argument('--config', type=str, help='Path to the config file', required=True)
    args = parser.parse_args()
    config_file = args.config
    config_data = read_config_file(config_file)
    folders_to_process_path = config_data['folders_to_process_path']
    raw_data_folders = get_folders_to_process(folders_to_process_path)
    raw_data_parent_folder = config_data['raw_data_parent_folder']
    sensors_to_sync = config_data['sensors_to_sync']
    sensor_config_path = config_data['sensor_config_file_path']
    output_folder_path = config_data['output_folder_path']
    sensor_config = read_config_file(sensor_config_path)
    
    for folder in raw_data_folders:
        
        print(f"Processing folder: {folder}")
        sensor_sync = SensorTimestampSynchronizer(folder, raw_data_parent_folder, sensors_to_sync, sensor_config, output_folder_path)
        sensor_sync.logger.info("Sensor Timestamp Synchronizer started")
        sensor_sync.sync_all_sensors()
    sensor_sync.logger.info("Sensor Timestamp Synchronizer completed")
    print("Sensor Timestamp Synchronizer completed")