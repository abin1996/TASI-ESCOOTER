import os 
import numpy as np

import logging
import pandas as pd
import time 
import cv2

from moviepy.editor import VideoFileClip


# beam_altitude_angles =[]
# beam_azimuth_angles =[]
# config_file = "/media/rtian2/New Volume/Jimmy/escooter_2024/data_preprocessed/config.json"
# with open(config_file) as json_file:
#     data = json.load(json_file)
#     beam_altitude_angles = data['beam_altitude_angles'] # store altitude angles
#     beam_azimuth_angles = data['beam_azimuth_angles']  # store azimuth angles

class Click_Based_Scenario_Extractor:
    def __init__(self, folder_dir, start, end, scenario_counter, higher_output_folder, temp_folder="./temp_copy_folder"):
        self.folder_dir = folder_dir
        self.folder_name = folder_dir.split('/')[-1]
        self.processed_folder = os.path.join(folder_dir, 'processed')
        self.video_folder = os.path.join(self.processed_folder, 'videos')
        self.video_ts_folder = os.path.join(self.processed_folder, 'timestamps')
        self.scenario_name = self.folder_name + '_' + str(scenario_counter) + '_' + str(int(start/1000)) + '_' + str(int(end/1000))
        self.output_folder = os.path.join(higher_output_folder, self.scenario_name)
        self.temp_folder = temp_folder
        self.start = start
        self.end = end
        self.camera_order = {
                "images1": "top_left",
                "images2": "bottom_middle",
                "images3": "top_right",
                "images4": "bottom_left",
                "images5": "bottom_right",
                "images6": "top_middle"
            }

        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        else:
            os.system("rm -r "+self.output_folder)
            os.makedirs(self.output_folder)
            
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
        self.logger.info("Auto check Time: "+str(self.end_time-self.start_time))
        
        self.sync = self.find_sync_file()

    
    def find_sync_file(self):
        wait_for_quality_drive = os.path.join("/media/abinmath/wait_for_quality_check/Extracted_Raw_Data", self.folder_name, 'processed')
        escooter_drive1 = os.path.join("/media/abinmath/TASI_ESCOOTER_Drive1/Extracted_Raw_Data", self.folder_name, 'processed')
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
            assert os.path.exists(self.folder_dir) 
            assert os.path.exists(self.processed_folder)
            assert os.path.exists(self.video_folder)
            self.video_list = os.listdir(self.video_folder)
            assert os.path.exists(self.video_ts_folder)
            # assert os.path.exists(self.lidar_folder)
            # self.lidar_list = os.listdir(self.lidar_folder)
        except:
            self.logger.error("Folder structure is not correct")
            return False

        #sync
        
        #check videos
        try:
            video_frames= {}
            fps = None
            for video in os.listdir(self.video_folder):
                video_path = os.path.join(self.video_folder, video)
                clip = VideoFileClip(video_path)
                if fps is None:
                    fps = clip.fps
                else:
                    assert fps == clip.fps

                video_frames[video] = clip.fps*clip.duration

                if verbose:
                    print("video: ", video)
                    print("frame: ", clip.fps*clip.duration)
                    print("duration: ", round(clip.duration/60, 2))
                    print("fps: ", clip.fps)
        except:
            self.logger.error("Error reading videos")
            return False

        
        #check timestamps
        try:
            ts_frames = {}
            for ts in os.listdir(self.video_ts_folder):
                ts_path = os.path.join(self.video_ts_folder, ts)
                #ts in txt
                if ts.endswith('.txt'):
                    ts_frames[ts] = pd.read_csv(ts_path, sep=' ', header=None)
                    ts_frames[ts].columns = ['timestamp']
                    ts_frames[ts]['timestamp'] = np.round(ts_frames[ts]['timestamp']/1e6,2)

                    if verbose:
                        print("ts: ", ts)
                        print("num of frames: ", ts_frames[ts].shape[0])
            #print video_frames, ts_frames
            
            for id in range(1,7):
                video_name = [i for i in video_frames.keys() if 'images'+str(id) in i][0]
                # print(ts_frames['images'+str(id)+'_timestamps.txt'])
                # print(video_frames[video_name])
                self.logger.info("Difference between ts and video: "+str(abs(ts_frames['images'+str(id)+'_timestamps.txt'].shape[0] - video_frames[video_name])))
                assert abs(ts_frames['images'+str(id)+'_timestamps.txt'].shape[0] - video_frames[video_name])<60
        except:
            self.logger.error("ts and video are not aligned")
            return False
        
        self.logger.info("All checks passed")
        print("All checks passed")
        self.fps = fps
        self.ts_frames = ts_frames
        return True


    def convert_video_timestamp_to_frame(self, video_ts_min, video_ts_sec):
        total_sec = video_ts_min*60 + video_ts_sec
        return int(total_sec*self.fps)

    def frame_to_timestamp(self, frame):
        ts_list = []
        for id in range(1,7):
            ts_name = 'images'+str(id)+'_timestamps.txt'
            ts_list.append(self.ts_frames[ts_name].iloc[frame, 0])

        max_gap = max(ts_list) - min(ts_list)
        assert max_gap/1000 < 60
        return np.median(ts_list)
    
    def get_frame_num(self,unix_ts,ts_frame):
        """
        Given a unix timestamp and a timestamp dataframe, return the index of the frame that is closest to the timestamp
        """
        return ts_frame.iloc[(ts_frame['timestamp']-unix_ts).abs().argsort()[:1]].index[0]
    
    def given_reference_unix(self,start,end):
        """
        Given a reference unix time in milisec, return the frame number for each camera
        """
        
        cloest_start =  self.sync.iloc[(self.sync['lidar_timestamps']-start).abs().argsort()[:1]]
        cloest_end =  self.sync.iloc[(self.sync['lidar_timestamps']-end).abs().argsort()[:1]]
        self.sync_sce = self.sync[(self.sync['lidar_timestamps']>=cloest_start['lidar_timestamps'].values[0]) & (self.sync['lidar_timestamps']<=cloest_end['lidar_timestamps'].values[0])]
        ts_cameras_start = {"images1": cloest_start['images1_timestamps'].values[0],
                      "images2": cloest_start['images2_timestamps'].values[0],
                    "images3": cloest_start['images3_timestamps'].values[0],
                    "images4": cloest_start['images4_timestamps'].values[0],
                    "images5": cloest_start['images5_timestamps'].values[0],
                    "images6": cloest_start['images6_timestamps'].values[0],
                    }
        
        ts_cameras_end = {"images1": cloest_end['images1_timestamps'].values[0],
                        "images2": cloest_end['images2_timestamps'].values[0],
                        "images3": cloest_end['images3_timestamps'].values[0],
                        "images4": cloest_end['images4_timestamps'].values[0],
                        "images5": cloest_end['images5_timestamps'].values[0],
                        "images6": cloest_end['images6_timestamps'].values[0],
                        }
        
        ts_frame_start = {}
        ts_frame_end = {}
        for key in ts_cameras_start.keys():
            ts_frame_start[key] = self.get_frame_num(ts_cameras_start[key],self.ts_frames[key+'_timestamps.txt'])
            ts_frame_end[key] = self.get_frame_num(ts_cameras_end[key],self.ts_frames[key+'_timestamps.txt'])

        return ts_frame_start, ts_frame_end
    
    def extract_video_frame(self,video_name, start_frame, end_frame, output_folder):
        """
        video_name (example): 'images1',
        start_frame: start frame number
        end_frame: end frame number

        Return: extract the frame from the video to output folder
        """
        video_name = [i for i in self.video_list if video_name in i][0]
        video_path = os.path.join(self.video_folder, video_name)

        clip = VideoFileClip(video_path)

        video_name_short = video_name.split('_')[0]
        if not os.path.exists(os.path.join(output_folder, video_name_short)):
            os.makedirs(os.path.join(output_folder, video_name_short))
        self.save_frames(clip, start_frame, end_frame, video_name_short, output_folder)
    
    def save_frames(self,clip, start_frame, end_frame,video_name_short, output_folder):
        for i in range(start_frame, end_frame+1):
            unix_ts = self.ts_frames[video_name_short+'_timestamps.txt'].iloc[i, 0]
            frame = clip.get_frame(i/clip.fps)
            frame_name = os.path.join(output_folder, video_name_short, video_name_short+'_'+str(int(unix_ts))+'.png')
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cv2.imwrite(frame_name, frame)
        return

    


    @staticmethod
    def find_closest_file(timestamp, folder_dir):
        files = os.listdir(folder_dir)
        files_ts = [i.split('_')[-1].split('.')[0] for i in files]
        closest_file_idx = np.argmin(np.abs(np.array(files_ts).astype(float) - timestamp))
        return files[closest_file_idx]

    def make_sync_sec(self, folders):
        for id,row in self.sync_sce.iterrows():
            reference_time = row['lidar_timestamps']
            closest_image1 = self.find_closest_file(reference_time, folders['images1'])
            closest_image2 = self.find_closest_file(reference_time, folders['images2'])
            closest_image3 = self.find_closest_file(reference_time, folders['images3'])
            closest_image4 = self.find_closest_file(reference_time, folders['images4'])
            closest_image5 = self.find_closest_file(reference_time, folders['images5'])
            closest_image6 = self.find_closest_file(reference_time, folders['images6'])

            self.sync_sce.loc[id, 'images1'] = closest_image1
            self.sync_sce.loc[id, 'images2'] = closest_image2
            self.sync_sce.loc[id, 'images3'] = closest_image3
            self.sync_sce.loc[id, 'images4'] = closest_image4
            self.sync_sce.loc[id, 'images5'] = closest_image5
            self.sync_sce.loc[id, 'images6'] = closest_image6


    def extract_scenario(self,start_end_type='unix'):
        """
        Given a start and end unix timestamp (13digits,milisec), extract the scenario to output folder
        """
        
        
        if not self.data_status:
            return "Data Structure is not correct"

        

        if start_end_type == 'unix':
            ts_frame_start, ts_frame_end = self.given_reference_unix(self.start,self.end)
           
        else:
            raise NotImplementedError
        

        for key in ts_frame_start.keys():
            print("Extracting ", key)
            self.extract_video_frame(key, ts_frame_start[key], ts_frame_end[key], self.temp_folder)
        
        time_1 = time.time()
        self.logger.info("Videos Extraction Time: "+str(time_1-self.end_time))

        folders = {
                "images1":os.path.join(self.temp_folder, 'images1'),
                "images2":os.path.join(self.temp_folder, 'images2'),
                "images3":os.path.join(self.temp_folder, 'images3'),
                "images4":os.path.join(self.temp_folder, 'images4'),
                "images5":os.path.join(self.temp_folder, 'images5'),
                "images6":os.path.join(self.temp_folder, 'images6')
            }

        try:
            self.make_sync_sec(folders)
        except:
            self.logger.error("Error making sync_sec")
            return "Error making sync_sec"
        
        try:
            print("Combining views")
            print(self.sync_sce)
            combine_views(self.sync_sce,folders,self.output_folder, self.camera_order)
            os.system("rm -r "+self.temp_folder)
        except:
            self.logger.error("Error combining views")
            return "Error combining views"
        
        return "Done"

# def get_sorted_files(folder):
#     files = os.listdir(folder)
#     files_with_ts = [(file, int(re.search(r'\d+', file).group())) for file in files]
#     return sorted(files_with_ts, key=lambda x: x[1])



import cv2
import numpy as np
def combine_views(sync_sce, folders, output_folder, camera_order, output_type="both", fps=10):
    """
    Combines synchronized camera views into a video.

    Parameters:

    """
    # Assuming the first camera's images to determine the video size
    sample_img_path = os.path.join(folders['images1'], sync_sce['images1'].iloc[0])
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

    for idx, row in sync_sce.iterrows():
        # Initialize a blank image for combining views
        combined_view = np.zeros((height*2, width * 3, 3), dtype=np.uint8)

        # Read and place synchronized camera images
        for key in camera_order.keys():
            position = position_map[camera_order[key]]  # Get the position of the camera from the dictionary
            img_path = os.path.join(folders[key], row[key])
            if row[key+"_timestamps_inserted_frame"] == 1:
                #white frame
                img = np.ones((height, width, 3), dtype=np.uint8)*255
            else:
                img = cv2.imread(img_path)
            img_resized = cv2.resize(img, (width, height))  # Ensure all images are the same size
            #combined view is 2 x 3 for camera images
            combined_view[position//3*height:(position//3+1)*height, (position%3)*width:(position%3+1)*width, :] = img_resized

        #save the combined view
        output_combine_folder = os.path.join(output_folder, 'combined')
        if not os.path.exists(output_combine_folder):
            os.makedirs(output_combine_folder)
        output_path = os.path.join(output_combine_folder, "combined_"+ str(row['lidar_timestamps'])+".jpg")
        combined_view = cv2.resize(combined_view, (width*3//2, height*2//2))
        cv2.imwrite(output_path, combined_view)

def get_folders_to_process(source_joy_click_folder):
    raw_data_folders = []
    with open(source_joy_click_folder, 'r') as file:
        folders = file.readlines()
        raw_data_folders = [f.strip() for f in folders]
    return raw_data_folders

if __name__ =="__main__":
    folders_to_process_path = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/click_based_scenario_extraction/click_based_scenario_folders.txt"
    source_raw_data_parent_folder = "/mnt/TASI-VRU1/Reordered_drive/Raw_Data"
    source_joy_click_folder = "/mnt/TASI-VRU1/click_based_scenarios_joy_csv"
    destination_folder = "/mnt/TASI-VRU2/Extracted_Click_Based_Scenarios"
    
    raw_data_to_process = get_folders_to_process(folders_to_process_path)

    for raw_data_folder_name in raw_data_to_process:
        print("Working on folder: ", raw_data_folder_name)
        joystick_click_csv_path = os.path.join(source_joy_click_folder, raw_data_folder_name, "joystick_clicks_period_20.csv")
        raw_data_folder = os.path.join(source_raw_data_parent_folder, raw_data_folder_name)
        output_folder = os.path.join(destination_folder, raw_data_folder_name)
        start_time = time.time()
        joystick_click_csv = pd.read_csv(joystick_click_csv_path) 
        for id,row in joystick_click_csv.iterrows():
            print("Working on Scenario : ", row['scenario'])

            start = row['start_time']
            end = row['end_time']
            if len(str(start)) != 13:
                digits = 13 - len(str(start))
                start = start*(10**digits)
            if len(str(end)) != 13:
                digits = 13 - len(str(end))
                end = end*(10**digits)

            # start -= 105730893
            # end -= 105730893

            test_s = Click_Based_Scenario_Extractor(raw_data_folder, start, end, int(row['scenario']), higher_output_folder=output_folder)
            status = test_s.extract_scenario()

            joystick_click_csv.loc[id, 'status'] = status
            joystick_click_csv.to_csv(joystick_click_csv_path, index=False)

        end_time = time.time()
        print("Total time for folder: ", str((end_time-start_time)/60), " mins")
        # print("Done")