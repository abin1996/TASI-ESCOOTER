import os
import shutil
import pandas as pd
from datetime import datetime
import cv2
import bagpy
import time

local_raw_data_path = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/src_raw_data"

def check_completed_lidar_quality(path):
    folder_summary = {}
    problematic_folders = {}
    for file in os.listdir(path):
        if file.endswith(".csv"):
            print("Processing file: ", file)
            df = pd.read_csv(os.path.join(path, file))
            folder_name = file.split(".")[0]
            avg_frame_rate = df['lidar_frame_rate'].mean()
            lowest_frame_rate = df['lidar_frame_rate'].min()
            num_of_rows_fps_below_10 = df[df['lidar_frame_rate'] < 9.8].shape[0]
            if num_of_rows_fps_below_10 > 0:
                problematic_folders[folder_name] = num_of_rows_fps_below_10
            folder_summary[folder_name] = {
                "avg_frame_rate": avg_frame_rate,
                "lowest_frame_rate": lowest_frame_rate,
                "num_of_rows_fps_below_10": num_of_rows_fps_below_10
            }
    folder_summary_df = pd.DataFrame(folder_summary).T
    folder_summary_df.to_csv("lidar_quality_summary.csv")
    problematic_folders_df = pd.DataFrame(problematic_folders, index=[0]).T
    problematic_folders_df.to_csv("problematic_folders.csv")
    print("Completed processing all the files.")
    print("Summary of the processed files:")
    print(folder_summary_df)
    print("Problematic folders:")
    print(problematic_folders_df)

check_completed_lidar_quality(local_raw_data_path)



            