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
            folder_name = (file.split("_")[2] + "_" + file.split("_")[3]).split(".")[0]
            # print("Processing file: ", folder_name)
            df = pd.read_csv(os.path.join(path, file))
            # folder_name = file.split(".")[0]
            avg_frame_rate = df['lidar_frame_rate'].mean()
            duration_min = df['duration'].sum() / 60
            lowest_frame_rate = df['lidar_frame_rate'].min()
            num_of_rows_fps_below_10 = df[df['lidar_frame_rate'] < 9.8].shape[0]
            if num_of_rows_fps_below_10 > 0:
                problematic_folders[folder_name] = {
                    "num_of_rows_fps_below_10": num_of_rows_fps_below_10,
                    "duration_min": round(duration_min,2),
                }
            folder_summary[folder_name] = {
                "avg_frame_rate": avg_frame_rate,
                "lowest_frame_rate": lowest_frame_rate,
                "num_of_rows_fps_below_10": num_of_rows_fps_below_10,
                "duration_min": round(duration_min,2),
            }
    folder_summary_df = pd.DataFrame(folder_summary).T
    folder_summary_df.to_csv("lidar_quality_summary.csv")
    total_duration = folder_summary_df['duration_min'].sum()
    total_duration_hours = round(total_duration/60,2)
    problematic_folders_df = pd.DataFrame(problematic_folders).T
    problematic_folders_df.to_csv("problematic_folders.csv")
    print("Summary of the processed files:")
    print(folder_summary_df)
    print("Problematic folders:")
    print(problematic_folders_df)
    print("Completed processing all the {} files.".format(len(folder_summary)))
    print("Total Length of all Data is {} mins or {} hours".format(total_duration, total_duration_hours))
    print("Total Length of all Problematic Data is {} mins".format(problematic_folders_df['num_of_rows_fps_below_10'].sum()))
    

check_completed_lidar_quality(local_raw_data_path)



            