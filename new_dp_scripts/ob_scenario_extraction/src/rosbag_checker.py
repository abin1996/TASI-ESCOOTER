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
import pypcd
import open3d as o3d
import numpy as np
import plotly.express as px

from PIL import Image
import numpy as np

import numpy as np


# ==============================================================================
#                                                                   SCALE_TO_255
# ==============================================================================
def scale_to_255(a, min, max, dtype=np.uint8):
    """ Scales an array of values from specified min, max range to 0-255
        Optionally specify the data type of the output (default is uint8)
    """
    return (((a - min) / float(max - min)) * 255).astype(dtype)


# ==============================================================================
#                                                         POINT_CLOUD_2_BIRDSEYE
# ==============================================================================
def point_cloud_2_birdseye(points,
                           res=0.1,
                           side_range=(-50., 50.),  # left-most to right-most
                           fwd_range = (-50., 50.), # back-most to forward-most
                           height_range=(-5., 5.),  # bottom-most to upper-most
                           ):
    """ Creates an 2D birds eye view representation of the point cloud data.

    Args:
        points:     (numpy array)
                    N rows of points data
                    Each point should be specified by at least 3 elements x,y,z
        res:        (float)
                    Desired resolution in metres to use. Each output pixel will
                    represent an square region res x res in size.
        side_range: (tuple of two floats)
                    (-left, right) in metres
                    left and right limits of rectangle to look at.
        fwd_range:  (tuple of two floats)
                    (-behind, front) in metres
                    back and front limits of rectangle to look at.
        height_range: (tuple of two floats)
                    (min, max) heights (in metres) relative to the origin.
                    All height values will be clipped to this min and max value,
                    such that anything below min will be truncated to min, and
                    the same for values above max.
    Returns:
        2D numpy array representing an image of the birds eye view.
    """
    # EXTRACT THE POINTS FOR EACH AXIS
    x_points = points[:, 0]
    y_points = points[:, 1]
    z_points = points[:, 2]

    # FILTER - To return only indices of points within desired cube
    # Three filters for: Front-to-back, side-to-side, and height ranges
    # Note left side is positive y axis in LIDAR coordinates
    f_filt = np.logical_and((x_points > fwd_range[0]), (x_points < fwd_range[1]))
    s_filt = np.logical_and((y_points > -side_range[1]), (y_points < -side_range[0]))
    filter = np.logical_and(f_filt, s_filt)
    indices = np.argwhere(filter).flatten()

    # KEEPERS
    x_points = x_points[indices]
    y_points = y_points[indices]
    z_points = z_points[indices]

    # CONVERT TO PIXEL POSITION VALUES - Based on resolution
    x_img = (-y_points / res).astype(np.int32)  # x axis is -y in LIDAR
    y_img = (-x_points / res).astype(np.int32)  # y axis is -x in LIDAR

    # SHIFT PIXELS TO HAVE MINIMUM BE (0,0)
    # floor & ceil used to prevent anything being rounded to below 0 after shift
    x_img -= int(np.floor(side_range[0] / res))
    y_img += int(np.ceil(fwd_range[1] / res))

    # CLIP HEIGHT VALUES - to between min and max heights
    pixel_values = np.clip(a=z_points,
                           a_min=height_range[0],
                           a_max=height_range[1])

    # RESCALE THE HEIGHT VALUES - to be between the range 0-255
    pixel_values = scale_to_255(pixel_values,
                                min=height_range[0],
                                max=height_range[1])

    # INITIALIZE EMPTY ARRAY - of the dimensions we want
    x_max = 1 + int((side_range[1] - side_range[0]) / res)
    y_max = 1 + int((fwd_range[1] - fwd_range[0]) / res)
    im = np.zeros([y_max, x_max], dtype=np.uint8)

    # FILL PIXEL VALUES IN IMAGE ARRAY
    im[y_img, x_img] = pixel_values

    # Convert from numpy array to a PIL image
    im = Image.fromarray(im)

    im.show()


# Replace 'your_file.pkl' with the path to your pickle file
# file_path = '/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/radar/as_tx/radar_as_tx_2024-06-11_16-39-01_0.bag'
# csv_path = "/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/camera/front_left/camera_fl_2024-06-11_16-39-01_0/camera_ic_r-image_raw.csv"
# img_folder = "/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/camera/front_left/camera_fl_2024-06-11_16-39-01_0/images/"

file_path = '/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/lidar/point_cloud/lidar_point_cloud_2024-06-11_16-39-01_22.bag'
csv_path = "/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/camera/front_left/camera_fl_2024-06-11_16-39-01_0/camera_ic_r-image_raw.csv"
img_folder = "/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/lidar/point_cloud/lidar_points/"


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
    # for topic, msg, t in bag.read_messages(topics=['/as_tx/radar_tracks']): # type: ignore
    #     print(msg.header.stamp.nsecs)
    #     print(msg.header.stamp.secs)
    #     timestamp_nsecs = str(msg.header.stamp.nsecs)
    #     # if nsecs has less than 9 digits, add zeros to the front 
    #     if len(str(msg.header.stamp.nsecs)) < 9:
    #         print("Less than 9 digits")
    #         timestamp_nsecs = str(msg.header.stamp.nsecs).zfill(9)
    #         print(timestamp_nsecs)
    #     full_timestamp = str(msg.header.stamp.secs) + timestamp_nsecs
    #     timestamp_ms = int(int(full_timestamp)/1e6)
    #     print("Timestamp: ", timestamp_ms)
    #     t = int(int(str(t))/1e6)
    #     unix_ts = str(t)
    #     count += 1
    #     #Save the message with timestamps to a csv using dataframe
    #     # print(msg)
    #     if not os.path.exists(img_folder):
    #         os.makedirs(img_folder)
    #     data['timestamp'].append(timestamp_ms)
    #     data['message'].append(str(msg))

        #Lidar

    for topic, msg, t in bag.read_messages(topics=['/velodyne_points']): # type: ignore
        # print(msg.header.stamp.nsecs)
        # print(msg.header.stamp.secs)
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
        pcd = pypcd.PointCloud.from_msg(msg)
        pcd.save(img_folder+'point_cloud_'+str(timestamp_ms)+'.pcd')

        pcd = o3d.io.read_point_cloud(img_folder+'point_cloud_'+str(timestamp_ms)+'.pcd')
        pcd_points = np.asarray(pcd.points)

        # Calculate distance from the origin
        distances = np.linalg.norm(pcd_points, axis=1)
        
        point_cloud_2_birdseye(pcd_points)

        # # Plot using Plotly
        # fig = px.scatter_3d(x=pcd_points[:, 0], y=pcd_points[:, 1], z=pcd_points[:, 2], color=distances, color_continuous_scale='Turbo')
        # fig.update_traces(marker=dict(size=1), selector=dict(mode='markers'))
        # fig.update_layout(scene_aspectmode='data')
        # fig.show()
        # break
        time.sleep(1)
        # print("Message: ", msg.data)
        # frame = CvBridge().imgmsg_to_cv2(msg, desired_encoding="bgr8")
        # frame_name = os.path.join(img_folder+'frame_'+str(timestamp_ms)+'.png')
        # cv2.imwrite(frame_name, frame)
    bag.close()
    print("Total messages:", count)
    df = pd.DataFrame(data)
    df.to_csv("/media/abinmath/ImDrive_Org/2024-06-11_16-39-01/lidar/point_cloud/pcd.csv", index=False)
        # print(data['25411.0'])
        # print(len(data['bd']))
        # print(len(data['front_right'][0]))
        # for i in data['bd']:
        #     print(i)
except FileNotFoundError:
    print("File not found.")
