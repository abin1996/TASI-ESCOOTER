import datetime
import os
import numpy as np
import laspy
import logging
import pandas as pd
import argparse
pd.options.mode.chained_assignment = None  # default='warn'
import time 
import shutil
import math
import json
import cv2
from cv_bridge import CvBridge, CvBridgeError  # type: ignore
import rosbag
from moviepy.editor import VideoFileClip
from os1.packet import (
    AZIMUTH_BLOCK_COUNT,
    CHANNEL_BLOCK_COUNT,
    azimuth_angle,
    azimuth_block,
    azimuth_measurement_id,
    azimuth_timestamp,
    channel_reflectivity,
    channel_signal_photons,
    azimuth_frame_id,
    azimuth_valid,
    channel_block,
    channel_range,
    unpack,
) #pip install ouster-os1

from helper import create_birdseye_view, get_lidar_config,get_folders_to_process, get_city_name


class Object_Based_Scenario_Extractor:
    def __init__(self, video_name, folder_dir, scenario_num, start, end, higher_output_folder, worker_obj, temp_folder="./temp_copy_folder", video_in_bag=False):
        self.folder_dir = folder_dir
        self.folder_name = video_name
        self.processed_folder = os.path.join(folder_dir, 'processed')
        self.gps_folder = os.path.join(self.processed_folder, 'gps')
        self.video_folder = os.path.join(self.processed_folder, 'videos')
        self.video_ts_folder = os.path.join(self.processed_folder, 'timestamps')
        self.video_bag_folder = os.path.join(self.processed_folder, 'video_bags')
        self.lidar_folder = os.path.join(self.processed_folder, 'lidar_data')
        self.scenario_name = self.folder_name + '_' + str(scenario_num) + '_' + str(int(start)) + '_' + str(int(end))
        self.output_folder = os.path.join(higher_output_folder, video_name, self.scenario_name)
        self.worker_obj = worker_obj
        self.temp_output_folder = temp_folder+ "_"+ video_name
        self.log_save_path = os.path.join(higher_output_folder, "logs", video_name, self.scenario_name, 'log_{}.txt'.format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
        self.scenario_num = scenario_num
        self.start = start * 1000
        self.end = end * 1000
        self.city = self.get_city_name()
        self.camera_order = self.get_camera_order()
        #Flag to check if the videos are in bag or mp4 format
        self.video_in_bag = video_in_bag
        #Store the list of video bags for each camera
        self.video_bags_list = {}
        self.sync = pd.read_csv(os.path.join(self.processed_folder, 'synchronized_timestamps/synchronized_timestamps.csv'))
        
        self.folder_cleanup()
        self.set_logger(higher_output_folder, video_name, self.scenario_name)
        self.perform_data_folder_check()
        

        
    def perform_data_folder_check(self):
        self.logger.info("Performing data quality check")
        self.worker_obj.send_event(f'task-data-quality-check-{self.scenario_num}')
        self.start_time = time.time()
        self.data_status = self.check_folder_structure()
        if int(self.scenario_num) == 1:
            self.data_status = self.check_video_frames_with_timestamps()
        
        self.end_time = time.time()
        self.logger.info("Folder_dir: "+self.folder_dir)
        self.logger.info("Scenario Name: "+self.scenario_name)
        self.logger.info("Start Time: "+str(self.start))
        self.logger.info("End Time: "+str(self.end))
        self.logger.info("Duration: "+str((self.end-self.start)/1000)+"s")
        self.logger.info("Data Quality Check Time: "+str(self.end_time-self.start_time))
    

    def check_folder_structure(self):
        """
        Check if the folder structure is correct
        Check if the fps of the videos are the same
        Check if the timestamps and videos are aligned
        """
        try: 
            assert os.path.exists(self.folder_dir) 
            assert os.path.exists(self.processed_folder)
            if not self.video_in_bag:
                assert os.path.exists(self.video_folder)
                assert os.path.exists(self.video_ts_folder)
            assert os.path.exists(self.gps_folder)
            assert os.path.exists(self.lidar_folder)

            self.folders = {
                "images1":os.path.join(self.temp_output_folder, 'images1'),
                "images2":os.path.join(self.temp_output_folder, 'images2'),
                "images3":os.path.join(self.temp_output_folder, 'images3'),
                "images4":os.path.join(self.temp_output_folder, 'images4'),
                "images5":os.path.join(self.temp_output_folder, 'images5'),
                "images6":os.path.join(self.temp_output_folder, 'images6'),
                "lidar"  :os.path.join(self.temp_output_folder, 'lidar')
            }
            if not self.video_in_bag:
                self.video_list = os.listdir(self.video_folder)
            self.lidar_list = os.listdir(self.lidar_folder)
            self.lidar_dict = {}
            for lidar in self.lidar_list:
                self.lidar_dict[lidar.split('_')[-1].split('.')[0]] = lidar
            self.gps_dict = {}
            for gps in os.listdir(self.gps_folder):
                self.gps_dict[gps.split('_')[-1]] = gps
            self.ts_frames = self.get_video_timestamps()
            if self.video_in_bag:
                # assert os.path.exists(self.video_bag_folder)
                if not os.path.exists(self.video_bag_folder):
                    self.logger.info("Using Alternative video bag path")
                    self.video_bag_folder = os.path.join('/media/abinmath/Boston LidCamB',self.folder_name) #Change this for one of connect hdd
                    if not os.path.exists(self.video_bag_folder):
                        self.logger.info("Video bag folder at "+ str(self.video_bag_folder)+" does not exist, No worries")
                        self.logger.info("Using Second Alternative video bag path")
                        self.video_bag_folder = os.path.join('/media/abinmath/Boston DC LidCamA-2',self.folder_name) #Change this for the second hdd
                        if not os.path.exists(self.video_bag_folder):
                            self.logger.error("Video bag folder at "+ str(self.video_bag_folder)+" does not exist!!!")
                            return False
                six_camera_folders = [i for i in os.listdir(self.video_bag_folder) if 'images' in i]
                assert len(six_camera_folders) == 6
                for folder in six_camera_folders:
                    assert os.path.exists(os.path.join(self.video_bag_folder, folder))
                    self.video_bags_list[folder] = {}
                    for bag in os.listdir(os.path.join(self.video_bag_folder, folder)):
                        self.video_bags_list[folder][bag.split('_')[-1].split('.')[0]] = bag
            return True
        except:
            self.logger.error("Folder structure is not correct")
            return False

    def check_video_frames_with_timestamps(self):
        try:
            if self.video_in_bag:
                video_frames= {}
                for key in self.video_bags_list.keys():
                    print("Camera: ", key)
                    video_frames[key] = 0
                    for bag in self.video_bags_list[key].keys():
                        bag_path = os.path.join(self.video_bag_folder, key, self.video_bags_list[key][bag])
                        bag = rosbag.Bag(bag_path)
                        video_frames[key] += bag.get_message_count(topic_filters=['/camera{}/image_color/compressed'.format(key[-1])])
                        bag.close()
                print(video_frames)
            else:
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
                    self.logger.info("FPS: "+str(fps))
                    self.logger.info("Duration: "+str(clip.duration))
                    self.logger.info("Number of frames: "+str(clip.fps*clip.duration))
                    clip.close()
        except:
            self.logger.error("Error reading videos during auto check")
            return False
        #check timestamps
        try:
            for id in range(1,7):
                video_name = [i for i in video_frames.keys() if 'images'+str(id) in i][0]
                self.logger.info("Checking "+video_name)
                self.logger.info("Length of ts: "+str(self.ts_frames['images'+str(id)+'_timestamps.txt'].shape[0]))
                self.logger.info("Length of video: "+str(video_frames[video_name]))
                ts_diff = abs(self.ts_frames['images'+str(id)+'_timestamps.txt'].shape[0] - video_frames[video_name])
                self.logger.info("Difference: "+str(ts_diff))
                assert ts_diff < 10
        except:
            self.logger.error("TS and Number of frames do not match. The difference is more than 10 frames. Use Video bags")
            return False
        
        self.logger.info("All checks passed")
        print("All checks passed")
        return True

    def get_video_timestamps(self):
        ts_frames = {}
        for ts in os.listdir(self.video_ts_folder):
            ts_path = os.path.join(self.video_ts_folder, ts)
            #ts in txt
            if ts.endswith('.txt'):
                ts_frames[ts] = pd.read_csv(ts_path, sep=' ', header=None)
                ts_frames[ts].columns = ['timestamp']
                ts_frames[ts]['timestamp'] = np.round(ts_frames[ts]['timestamp']/1e6,2)
        return ts_frames

    def set_logger(self, higher_output_folder, video_name, scenario_name):
        if not os.path.exists(os.path.join(higher_output_folder, "logs", video_name, scenario_name)):
            os.makedirs(os.path.join(higher_output_folder, "logs", video_name, scenario_name))
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = [logging.FileHandler(self.log_save_path)]

    def folder_cleanup(self):
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        else:
            shutil.rmtree(self.output_folder)
            os.makedirs(self.output_folder)
        
        if not os.path.exists(self.temp_output_folder):
            os.makedirs(self.temp_output_folder)
        else:
            shutil.rmtree(self.temp_output_folder)
            os.makedirs(self.temp_output_folder)

    def get_city_name(self):
        video_date = self.folder_name.split('_')[0]
        #The date is in the format of DD-MM-YYYY. The city is austin if date is in the range of 01-05-22 to 31-05-22.
        date = int(video_date.split('-')[0])
        month = int(video_date.split('-')[1])
        if month == 5:
            if date >= 1 and date <= 31:
                return "austin"
        if (month == 6 and 1 <= date <= 15) or (month == 7 and 1 <= date <= 2):
            return "san_diego"
        if (month == 7 and 25 <= date <= 31) or (month == 8 and 1 <= date <= 10):
            return "boston"
        else:
            return "indy"

    def get_camera_order(self):
        if self.city == "austin":
            return {
                    "images1": "top_left",
                    "images2": "bottom_middle",
                    "images3": "top_right",
                    "images4": "bottom_left",
                    "images5": "bottom_right",
                    "images6": "top_middle"
                }
        else:
            return {
                    "images1": "bottom_left",
                    "images2": "top_middle",
                    "images3": "top_left",
                    "images4": "top_right",
                    "images5": "bottom_right",
                    "images6": "bottom_middle"
                }
        
    
    
    
    @staticmethod
    def save_row_as_las(row, output_folder):
        # Create a new LAS file
        header = laspy.LasHeader(version="1.4", point_format=6)
        
        las = laspy.LasData(header)
        
        # Assign the data from the row to the LAS object
        las.x = row['xyzintensity'][:, 0]
        las.y = row['xyzintensity'][:, 1]
        las.z = row['xyzintensity'][:, 2]
        las.intensity = row['xyzintensity'][:, 3]
        # Additional attributes like reflectivity and time_azimuth can be added as extra dimensions
        las.add_extra_dim(laspy.ExtraBytesParams(name="reflectivity", type=np.uint16)) # type: ignore
        las.reflectivity = row['xyzintensity'][:, 4].astype(np.uint16)
        las.add_extra_dim(laspy.ExtraBytesParams(name="time_azimuth", type=np.float64)) # type: ignore
        las.time_azimuth = row['xyzintensity'][:, 5]

        # Construct the filename and save the LAS file
        filename = f"lidar_{row['Time']}.las"
        las.write(f"{output_folder}/{filename}")

    @staticmethod
    def findxyz(raw_packet):      #decodes binary packet for a given packet buffer txt file 
        x,y,z,intensity,reflect,time_azimuth=[],[],[],[],[],[]
        if not isinstance(raw_packet, tuple):
            packet = unpack(raw_packet)

        beam_altitude_angles, beam_azimuth_angles = get_lidar_config()

        for b in range(AZIMUTH_BLOCK_COUNT):  #Azimuth loop contains 16 azimuth blocks  azimuth angles
            az_block = azimuth_block(b, packet) #extract the azimtuth block
            az_angle = azimuth_angle(az_block)
            enc = az_block[3]
            for i in range(64): ##64 channel blocks in every data block
                ch_block = channel_block(i,az_block)
                #print("ch_block",ch_block) 
                ch_range = channel_range(ch_block)
                #print ("ch_range", ch_range)
                theta  = 2*math.pi*( (enc/90112) + ((beam_azimuth_angles[i])/360) ) #+ 0.030  # equations from the ouster software user guide
                phi    = 2*math.pi*( beam_altitude_angles[i] / 360 )                         #
                r = ch_range/1000 #/1000 #/1000000
                x_point =   r * math.cos(theta) * math.cos(phi)  
                y_point =  -1 * r * math.sin(theta) * math.cos(phi) 
                z_point =   r * math.sin(phi) 
                ch_ref = channel_reflectivity(ch_block)
                ch_int = channel_signal_photons(ch_block)
                ta=azimuth_timestamp(az_block) 
                x.append( round(x_point,8) )  #add the x points to a list
                y.append( round(y_point,8) )  #add the y points to a list
                z.append( round(z_point,8)  ) #add the z points to a list
                if ch_int>255:
                    intensity.append(255)
                else:
                    intensity.append(ch_int)
                time_azimuth.append(ta)
                reflect.append(ch_ref)
        xyzintensity = np.column_stack((x,y,z,intensity,reflect,time_azimuth))
        return xyzintensity

    # def convert_video_timestamp_to_frame(self, video_ts_min, video_ts_sec):
    #     total_sec = video_ts_min*60 + video_ts_sec
    #     return int(total_sec*self.fps)

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
    
    def extract_video_frame(self,video_name, start_frame, end_frame, start_min, end_min, output_folder):
        """
        video_name (example): 'images1',
        start_frame: start frame number
        end_frame: end frame number

        Return: extract the frame from the video to output folder
        """
        
        if self.video_in_bag:
            self.extract_image_frame_from_bag(video_name, start_min, end_min, output_folder)
        else:
            self.extract_image_frame_from_mp4(video_name, start_frame, end_frame, output_folder)

    def extract_image_frame_from_bag(self, video_name, start_min, end_min, output_folder):
        video_name = [i for i in self.video_bags_list.keys() if video_name in i][0]
        image_bags = self.video_bags_list[video_name]

        if not os.path.exists(os.path.join(output_folder, video_name)):
            os.makedirs(os.path.join(output_folder, video_name))
        for bag_num, bag_name in image_bags.items():
            bag = rosbag.Bag(os.path.join(self.video_bag_folder, video_name, bag_name))
            bag_start = int(bag.get_start_time()*1e3)
            bag_end = int(bag.get_end_time()*1e3)
            if bag_start > self.end or bag_end < self.start:
                continue
            for topic, msg, t in bag.read_messages(topics=['/camera{}/image_color/compressed'.format(video_name[-1])]):
                t = int(int(str(t))/1e6)
                if int(t) < self.start or int(t) > self.end:
                    continue
                unix_ts = str(t)
                frame = CvBridge().compressed_imgmsg_to_cv2(msg)
                frame_name = os.path.join(output_folder, video_name, video_name+'_'+unix_ts+'.png')
                cv2.imwrite(frame_name, frame)
            bag.close()
    
    def extract_image_frame_from_mp4(self, video_name, start_frame, end_frame, output_folder):
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

    def extract_lidar(self, start_unix, end_unix,start_min,end_min, output_folder):
        
        # lidar_filename = self.lidar_list[0].split('_')[1]
        lidar_csv = pd.DataFrame()
        count = 0
        for i in range(start_min,end_min+1):
            lidar_filename = self.lidar_dict[str(i)]
            lidar_file = os.path.join(self.lidar_folder, lidar_filename)
            try:
                lidar_csv = pd.concat([lidar_csv, pd.read_csv(lidar_file)], axis=0)
                self.logger.info("Reading "+lidar_filename)
            except:
                print("Error reading ", lidar_filename)
                self.logger.error("Error reading "+lidar_filename)
                return
            count += 1
        lidar_csv['Time'] = lidar_csv['Time']*1000
        print("Done reading")
        #sort by "Time"
        lidar_csv = lidar_csv.sort_values(by='Time')
        lidar_csv = lidar_csv.reset_index(drop=True)
        
        if len(lidar_csv)/128/10 < count*60*0.95:
            print("Lidar data is missing, Skip this scenario")
            self.logger.error("Lidar data is missing, Skip this scenario")
            return "Lidar data is missing, Skip this scenario"

        start_index =  lidar_csv.iloc[(lidar_csv['Time']-start_unix).abs().argsort()[:1]].index[0]
        end_index =  lidar_csv.iloc[(lidar_csv['Time']-end_unix).abs().argsort()[:1]].index[0]
        # print(start_index, end_index)
        # return lidar_csv,lidar_csv
        start_index = max(0, start_index-64)
        end_index = min(lidar_csv.shape[0], end_index+128)
        # print(start_index, end_index)
        lidar_csv = lidar_csv.iloc[start_index:end_index]
        frame_num = [number for number in range(0, lidar_csv.shape[0]//128 + 1) for _ in range(128)]
        lidar_csv['frame_num'] = frame_num[:lidar_csv.shape[0]]
        
        
        # print(lidar_csv['frame_num'].max()+1)
        new_lidar_csv = pd.DataFrame()
        for frame_id in range(0, int(lidar_csv['frame_num'].max()+1)):
            lidar_csv_frame = lidar_csv[lidar_csv['frame_num'] == frame_id]
            xyzintensity = np.empty((0,6))
            for idx, row in lidar_csv_frame.iterrows():
                xyz = self.findxyz(eval(row.buf)[:-1])
                xyzintensity = np.vstack((xyzintensity, xyz))
            new_ts =  lidar_csv_frame['Time'].mean()
            #add a new row to new_lidar_csv, with the frame number and the xyzintensity
            new_lidar_csv = pd.concat([new_lidar_csv, pd.DataFrame({'frame_num': frame_id, 'xyzintensity': [xyzintensity], 'Time': new_ts})], axis=0)
        # return lidar_csv,new_lidar_csv
        new_lidar_csv['Time'] = new_lidar_csv['Time'].astype(int)
        lidar_output_folder = os.path.join(output_folder, 'lidar')
        if not os.path.exists(lidar_output_folder):
            os.makedirs(lidar_output_folder)
        for idx, row in new_lidar_csv.iterrows():
            self.save_row_as_las(row, lidar_output_folder)
        # new_lidar_csv.to_pickle(os.path.join(output_folder, 'lidar.pkl'))
        return "Done"
    
    def extract_gps(self, start_min, end_min, output_folder):
        gps_outdir = os.path.join(output_folder, 'gps')
        gps_indir = self.gps_folder
        if not os.path.exists(gps_outdir):
            os.makedirs(gps_outdir)
        tcp_fix = pd.DataFrame()
        tcp_time = pd.DataFrame()
        tcp_vel = pd.DataFrame()
        for i in range(start_min,end_min+1):
            gps_min_folder = self.gps_dict[str(i)]
            print("Reading ", gps_min_folder)
            fix_med = pd.read_csv(os.path.join(gps_indir,gps_min_folder,'tcpfix.csv'))
            time_med = pd.read_csv(os.path.join(gps_indir,gps_min_folder,'tcptime.csv'))
            vel_med = pd.read_csv(os.path.join(gps_indir, gps_min_folder,'tcpvel.csv'))
            tcp_fix = pd.concat([tcp_fix,fix_med],ignore_index=True)
            tcp_time = pd.concat([tcp_time,time_med],ignore_index=True)
            tcp_vel = pd.concat([tcp_vel,vel_med],ignore_index=True)
        tcp_fix.to_csv(os.path.join(gps_outdir,'tcp_fix.csv'))
        tcp_time.to_csv(os.path.join(gps_outdir,'tcp_time.csv'))
        tcp_vel.to_csv(os.path.join(gps_outdir,'tcp_vel.csv'))
        return "Done"

    @staticmethod
    def find_closest_file(timestamp, folder_dir):
        files = os.listdir(folder_dir)
        files_ts = [i.split('_')[-1].split('.')[0] for i in files]
        closest_file_idx = np.argmin(np.abs(np.array(files_ts).astype(float) - timestamp))
        return files[closest_file_idx]

    def make_sync_sec(self):
        # files_sorted = {key: get_sorted_files(folder) for key, folder in folders.items()}
        for id,row in self.sync_sce.iterrows():
            reference_time = row['lidar_timestamps']
            closest_image1 = self.find_closest_file(reference_time, self.folders['images1'])
            closest_image2 = self.find_closest_file(reference_time, self.folders['images2'])
            closest_image3 = self.find_closest_file(reference_time, self.folders['images3'])
            closest_image4 = self.find_closest_file(reference_time, self.folders['images4'])
            closest_image5 = self.find_closest_file(reference_time, self.folders['images5'])
            closest_image6 = self.find_closest_file(reference_time, self.folders['images6'])
            closest_lidar = self.find_closest_file(reference_time, self.folders['lidar'])

            self.sync_sce.loc[id, 'images1'] = closest_image1
            self.sync_sce.loc[id, 'images2'] = closest_image2
            self.sync_sce.loc[id, 'images3'] = closest_image3
            self.sync_sce.loc[id, 'images4'] = closest_image4
            self.sync_sce.loc[id, 'images5'] = closest_image5
            self.sync_sce.loc[id, 'images6'] = closest_image6
            self.sync_sce.loc[id, 'lidar'] = closest_lidar
        self.sync_sce.to_csv(os.path.join(self.temp_output_folder, 'sync_sce.csv'), index=False)

    def combine_views(self):
        """
        Combines synchronized camera and LiDAR views into a video.

        Parameters:

        """
        # Assuming the first camera's images to determine the video size
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
            combined_view = np.zeros((height*2, width * 5, 3), dtype=np.uint8)

            # Read and place synchronized camera images
            for key in self.camera_order.keys():
                position = position_map[self.camera_order[key]]
                img_path = os.path.join(self.folders[key], row[key])
                if row[key+"_timestamps_inserted_frame"] == 1:
                    #white frame
                    img = np.ones((height, width, 3), dtype=np.uint8)*255
                else:
                    img = cv2.imread(img_path)
                img_resized = cv2.resize(img, (width, height))  # Ensure all images are the same size
                #combined view is 2 x 3 for camera images
                combined_view[position//3*height:(position//3+1)*height, (position%3)*width:(position%3+1)*width, :] = img_resized


            # Create and place the LiDAR bird's-eye view
            if row["inserted_lidar_frame"] == 1:
                #white frame
                lidar_view = np.ones((height*2, width*2, 3), dtype=np.uint8)*255
            else:
                lidar_view = create_birdseye_view(os.path.join(self.folders['lidar'], row['lidar']),output_size = (2*width, 2*height))
            combined_view[:, 3*width:, :] = lidar_view

            #save the combined view
            output_combine_folder = os.path.join(self.temp_output_folder, 'combined')
            if not os.path.exists(output_combine_folder):
                os.makedirs(output_combine_folder)
            output_path = os.path.join(output_combine_folder, "combined_"+str(row['lidar_timestamps'])+".jpg")
            combined_view = cv2.resize(combined_view, (width*5//4, height*2//4))
            cv2.imwrite(output_path, combined_view)


    def extract_scenario(self,start_end_type='unix'):
        """
        Given a start and end unix timestamp (13digits,milisec), extract the scenario to output folder
        """
        self.logger.info("Extracting Scenario number: {}".format(str(self.scenario_num)))
        if not self.data_status:
            return "Data Structure is not correct"

        if start_end_type == 'unix':
            ts_frame_start, ts_frame_end = self.given_reference_unix(self.start,self.end)
            start_min = ts_frame_start['images1']//600
            end_min = ts_frame_end['images1']//600
        else:
            raise NotImplementedError
        
        #Extract videos
        self.logger.info("Extracting Images")
        self.worker_obj.send_event(f'task-image-extraction-{self.scenario_num}')
        image_extraction_time_start = time.time()
        for key in ts_frame_start.keys():
            print(f"Extracting {key} ")
            self.extract_video_frame(key, ts_frame_start[key], ts_frame_end[key],start_min, end_min, self.temp_output_folder)
        
        print("Done extracting Images")
        self.logger.info("Images Extraction Time: {} mins".format(str((time.time()-image_extraction_time_start)/60)))
        
        print("Extracting lidar")
        self.logger.info("Extracting LiDAR")
        self.worker_obj.send_event(f'task-lidar-extraction-{self.scenario_num}')
        lidar_extraction_time_start = time.time()
        status = self.extract_lidar(self.start, self.end,start_min,end_min, self.temp_output_folder)
        if status == "Lidar data is missing, Skip this scenario":
            return "Lidar data is missing, Skip this scenario"
        self.logger.info("Lidar Extraction Time: {} mins ".format(str((time.time()-lidar_extraction_time_start)/60)))
        print("Done extracting lidar")


        #Extract GPS data
        print("Extracting GPS data")
        self.logger.info("Extracting GPS data")
        self.worker_obj.send_event(f'task-gps-extraction-{self.scenario_num}')
        gps_extraction_time_start = time.time()
        status = self.extract_gps(start_min, end_min, self.temp_output_folder)
        print("Done extracting GPS data")
        self.logger.info("GPS Extraction Time: {} mins".format(str((time.time()-gps_extraction_time_start)/60)))

        try:
            
            self.worker_obj.send_event(f'task-sensor-synchronization-{self.scenario_num}')
            self.logger.info("Making sync_sec")
            self.make_sync_sec()
            self.logger.info("Done making sync_sec")
        except Exception as e:
            print(e)
            self.logger.error("Error making sync_sec")
            return "Error making sync_sec"
        
        try:
            self.worker_obj.send_event(f'task-combine-sensors-{self.scenario_num}')
            self.logger.info("Combining views")
            combine_video_start = time.time()
            self.combine_views()
            self.logger.info("Done combining views")
            self.logger.info("Combining views time: {} mins".format(str((time.time()-combine_video_start)/60)))
        except Exception as e:
            print(e)
            self.logger.error("Error combining views")
            return "Error combining views"
        
        try:
            self.worker_obj.send_event(f'task-copy-output-{self.scenario_num}')
            self.logger.info("Copying output to network drive")
            copying_output_start = time.time()
            shutil.copytree(self.temp_output_folder, self.output_folder, dirs_exist_ok=True)
            shutil.rmtree(self.temp_output_folder)
            shutil.copyfile(self.log_save_path, os.path.join(self.output_folder, 'logs.txt'))
            self.logger.info("Done copying output")
            self.logger.info("Copying output time: {} mins".format(str((time.time()-copying_output_start)/60)))
        except:
            self.logger.error("Error copying output")
            return "Error copying output"
        return "Done"


def check_raw_data_location(video_name, raw_data_tasi_vru1, raw_data_tasi_vru2):
    vru_path2 = os.path.join(raw_data_tasi_vru2, video_name,"processed", "synchronized_timestamps","synchronized_timestamps.csv")
    if os.path.exists(vru_path2):
        return raw_data_tasi_vru2
    return raw_data_tasi_vru1

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
                extractor = Object_Based_Scenario_Extractor(video_name, raw_data_video_folder, scenario_count, scenario_start, scenario_end, destination_folder, self,video_in_bag=video_in_bag)
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