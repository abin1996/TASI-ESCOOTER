import copy
import csv
from datetime import datetime
import json
from logging import config
import os
from random import sample
import shutil 
import numpy as np
import argparse
import logging
import pandas as pd
import time 
import cv2
from cv_bridge import CvBridge, CvBridgeError  # type: ignore
from pyparsing import col
import rosbag
import pypcd
class Object_Based_Scenario_Extractor:
    def __init__(self, folder_name, raw_data_parent_folder, output_folder_path, sensor_config, temp_folder="./temp_copy_folder", output_additional_fps=5):
        self.folder_dir = os.path.join(raw_data_parent_folder, folder_name)
        self.folder_name = folder_name
        self.sensor_config = sensor_config
        self.processed_folder = os.path.join(self.folder_dir, 'processed')
        self.output_folder_path_parent = output_folder_path
        self.output_folder_path = os.path.join(output_folder_path, folder_name)
        self.clean_up_folder(self.output_folder_path)
        self.temp_folder = temp_folder + '_' + self.folder_name
        self.clean_up_folder(self.temp_folder)
        self.sync = self.find_sync_file()
        self.additional_fps_output = output_additional_fps
        self.folder_names = {
            'camera': sensor_config['camera'].keys(),
            'lidar': sensor_config['lidar'].keys(),
            'radar': sensor_config['radar'].keys(),
            'gps': sensor_config['gps'].keys()
        }
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
        if not os.path.exists(os.path.join(self.output_folder_path_parent, 'logs', self.folder_name)):
            os.makedirs(os.path.join(self.output_folder_path_parent, 'logs', self.folder_name))
        self.file_handler = logging.FileHandler(os.path.join(self.output_folder_path_parent, 'logs', self.folder_name ,'cb_scenario_extraction_{}.log'.format(datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))))
        self.file_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)

        self.logger.info("Folder Path: "+self.folder_dir)


    def close_logger(self):
        self.logger.removeHandler(self.file_handler)
        self.file_handler.close()

    def clean_up_folder(self, folder):
        if os.path.exists(folder):
            os.system("rm -r "+folder)
            os.makedirs(folder)
        else:
            os.makedirs(folder)

    def find_sync_file(self):
        sync_file_path = os.path.join(self.processed_folder, 'synced_sensor_timestamps_5FPS.csv')
        if not os.path.exists(sync_file_path):
            self.logger.error(f"Sync file not found in {self.processed_folder}")
            raise Exception(f"Sync file not found in {self.processed_folder}")
        return pd.read_csv(sync_file_path)
    
    def extract_scenarios(self, scenario_df_path):
        """
        Extract scenarios from the scenario_df
        """
        self.data_status = self.data_structure_check()
        if not self.data_status:
            raise Exception("Data structure not correct")
        
        scenario_df = pd.read_csv(scenario_df_path)
        if len(scenario_df) == 0:
            print("No scenarios present for this folder")
            self.logger.info("No scenarios present for this folder")
            return
        if 'status' not in scenario_df.columns:
            scenario_df['ob_status'] = 'Not Processed'
        elif len(scenario_df[scenario_df['status']=='Done']) == len(scenario_df):
            print("All scenarios processed for this folder")
            self.logger.info("All scenarios processed for this folder")
            return
        for idx, row in scenario_df.iterrows():
            scenario_name = row['Scenario Number']
            print("**Working on Scenario : ", scenario_name)
            self.logger.info("Working on Scenario : "+str(scenario_name))
            if row['ob_status'] == 'Done':
                print("Scenario already processed")
                self.logger.info("Scenario already processed")
                continue

            start = int(row['Start Time'])
            start -= 2
            end = int(row['Stop Time'])
            end += 1
            if len(str(start)) != 13:
                digits = 13 - len(str(start))
                start = start*(10**digits)
            if len(str(end)) != 13:
                digits = 13 - len(str(end))
                end = end*(10**digits)
    
            self.scenario_name = self.folder_name + '_' + str(scenario_name) + '_' + str(int(start/1000)) + '_' + str(int(end/1000))
            self.scenario_output_folder = os.path.join(self.output_folder_path, self.scenario_name)
            
            self.start = start
            self.end = end
            self.logger.info("Start: "+str(self.start))
            self.logger.info("End: "+str(self.end))
            self.logger.info("Duration: "+str((self.end-self.start)/1000)+"s")

            #Extract the scenario
            scenario_extraction_status = self.extract_scenario()

            scenario_df.loc[idx, 'ob_status'] = scenario_extraction_status # type: ignore
            scenario_df.to_csv(scenario_df_path, index=False)
            self.logger.info("Extraction Status for Scenario: "+str(scenario_name) + " is: "+scenario_extraction_status)
        
        self.logger.info("Completed extracting scenarios")
        print("Completed extracting scenarios")

    def data_structure_check(self):
        """
        Check if the folder structure is correct
        """

        if not os.path.exists(self.folder_dir):
            self.logger.error("Raw Data Folder does not exist")
            return False
        if not os.path.exists(self.processed_folder):
            self.logger.error("Processed folder does not exist")
            return False
        if not os.path.exists(self.output_folder_path):
            self.logger.error("Output folder does not exist")
            return False
        if self.sync.empty:
            return False
        
        for sensor_type in self.folder_names.keys():
            for sensor_name in self.folder_names[sensor_type]:
                if not os.path.exists(os.path.join(self.folder_dir, self.sensor_config[sensor_type][sensor_name]['dir'])):
                    self.logger.error(f"Folder for {sensor_name} does not exist")
                    return False

        self.store_bag_indexes()
        return True

    def store_bag_indexes(self):
        self.save_folder_paths = {}
        for sensor_type in self.folder_names.keys():
            for sensor_name in self.folder_names[sensor_type]:
                sensor_dir = os.path.join(self.folder_dir, self.sensor_config[sensor_type][sensor_name]['dir'])
                bag_names = os.listdir(sensor_dir)
                bag_index_filename_dict = {}
                for bag in bag_names:
                    bag_index = int(bag.split('_')[-1].split('.')[0])
                    bag_index_filename_dict[bag_index] = bag
                self.sensor_config[sensor_type][sensor_name]['bag_num_filenames'] = bag_index_filename_dict
                self.save_folder_paths[sensor_name] = os.path.join(self.temp_folder,  self.sensor_config[sensor_type][sensor_name]['output_folder_name'])

    def extract_scenario(self):
        """
        Given a start and end unix timestamp (13digits,milisec), extract the scenario to output folder
        """
        
        self.logger.info("Extracting Scenario: "+str(self.scenario_name))
        print("Extracting Scenario: ", self.scenario_name)
        self.set_clipped_sync_timestamps()
        
        # try:
        time_start = time.time()
        for camera_name in self.folder_names['camera']:
            print("Extracting Camera: ", camera_name)
            self.extract_sensor_data_from_bag_individual('camera',camera_name)
        self.logger.info("Videos Extraction Time: "+str((time.time()-time_start)/60)+" minutes")
        print("Videos Extraction Time: ", (time.time()-time_start)/60, " minutes")
    # except:
    #     self.logger.error("Error extracting videos")
    #     return "Error extracting videos"
    
    # try:
        time_start = time.time()
        print("Extracting LiDAR")
        #Extract LiDAR
        for lidar_sensor_name in self.folder_names['lidar']:
            print("Extracting LiDAR: ", lidar_sensor_name)
            #Extract LiDAR
            self.extract_sensor_data_from_bag_individual('lidar', lidar_sensor_name)
        self.logger.info("LiDAR Extraction Time: "+str((time.time()-time_start)/60)+" minutes")
        print("LiDAR Extraction Time: ", (time.time()-time_start)/60, " minutes")
    # except:
    #     self.logger.error("Error extracting LiDAR")
    #     return "Error extracting LiDAR"
    
    # try:
        time_start = time.time()
        print("Extracting Radar and GPS")
        #Extract Radar and GPS
        for sensor_type in ['radar', 'gps']:
            for sensor_name in self.folder_names[sensor_type]:
                print("Extracting ", sensor_name)
                self.extract_sensor_data_from_bag_combined(sensor_type, sensor_name)
        self.logger.info("Radar and GPS Extraction Time: "+str((time.time()-time_start)/60)+" minutes")
        print("Radar and GPS Extraction Time: ", (time.time()-time_start)/60, " minutes")
    # except:
    #     self.logger.error("Error extracting Radar and GPS")
    #     return "Error extracting Radar and GPS"
    # try:
        time_start = time.time()
        print("Combining cameras")
        self.combine_views()

        self.logger.info("Combining Cameras Time: "+str((time.time()-time_start)/60)+" minutes")
        print("Combining Cameras Time: ", (time.time()-time_start)/60, " minutes")
    # except:
    #     self.logger.error("Error combining views")
    #     return "Error combining views"

    # try:
        #Create N FPS output 
        print("Creating N FPS output")
        self.logger.info("Creating N FPS output")
        self.create_N_FPS_output()
    # except:
    #     self.logger.error("Error creating NFPS output")
    #     return "Error creating N FPS output"
    # try:
        time_start = time.time()
        print("Copying the all the data to output folder")
        shutil.copytree(self.temp_folder, self.scenario_output_folder, dirs_exist_ok=True)
        shutil.rmtree(self.temp_folder)
        self.logger.info("Copying Combined View Time: "+str((time.time()-time_start)/60)+" minutes")
    # except:
    #     self.logger.error("Error copying the combined view to output folder")
    #     return "Error copying the combined view to output folder"

        self.sync_scenario.to_csv(os.path.join(self.scenario_output_folder, 'synced_sensor_timestamps_5FPS.csv'), index=False)

        return "Done"

    def set_clipped_sync_timestamps(self):
        first_camera_name = list(self.folder_names['camera'])[0]
        print("Original Sync Length: ", len(self.sync))  
        self.sync_scenario = self.sync[(self.sync[first_camera_name]>=self.start) & (self.sync[first_camera_name]<=self.end)]
        self.sync_scenario = self.sync_scenario.reset_index(drop=True)
        for sensor_type in self.folder_names.keys():
            for sensor_name in self.folder_names[sensor_type]:
                sync_file_col_name = self.sensor_config[sensor_type][sensor_name]['sync_file_column_name']
                self.sync_scenario[sync_file_col_name+'_file_name'] = ''
        print("Sync Scenario Length(frames): ", len(self.sync_scenario))
        self.logger.info("Sync Scenario Length(frames): "+str(len(self.sync_scenario)))

    #Handles camera and LiDAR data extraction
    def extract_sensor_data_from_bag_individual(self, sensor_type, sensor_name):

        output_folder = self.save_folder_paths[sensor_name]
        sync_file_col_name = self.sensor_config[sensor_type][sensor_name]['sync_file_column_name']       
        start_timestamp_for_camera = self.sync_scenario[sync_file_col_name].iloc[0]
        end_timestamp_for_camera = self.sync_scenario[sync_file_col_name].iloc[-1]

        output_sensor = dict(self.sensor_config[sensor_type][sensor_name])
        output_prefix = output_sensor['output_filename_prefix']
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
        bag_names = os.listdir(os.path.join(self.folder_dir, self.sensor_config[sensor_type][sensor_name]['dir']))
        bag_names = [f for f in bag_names if f.endswith('.bag')]
        bag_names.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
        for bag_name in bag_names:
            bag = rosbag.Bag(os.path.join(self.folder_dir, self.sensor_config[sensor_type][sensor_name]['dir'], bag_name))
            bag_start = int(bag.get_start_time()*1e3) - 1000
            bag_end = int(bag.get_end_time()*1e3) + 1000
            if bag_start > end_timestamp_for_camera or bag_end < start_timestamp_for_camera:
                continue
            for topic, msg, t in bag.read_messages(topics=[self.sensor_config[sensor_type][sensor_name]['topic']]): # type: ignore
                timestamp_nsecs = str(msg.header.stamp.nsecs)
                # if nsecs has less than 9 digits, add zeros to the front 
                if len(str(msg.header.stamp.nsecs)) < 9:
                    timestamp_nsecs = str(msg.header.stamp.nsecs).zfill(9)
                full_timestamp = str(msg.header.stamp.secs) + timestamp_nsecs
                timestamp_ms = int(int(full_timestamp)/1e6)

                if int(timestamp_ms) < start_timestamp_for_camera or int(timestamp_ms) > end_timestamp_for_camera:
                    continue
                unix_ts = str(timestamp_ms)
                
                if sensor_type == 'camera':
                    self.handle_camera_data(msg, unix_ts, sensor_name, output_folder, output_prefix)
                elif sensor_type == 'lidar':
                    self.handle_lidar_data(msg, unix_ts, sensor_name, output_folder, output_prefix)
            bag.close()

    def handle_camera_data(self, msg, timestamp_ms, camera_name, output_folder, output_file_name_prefix):
        frame = CvBridge().imgmsg_to_cv2(msg, desired_encoding="bgr8")
        filename = output_file_name_prefix+'_'+timestamp_ms+'.png'
        frame_name = os.path.join(output_folder, filename)
        cv2.imwrite(frame_name, frame)
        #Add the frame name to the sync_scenario with column name as camera_name_file_name
        sync_file_col_name = self.sensor_config['camera'][camera_name]['sync_file_column_name']
        self.sync_scenario.loc[self.sync_scenario[sync_file_col_name] == int(timestamp_ms), sync_file_col_name+'_file_name'] = filename
        
    
    def handle_lidar_data(self, msg, timestamp_ms, lidar_name, output_folder, output_file_name_prefix):
        pcd = pypcd.PointCloud.from_msg(msg)
        filename = output_file_name_prefix+'_'+timestamp_ms+'.pcd'
        lidar_pcd_name = os.path.join(output_folder,filename)
        pcd.save(lidar_pcd_name)
        #Add the frame name to the sync_scenario with column name as camera_name_file_name
        sync_file_col_name = self.sensor_config['lidar'][lidar_name]['sync_file_column_name']
        self.sync_scenario.loc[self.sync_scenario[sync_file_col_name] == int(timestamp_ms), sync_file_col_name+'_file_name'] = filename
    
    #Handles Radar and  GPS data
    def extract_sensor_data_from_bag_combined(self, sensor_type, sensor_name):
        output_folder = self.save_folder_paths[sensor_name]
        sync_file_col_name = self.sensor_config[sensor_type][sensor_name]['sync_file_column_name']
        if sync_file_col_name not in self.sync.columns:
            start_timestamp_for_camera = self.start
            end_timestamp_for_camera = self.end
        else:
            start_timestamp_for_camera = self.sync_scenario[sync_file_col_name].iloc[0]
            end_timestamp_for_camera = self.sync_scenario[sync_file_col_name].iloc[-1]

        output_timestamp_list = []
        output_message_list = []

        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
        bag_names = os.listdir(os.path.join(self.folder_dir, self.sensor_config[sensor_type][sensor_name]['dir']))
        bag_names = [f for f in bag_names if f.endswith('.bag')]
        bag_names.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
        for bag_name in bag_names:
            bag = rosbag.Bag(os.path.join(self.folder_dir, self.sensor_config[sensor_type][sensor_name]['dir'], bag_name))
            bag_start = int(bag.get_start_time()*1e3) - 1000
            bag_end = int(bag.get_end_time()*1e3) + 1000
            if bag_start > end_timestamp_for_camera or bag_end < start_timestamp_for_camera:
                continue
            for topic, msg, t in bag.read_messages(topics=[self.sensor_config[sensor_type][sensor_name]['topic']]): # type: ignore
                timestamp_nsecs = str(msg.header.stamp.nsecs)
                # if nsecs has less than 9 digits, add zeros to the front 
                if len(str(msg.header.stamp.nsecs)) < 9:
                    timestamp_nsecs = str(msg.header.stamp.nsecs).zfill(9)
                full_timestamp = str(msg.header.stamp.secs) + timestamp_nsecs
                timestamp_ms = int(int(full_timestamp)/1e6)

                if int(timestamp_ms) < start_timestamp_for_camera or int(timestamp_ms) > end_timestamp_for_camera:
                    continue
                unix_ts = str(timestamp_ms)

                output_timestamp_list.append(unix_ts)
                output_message_list.append(str(msg))
            bag.close()
        
        output_sensor_data_csv = pd.DataFrame({'timestamp': output_timestamp_list, 'message': output_message_list})
        output_file_name_prefix = self.sensor_config[sensor_type][sensor_name]['output_filename_prefix']
        output_sensor_data_csv.to_csv(os.path.join(output_folder, output_file_name_prefix+'.csv'), index=False)


    
    def combine_views(self):
        """
        Combines synchronized camera and LiDAR views into a video.

        Parameters:

        """
        # Get the first image from first camera to get the height and width of the image
        first_camera_name = "front_left"
        sample_img_path = self.get_image_path(self.sync_scenario[first_camera_name].iloc[0], first_camera_name)
        sample_img = cv2.imread(sample_img_path)
        height, width, _ = sample_img.shape
        position_map = {
            'front_left': 0,
            'front_right': 1
        }

        for idx, row in self.sync_scenario.iterrows():
        # Initialize a blank image for combining views
            combined_view = np.zeros((height, width * 2, 3), dtype=np.uint8)
            # Read and place synchronized camera images
            for key in self.sensor_config['camera'].keys():
                position = position_map[key]  # Get the position of the camera from the dictionary
                camera_timestamp = row[key]
                img_path = self.get_image_path(camera_timestamp, key)
                img = cv2.imread(img_path)
                img_resized = cv2.resize(img, (width, height))  # Ensure all images are the same size
                #combined view is 2 x 1 for camera images
                combined_view[0:height, (position%2)*width:(position%2+1)*width, :] = img_resized
            #save the combined view
            output_combine_folder = os.path.join(self.temp_folder, 'combined')
            if not os.path.exists(output_combine_folder):
                os.makedirs(output_combine_folder)
            output_path = os.path.join(output_combine_folder, "combined_"+ str(row[first_camera_name])+".jpg")
            cv2.imwrite(output_path, combined_view)

    def get_image_path(self, timestamp, camera_name):
        output_file_name_prefix = self.sensor_config['camera'][camera_name]['output_filename_prefix']
        return os.path.join(self.save_folder_paths[camera_name], output_file_name_prefix+'_'+ str(timestamp)+".png")

    def get_lidar_pcd_path(self, timestamp, lidar_name):
        output_file_name_prefix = self.sensor_config['lidar'][lidar_name]['output_filename_prefix']
        return os.path.join(self.save_folder_paths[lidar_name], output_file_name_prefix+'_'+ str(timestamp)+".pcd")

    def create_N_FPS_output(self):
        n = self.additional_fps_output
        div_factor = int(10/n)
        self.sync_scenario_1FPS = self.sync_scenario.iloc[::div_factor]
        self.output_n_fps_folder = os.path.join(self.temp_folder, '{}FPS'.format(n))
        if not os.path.exists(self.output_n_fps_folder):
            os.makedirs(self.output_n_fps_folder)
        self.sync_scenario_1FPS.to_csv(os.path.join(self.output_n_fps_folder, 'synced_sensor_timestamps_1FPS.csv'), index=False)
        for sensor_type in self.folder_names.keys():
            for sensor_name in self.folder_names[sensor_type]:
                sync_file_col_name = self.sensor_config[sensor_type][sensor_name]['sync_file_column_name']
                if sync_file_col_name not in self.sync_scenario_1FPS.columns or sensor_type == 'gps':
                    continue
                sensor_output_folder = os.path.join(self.output_n_fps_folder, self.sensor_config[sensor_type][sensor_name]['output_folder_name'])
                if not os.path.exists(sensor_output_folder):
                    os.makedirs(sensor_output_folder)
                print("Creating custom FPS output for: ", sensor_name)
                if sensor_type == 'camera':
                    self.create_N_FPS_image_output(sensor_output_folder, sensor_name)
                if sensor_type == 'lidar':
                    self.create_N_FPS_lidar_output(sensor_output_folder, sensor_name)
                if sensor_type == 'radar':
                    self.create_N_FPS_csv_output(sensor_output_folder, sensor_type, sensor_name)
    
    def create_N_FPS_image_output(self, output_folder, camera_name):
        output_prefix = self.sensor_config['camera'][camera_name]['output_filename_prefix']
        for idx, row in self.sync_scenario_1FPS.iterrows():
            timestamp = row[camera_name]
            img_path = self.get_image_path(timestamp, camera_name)
            output_path = os.path.join(output_folder, output_prefix+'_'+str(timestamp)+'.png')
            self.copy_file_to_path(img_path, output_path)
            

    def create_N_FPS_lidar_output(self, output_folder, lidar_name):
        output_prefix = self.sensor_config['lidar'][lidar_name]['output_filename_prefix']
        for idx, row in self.sync_scenario_1FPS.iterrows():
            timestamp = row['lidar']
            pcd_path = self.get_lidar_pcd_path(timestamp, lidar_name)
            output_file_path = os.path.join(output_folder, output_prefix+'_'+str(timestamp)+'.pcd')
            self.copy_file_to_path(pcd_path, output_file_path)
    
    def create_N_FPS_csv_output(self, output_folder, sensor_type, sensor_name):
        csv_file_path = os.path.join(self.save_folder_paths[sensor_name], self.sensor_config[sensor_type][sensor_name]['output_filename_prefix']+'.csv')
        df = pd.read_csv(csv_file_path)
        column_name = self.sensor_config[sensor_type][sensor_name]['sync_file_column_name']
        df_1fps = df[df['timestamp'].isin(self.sync_scenario_1FPS[column_name])]
        df_1fps.to_csv(os.path.join(output_folder, self.sensor_config[sensor_type][sensor_name]['output_filename_prefix']+'.csv'), index=False)
            
    def copy_file_to_path(self, file_path, output_file_path):
        shutil.copy(file_path, output_file_path)

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

if __name__ =="__main__":
    parser = argparse.ArgumentParser(description='Object Based Scenario Extractor Configuration')
    parser.add_argument('--config', type=str, help='Path to the config file', required=True)
    args = parser.parse_args()
    config_file = args.config
    config_data = read_config_file(config_file)
    folders_to_process_path = config_data['folders_to_process_path']
    raw_data_folders = get_folders_to_process(folders_to_process_path)
    raw_data_parent_folder = config_data['source_raw_data_parent_folder']
    scenario_metadata_file_name = config_data['scenario_metadata_file_name']
    scenario_metadata_file_path = config_data['scenario_metadata_file_path']
    output_folder_path = config_data['output_folder_path']
    custom_fps_output = config_data['custom_fps_output']
    sensor_config = config_data['sensor_config']
    
    for folder in raw_data_folders:
        print(f"Processing folder: {folder}")
        scenario_df_path = os.path.join(scenario_metadata_file_path, folder, scenario_metadata_file_name)
        ob_extractor = Object_Based_Scenario_Extractor(folder, raw_data_parent_folder, output_folder_path, sensor_config, output_additional_fps=custom_fps_output)
        ob_extractor.logger.info("Started OB Scenario extraction for folder: "+folder)
        ob_extractor.extract_scenarios(scenario_df_path)
        ob_extractor.logger.info("OB Scenario extraction completed for folder: "+folder)
        ob_extractor.close_logger()
    print("Completed OB Scenario Extraction")