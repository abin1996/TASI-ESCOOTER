import os
import shutil
import pandas as pd
from datetime import datetime
import cv2
import bagpy
import time

# Replace 'your_file.pkl' with the path to your pickle file
file_path = '/home/abinmath@ads.iu.edu/Downloads/snow-roundabout-2024-01-22-10-37-23.bag'

try:
    if file_path.endswith(".bag"):
        bag = bagpy.bagreader(file_path)
				# print(bag.start_time)
        data=bag.message_by_topic('/camera_fl/image_raw')
        print("Contents of the rosbag file:")
        print(data)
        # print(data['25411.0'])
        # print(len(data['bd']))
        # print(len(data['front_right'][0]))
        # for i in data['bd']:
        #     print(i)
except FileNotFoundError:
    print("File not found.")
except Exception as e:
    print("An error occurred:", e)