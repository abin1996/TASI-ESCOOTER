import os
import shutil
import pandas as pd
from datetime import datetime
import cv2
import bagpy
import time

# Replace 'your_file.pkl' with the path to your pickle file
file_path = '/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/radar/as_tx/radar_as_tx_2024-06-11_16-39-01_0.bag'

try:
    if file_path.endswith(".bag"):
        bag = bagpy.bagreader(file_path)
        print(bag.start_time)
        data=bag.message_by_topic('/as_tx/radar_tracks')
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