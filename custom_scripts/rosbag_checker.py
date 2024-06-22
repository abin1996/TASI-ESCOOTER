from calendar import c
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
file_path = '/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/radar/as_tx/radar_as_tx_2024-06-11_16-39-01_0.bag'
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
    count = 0
    data = {
        'timestamp': [],
        'message': []
    }
    for topic, msg, t in bag.read_messages(topics=['/as_tx/radar_tracks']): # type: ignore
        print(msg.header.stamp.nsecs)
        print(msg.header.stamp.secs)
        timestamp_nsecs = str(msg.header.stamp.nsecs)
        # if nsecs has less than 9 digits, add zeros to the front 
        if len(str(msg.header.stamp.nsecs)) < 9:
            print("Less than 9 digits")
            timestamp_nsecs = str(msg.header.stamp.nsecs).zfill(9)
            print(timestamp_nsecs)
        full_timestamp = str(msg.header.stamp.secs) + timestamp_nsecs
        timestamp_ms = int(int(full_timestamp)/1e6)
        print("Timestamp: ", timestamp_ms)
        t = int(int(str(t))/1e6)
        unix_ts = str(t)
        count += 1
        #Save the message with timestamps to a csv using dataframe
        # print(msg)
        if not os.path.exists(img_folder):
            os.makedirs(img_folder)
        data['timestamp'].append(timestamp_ms)
        data['message'].append(str(msg))

        # print("Message: ", msg.data)
        # frame = CvBridge().imgmsg_to_cv2(msg, desired_encoding="bgr8")
        # frame_name = os.path.join(img_folder+'frame_'+str(timestamp_ms)+'.png')
        # cv2.imwrite(frame_name, frame)
    bag.close()
    print("Total messages:", count)
    df = pd.DataFrame(data)
    df.to_csv("/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/radar/as_tx/radar_tracks.csv", index=False)
        # print(data['25411.0'])
        # print(len(data['bd']))
        # print(len(data['front_right'][0]))
        # for i in data['bd']:
        #     print(i)
except FileNotFoundError:
    print("File not found.")
