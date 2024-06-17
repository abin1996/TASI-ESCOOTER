from math import nan
import os
import shutil
import pandas as pd
from datetime import datetime
import cv2
import bagpy
import time
from cv_bridge import CvBridge
import rosbag
# Replace 'your_file.pkl' with the path to your pickle file
file_path = '/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/camera/front_left/camera_fl_2024-06-11_16-39-01_0.bag'
csv_path = "/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/camera/front_left/camera_fl_2024-06-11_16-39-01_0/camera_ic_r-image_raw.csv"
img_folder = "/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/camera/front_left/camera_fl_2024-06-11_16-39-01_0/images/"
try:
    # if file_path.endswith(".bag"):
    #     bag = bagpy.bagreader(file_path)
    #     print(bag.start_time)
    #     data=bag.message_by_topic('/camera_ic_r/image_raw')
    #     print("Contents of the rosbag file:")
    #     print(data)

    bag = rosbag.Bag(file_path)
    bag_start = int(bag.get_start_time()*1e3)
    bag_end = int(bag.get_end_time()*1e3)
    print("Bag start time:", bag_start)
    print("Bag end time:", bag_end)
    for topic, msg, t in bag.read_messages(topics=['/camera_ic_r/image_raw']): # type: ignore
        t = int(int(str(t))/1e6)
        unix_ts = str(t)
        frame = CvBridge().compressed_imgmsg_to_cv2(msg)
        frame_name = os.path.join(output_folder, video_name, video_name+'_'+unix_ts+'.png')
        cv2.imwrite(frame_name, frame)
    bag.close()


        # print(data['25411.0'])
        # print(len(data['bd']))
        # print(len(data['front_right'][0]))
        # for i in data['bd']:
        #     print(i)
except FileNotFoundError:
    print("File not found.")
except Exception as e:
    print("An error occurred:", e)