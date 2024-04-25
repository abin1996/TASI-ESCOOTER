from bagpy import bagreader
import pandas as pd
import rosbag
import csv
import math
from os1.packet import (
    AZIMUTH_BLOCK_COUNT,
    CHANNEL_BLOCK_COUNT,
    azimuth_angle,
    azimuth_block,
    azimuth_measurement_id,
    azimuth_timestamp,
    azimuth_valid,
    channel_block,
    channel_range,
    unpack,
)


path = "path to bag file here"
output_csv = "path to the output folder"
df = pd.DataFrame()

# Importing the config data
import json
beam_altitude_angles =[]
beam_azimuth_angles =[]


with open("config.json") as json_file:
    data = json.load(json_file)
    beam_altitude_angles = data['beam_altitude_angles']
    beam_azimuth_angles = data['beam_azimuth_angles']
    #print(beam_altitude_angles)
    #print(beam_azimuth_angles)

def findxyz(filename,output_csv):
    X = []
    Y = []
    Z = []
    bag = rosbag.Bag(path)
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
               X.append( x_point )
               Y.append( y_point )
               Z.append( z_point )

        # Construct output file path
        if track == 128:
            track = 0
            frame += 1
            print("Running.....",frame)
            filename = output_csv + 'output_data_frame_' + str(frame) + '_' + '.csv'

            # Writing to CSV
            with open(filename, 'w', newline='') as csvfile:
                fieldnames = ['X', 'Y', 'Z']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for x, y, z in zip(X, Y, Z):
                    writer.writerow({'X': x, 'Y': y, 'Z': z})
            X = []
            Y = []
            Z = []

findxyz(path,output_csv)