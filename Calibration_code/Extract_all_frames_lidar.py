import pandas as pd
import rosbag
import os
import csv
import math
from os1.packet import (
    AZIMUTH_BLOCK_COUNT,
    azimuth_block,
    channel_signal_photons,
    channel_block,
    channel_range,
    unpack,
)

# Function for grabbing the path for lidar file from the raw data folder
def grab_files(input_folder):
    lidar_folder = os.path.join(input_folder, 'lidar')

    # Grab bag file from lidar folder
    bag_files = [f for f in os.listdir(lidar_folder) if f.endswith('.bag')]
    if len(bag_files) == 0:
        print("No bag file found in the 'lidar' folder....")
        return
    elif len(bag_files) == 1:
        print("Grabbing the Bag file....")
    elif len(bag_files) > 1:
        print("Multiple bag files found in the 'lidar' folder. Taking the first one.")
    bag_file = os.path.join(lidar_folder, bag_files[0])

    return bag_file

def findxyz(bag_file,output_folder):
    os.makedirs(output_folder, exist_ok=True)
    X = []
    Y = []
    Z = []
    Intensity = []
    bag = rosbag.Bag(bag_file)
    track = 0
    frame = 0
    for topic, msg, t in bag.read_messages(topics=['/os_node/lidar_packets']):
        track += 1
        raw_packet=msg.buf[:-1]
        if not isinstance(raw_packet, tuple):
            packet = unpack(raw_packet)
        for b in range(AZIMUTH_BLOCK_COUNT):  #Azimuth loop contains 16 azimuth blocks  azimuth angles
           az_block = azimuth_block(b, packet)
           enc = az_block[3]
           for i in range(64): ##64 channel blocks in every data block
               ch_block = channel_block(i,az_block)
               ch_range = channel_range(ch_block)
               theta  = 2*math.pi*( (enc/90112) + ((beam_azimuth_angles[i])/360) )
               phi    = 2*math.pi*( beam_altitude_angles[i] / 360 )
               r = ch_range/1000 #/1000 #/1000000
               x_point =   r * math.cos(theta) * math.cos(phi)
               y_point =  -1 * r * math.sin(theta) * math.cos(phi)
               z_point =   r * math.sin(phi)
               ch_int = channel_signal_photons(ch_block)
               X.append( x_point )
               Y.append( y_point )
               Z.append( z_point )
               Intensity.append( ch_int )

        # Construct output file path
        if track == 128:
            track = 0
            frame += 1
            print("Running.....",frame)
            filename = output_folder + 'output_data_frame_' + str(frame) + '_' + '.csv'

            # Writing to CSV
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['X', 'Y', 'Z', 'Intensity']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for x, y, z, intensity in zip(X, Y, Z, Intensity):
                    writer.writerow({'X': x, 'Y': y, 'Z': z, 'Intensity': intensity})
            X = []
            Y = []
            Z = []
            Intensity = []


# Importing the config data
import json
beam_altitude_angles =[]
beam_azimuth_angles =[]

# Change the path of the json file here if it is not in the directory you are working
with open("config.json") as json_file:
    data = json.load(json_file)
    beam_altitude_angles = data['beam_altitude_angles']
    beam_azimuth_angles = data['beam_azimuth_angles']

# Provide the raw data folder path
input_folder = '/home/dp75@ads.iu.edu/TASI/TASI_Project/Calibration_code/20-06-22_22-18-30'
bag_file = grab_files(input_folder)
calibration_folder = os.path.join(input_folder, 'calibration')
output_folder = os.path.join(calibration_folder, 'extracted_lidar_frames')
df = pd.DataFrame()

findxyz(bag_file,output_folder)