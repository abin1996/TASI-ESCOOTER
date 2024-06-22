import json
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
import rosbag
from moviepy.editor import VideoFileClip

class Click_Based_Scenario_Extractor:
    def __init__(self, folder_dir, start, end, scenario_counter, city, higher_output_folder, temp_folder="./temp_copy_folder", use_video_bag=True, video_bag_folder_path=None):
        self.folder_dir = folder_dir
        self.folder_name = folder_dir.split('/')[-1]
        self.processed_folder = os.path.join(folder_dir, 'processed')
        self.scenario_name = self.folder_name + '_' + str(scenario_counter) + '_' + str(int(start/1000)) + '_' + str(int(end/1000))
        self.output_folder = os.path.join(higher_output_folder, self.scenario_name)
        print("Output folder: ", self.output_folder)
        self.temp_folder = temp_folder + '_' + self.folder_name
        self.start = start
        self.end = end
        self.city = city
        self.use_video_bag = use_video_bag
        self.org_video_bag_path = str(video_bag_folder_path)
        self.sync = self.find_sync_file()
        #Store the list of video bags for each camera
        self.video_bags_list = {}
        self.camera_folder_names = ['images1', 'images2', 'images3', 'images4', 'images5', 'images6']
        if self.city == "austin":
            self.camera_order = {
                    "images1": "top_left",
                    "images2": "bottom_middle",
                    "images3": "top_right",
                    "images4": "bottom_left",
                    "images5": "bottom_right",
                    "images6": "top_middle"
                }
        else:
            self.camera_order = {
                    "images1": "bottom_left",
                    "images2": "top_middle",
                    "images3": "top_left",
                    "images4": "top_right",
                    "images5": "bottom_right",
                    "images6": "bottom_middle"
                }

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        else:
            os.system("rm -r "+self.output_folder)
            os.makedirs(self.output_folder)

        if os.path.exists(self.temp_folder):
            os.system("rm -r "+self.temp_folder)
            
        log_file_path = os.path.join(self.output_folder, 'log.txt')

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = [logging.FileHandler(log_file_path)]
        self.start_time = time.time()
        self.data_status = self.auto_check()
        self.end_time = time.time()
        self.logger.info("Folder_dir: "+self.folder_dir)
        self.logger.info("Start: "+str(self.start))
        self.logger.info("End: "+str(self.end))
        self.logger.info("Duration: "+str((self.end-self.start)/1000)+"s")

    def find_sync_file(self):
        wait_for_quality_drive = os.path.join("/media/abinmath/wait_for_quality_check/Extracted_Raw_Data", self.folder_name, 'processed')
        escooter_drive1 = os.path.join("/media/abinmath/TASI_ESCOOTER_Drive1/Extracted_Raw_Data", self.folder_name, 'processed')
        tasi_vru2 = os.path.join("/mnt/TASI-VRU2/RAW_DATA", self.folder_name, 'processed')
        if os.path.exists(os.path.join(self.processed_folder, 'synchronized_timestamps/synchronized_timestamps.csv')):
            sync_file_path = os.path.join(self.processed_folder, 'synchronized_timestamps/synchronized_timestamps.csv')
            print("Sync file in TASI-VRU1")
            return pd.read_csv(sync_file_path)
        elif os.path.exists(os.path.join(wait_for_quality_drive, 'synchronized_timestamps/synchronized_timestamps.csv')):
            sync_file_path = os.path.join(wait_for_quality_drive, 'synchronized_timestamps/synchronized_timestamps.csv')
            print("Sync file in wait_for_quality_check drive")
            return pd.read_csv(sync_file_path)
        elif os.path.exists(os.path.join(escooter_drive1, 'synchronized_timestamps/synchronized_timestamps.csv')):
            sync_file_path = os.path.join(escooter_drive1, 'synchronized_timestamps/synchronized_timestamps.csv')
            print("Sync file in TASI_ESCOOTER_Drive1")
            return pd.read_csv(sync_file_path)
        elif os.path.exists(os.path.join(tasi_vru2, 'synchronized_timestamps/synchronized_timestamps.csv')):
            sync_file_path = os.path.join(tasi_vru2, 'synchronized_timestamps/synchronized_timestamps.csv')
            print("Sync file in TASI-VRU2")
            return pd.read_csv(sync_file_path)
        else:
            print("Sync file not found")
            return None

    def auto_check(self,verbose=False):
        """
        Check if the folder structure is correct
        Check if the fps of the videos are the same
        Check if the timestamps and videos are aligned
        """
        try: 
            assert os.path.exists(self.org_video_bag_path) 
            six_camera_folders = [i for i in os.listdir(self.org_video_bag_path) if 'images' in i]
            # print("Six camera folders: ", six_camera_folders)
            assert len(six_camera_folders) == 6
            for folder in six_camera_folders:
                assert os.path.exists(os.path.join(self.org_video_bag_path, folder))
                self.video_bags_list[folder] = {}
                for bag in os.listdir(os.path.join(self.org_video_bag_path, folder)):
                    self.video_bags_list[folder][bag.split('_')[-1].split('.')[0]] = bag
            self.folders = {
                "images1":os.path.join(self.temp_folder, 'images1'),
                "images2":os.path.join(self.temp_folder, 'images2'),
                "images3":os.path.join(self.temp_folder, 'images3'),
                "images4":os.path.join(self.temp_folder, 'images4'),
                "images5":os.path.join(self.temp_folder, 'images5'),
                "images6":os.path.join(self.temp_folder, 'images6')
            }
            closest_start =  self.sync.iloc[(self.sync['lidar_timestamps']-self.start).abs().argsort()[:1]]
            closest_end =  self.sync.iloc[(self.sync['lidar_timestamps']-self.end).abs().argsort()[:1]]
            self.sync_sce = self.sync[(self.sync['lidar_timestamps']>=closest_start['lidar_timestamps'].values[0]) & (self.sync['lidar_timestamps']<=closest_end['lidar_timestamps'].values[0])]
            print("Sync sce shape: ", self.sync_sce.shape)
        except:
            self.logger.error("Folder structure is not correct")
            return False

        return True

    
    def extract_video_frame(self,video_name):
        """
        video_name (example): 'images1',
        start_frame: start frame number
        end_frame: end frame number

        Return: extract the frame from the video to output folder
        """
        # video_name = [i for i in self.video_bags_list.keys() if video_name in i][0]
        # image_bags = self.video_bags_list[video_name]
        output_folder = self.folders[video_name]
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        bag_names = list(sorted(os.listdir(os.path.join(self.org_video_bag_path, video_name))))
        for bag_name in bag_names:
            bag = rosbag.Bag(os.path.join(self.org_video_bag_path, video_name, bag_name))
            for topic, msg, t in bag.read_messages(topics=['/camera{}/image_color/compressed'.format(video_name[-1])]):
                t = int(int(str(t))/1e6)
                if int(t) < self.start or int(t) > self.end:
                    continue
                unix_ts = str(t)
                frame = CvBridge().compressed_imgmsg_to_cv2(msg)
                frame_name = os.path.join(output_folder, video_name+'_'+unix_ts+'.png')
                cv2.imwrite(frame_name, frame)
            bag.close()

    
    @staticmethod
    def find_closest_file(timestamp, folder_dir):
        files = os.listdir(folder_dir)
        files_ts = [i.split('_')[-1].split('.')[0] for i in files]
        closest_file_idx = np.argmin(np.abs(np.array(files_ts).astype(float) - timestamp))
        return files[closest_file_idx]

    def make_sync_sec(self):
        for id,row in self.sync_sce.iterrows():
            reference_time = row['lidar_timestamps']
            closest_image1 = self.find_closest_file(reference_time, self.folders['images1'])
            closest_image2 = self.find_closest_file(reference_time, self.folders['images2'])
            closest_image3 = self.find_closest_file(reference_time, self.folders['images3'])
            closest_image4 = self.find_closest_file(reference_time, self.folders['images4'])
            closest_image5 = self.find_closest_file(reference_time, self.folders['images5'])
            closest_image6 = self.find_closest_file(reference_time, self.folders['images6'])

            self.sync_sce.loc[id, 'images1'] = closest_image1
            self.sync_sce.loc[id, 'images2'] = closest_image2
            self.sync_sce.loc[id, 'images3'] = closest_image3
            self.sync_sce.loc[id, 'images4'] = closest_image4
            self.sync_sce.loc[id, 'images5'] = closest_image5
            self.sync_sce.loc[id, 'images6'] = closest_image6

    def combine_views(self):
        """
        Combines synchronized camera and LiDAR views into a video.

        Parameters:

        """
    
        sample_img_path = os.path.join(self.folders['images1'], self.sync_sce['images1'].iloc[0])
        sample_img = cv2.imread(sample_img_path)
        height, width, _ = sample_img.shape
        position_map = {
            'top_left': 0,
            'top_middle': 1,
            'top_right': 2,
            'bottom_left': 3,
            'bottom_middle': 4,
            'bottom_right': 5
        }

        for idx, row in self.sync_sce.iterrows():
        # Initialize a blank image for combining views
            combined_view = np.zeros((height*2, width * 3, 3), dtype=np.uint8)
            # Read and place synchronized camera images
            for key in self.camera_order.keys():
                position = position_map[self.camera_order[key]]  # Get the position of the camera from the dictionary
                img_path = os.path.join(self.folders[key], row[key])
                if row[key+"_timestamps_inserted_frame"] == 1:
                    #white frame
                    img = np.ones((height, width, 3), dtype=np.uint8)*255
                else:
                    img = cv2.imread(img_path)
                img_resized = cv2.resize(img, (width, height))  # Ensure all images are the same size
                #combined view is 2 x 3 for camera images
                combined_view[position//3*height:(position//3+1)*height, (position%3)*width:(position%3+1)*width, :] = img_resized

            #save the combined view
            output_combine_folder = os.path.join(self.temp_folder, 'combined')
            if not os.path.exists(output_combine_folder):
                os.makedirs(output_combine_folder)
            output_path = os.path.join(output_combine_folder, "combined_"+ str(row['lidar_timestamps'])+".jpg")
            combined_view = cv2.resize(combined_view, (width*3//2, height*2//2))
            cv2.imwrite(output_path, combined_view)

    def extract_scenario(self):
        """
        Given a start and end unix timestamp (13digits,milisec), extract the scenario to output folder
        """
        
        
        if not self.data_status:
            return "Data Structure is not correct"
        
        try:
            for camera_name in self.camera_folder_names:
                print("Extracting Camera: ", camera_name)
                self.extract_video_frame(camera_name)
            
            time_1 = time.time()
            self.logger.info("Videos Extraction Time: "+str(time_1-self.end_time))
        except:
            self.logger.error("Error extracting videos")
            return "Error extracting videos"
        
        try:
            self.make_sync_sec()
        except:
            self.logger.error("Error making sync_sec")
            return "Error making sync_sec"
        
        try:
            print("Combining all 6 cameras in one frame")
            self.combine_views()
            #Delete all images folders
            for key in self.folders.keys():
                shutil.rmtree(self.folders[key])
        except:
            self.logger.error("Error combining views")
            return "Error combining views"
        try:
            print("Copying the combined view to output folder")
            shutil.copytree(self.temp_folder, self.output_folder, dirs_exist_ok=True)
            shutil.rmtree(self.temp_folder)
        except:
            self.logger.error("Error copying the combined view to output folder")
            return "Error copying the combined view to output folder"
        return "Done"


    


def get_folders_to_process(source_joy_click_folder):
    raw_data_folders = []
    with open(source_joy_click_folder, 'r') as file:
        folders = file.readlines()
        raw_data_folders = [f.strip() for f in folders]
    return raw_data_folders

def get_city_name(folder_name):
    video_date = folder_name.split('_')[0]
    #The date is in the format of DD-MM-YYYY. The city is austin if date is in the range of 01-05-22 to 31-05-22.
    date = int(video_date.split('-')[0])
    month = int(video_date.split('-')[1])
    if month == 5:
        if date >= 1 and date <= 31:
            return "austin"
    if (month == 6 and 15 <= date <= 30) or (month == 7 and 1 <= date <= 2):
        return "san_diego"
    if (month == 7 and 25 <= date <= 31) or (month == 8 and 1 <= date <= 10):
        return "boston"
    else:
        return "indy"
    
if __name__ =="__main__":

     
    # Load the configuration file
    parser = argparse.ArgumentParser(description='Extract OB scenarios based on joystick clicks')
    parser.add_argument('-c', type=str, help='Path to the config file', required=True)
    arguments = parser.parse_args()
    config_path = arguments.c
    config = None
    #Read the json file
    if not os.path.exists(config_path):
        print("Config file path error")
        exit(1)
    with open(config_path) as f:
        config = json.load(f)
    raw_data_tasi_vru1 = config['raw_data_tasi_vru1']
    raw_data_tasi_vru2 = config['raw_data_tasi_vru2']
    ob_scenario_click_folder = config['ob_scenario_click_folder']
    destination_folder = config['destination_folder']
    folders_to_process_path = config['folders_to_extract_path']
    raw_data_to_process = get_folders_to_process(folders_to_process_path)


    
    for video_name in raw_data_to_process:
        print("-----------Working on folder: ", video_name, "-----------")
        raw_data_folder_path = check_raw_data_location(video_name, raw_data_tasi_vru1, raw_data_tasi_vru2)
        print(f"Raw data folder path: {raw_data_folder_path}")
        # Load the scenario file
        ob_scenarios_path = os.path.join(ob_scenario_click_folder, video_name, "object_based_scenarios.csv")
        ob_scenarios_df = pd.read_csv(ob_scenarios_path)

        scenario_count = 0
        video_start_time = time.time()
        all_status = []
        print(f"Total scenarios to process: {len(ob_scenarios_df)}")
        #Process all the scenarios
        for index, row in ob_scenarios_df.iterrows():
            scenario_start_time = time.time()
            scenario_count += 1
            print(f"Processing scenario {scenario_count} out of {len(ob_scenarios_df)}")
            scenario_start = row['Start Time']
            scenario_end = row['Stop Time']
            raw_data_video_folder = os.path.join(raw_data_folder_path, video_name)
            try:
                extractor = Click_Based_Scenario_Extractor(video_name, raw_data_video_folder, scenario_count, scenario_start, scenario_end, destination_folder, None ,video_in_bag=True)
                status = extractor.extract_scenario()
            except Exception as e:
                print(f"Error processing scenario {scenario_count} for video {video_name}. Error: {str(e)}")
                print("Error processing scenario number: {scenario_count}")
                status = "Error"
            all_status.append(status)
            scenario_duration = (time.time() - scenario_start_time)/60
            print(f"Processed scenario {scenario_count} in {scenario_duration} mins")

        video_duration = (time.time() - video_start_time)/60
        print(f"Processed video: {video_name} in {video_duration} mins")

        print(all_status)
        #Save all the status to a file with name as current task_id inside the destination folder
        with open(os.path.join('logs','worker_logs', f"{video_name}_status.txt"), 'w') as f:
            for status in all_status:
                f.write(f"{status}\n")
        
        if set(all_status) == {"Done"}:
            print(f"All {len(all_status)} scenarios success")
        else:
            num_failed = len(all_status) - all_status.count("Done")
            print(f"Failed {num_failed} scenarios out of {len(all_status)}. Check Logs")