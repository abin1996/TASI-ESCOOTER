import json
import os
import pandas as pd
from datetime import datetime
import cv2
import bagpy

def check_if_annotation_info_exists(scenario_folder):
	annotation_root_folder = "/Volumes/TASI-VRU Data Storage/XML_ Annotations"
	annotation_file = os.path.join(annotation_root_folder, scenario_folder + ".xml")
	if os.path.exists(annotation_file):
		return True
	return False

def get_scenario_info_for_subfolder(subfolder, subfolder_path):
	scenario_root_folder = "/Volumes/TASI-VRU Data Storage/Reordered_drive/processed_final"
	all_scenarios_for_subfolder = []
	for scenario_folder in os.listdir(scenario_root_folder):
		if scenario_folder.startswith(subfolder):
			print(f"Processing subfolder {subfolder}")
			scenario_info = {}
			lidar_frames_path = os.path.join(scenario_root_folder, scenario_folder,scenario_folder+'_bird_eye')
			#get number of files in lidar_frames_path
			lidar_frames = len([name for name in os.listdir(lidar_frames_path) if os.path.isfile(os.path.join(lidar_frames_path, name))])
			#there are 6 cameras, so we need to iterate through all of them and get the maximum number of frames out of all of them
			max_camera_frames = 0
			for i in range(1, 7):
				try:
					camera_frames_path = os.path.join(scenario_root_folder,scenario_folder, scenario_folder+'_images',  scenario_folder+'_cam'+str(i))
				except Exception as e:
					print("Error: " + camera_frames_path + " does not exist")
                #get number of files in camera_frames_path
				camera_frames = len([name for name in os.listdir(camera_frames_path) if os.path.isfile(os.path.join(camera_frames_path, name))])
				max_camera_frames = max(max_camera_frames, camera_frames)
			#The scenario_folder looks like this: 28-07-22_15-39-58_15341600_3_002_010
			#The different parts are separated by underscores, 28-07-22_15-39-58 is the timestamp, 15341600 is the from time(15min 34sec) and to time(16min 00sec), 2 is the city number, 001 is the scenario number, and 100 is the ecsoote/bicycle information
			scenario_info["video_subfolder"] = subfolder
			scenario_info["scenario_name"] = scenario_folder
			scenario_info["annotation_info_exists"] = check_if_annotation_info_exists(scenario_folder)
			scenario_info["from_time"] = scenario_folder.split("_")[2][:4]
			scenario_info["from_time_minutes"] = scenario_info["from_time"][:2]
			scenario_info["from_time_seconds"] = scenario_info["from_time"][2:]
			scenario_info["to_time"] = scenario_folder.split("_")[2][-4:]
			scenario_info["to_time_minutes"] = scenario_info["to_time"][:2]
			scenario_info["to_time_seconds"] = scenario_info["to_time"][2:]
			scenario_info["city_number"] = scenario_folder.split("_")[3]
			scenario_info["scenario_number"] = scenario_folder.split("_")[4]
			scenario_info["escooter_bicycle"] = scenario_folder.split("_")[5]
			from_time_seconds = scenario_info["from_time_minutes"] * 60 + scenario_info["from_time_seconds"]
			to_time_seconds = scenario_info["to_time_minutes"] * 60 + scenario_info["to_time_seconds"]
			time_difference_seconds = int(to_time_seconds) - int(from_time_seconds)
			scenario_info["duration"] = time_difference_seconds/60
			scenario_info["lidar_frames"] = lidar_frames
			scenario_info["camera_frames"] = max_camera_frames
			print(scenario_info)
			all_scenarios_for_subfolder.append(scenario_info)
	return all_scenarios_for_subfolder

def process_subfolders(root_folder):
	"""
	Iterates through all subfolders in the root folder, processes timestamp files, and creates a DataFrame.

	Args:
	root_folder: The path to the root folder containing subfolders.
	"""

	data = []
	data_frame_count = []
	all_scenarios = []
	break_counter = 0
	for subfolder in os.listdir(root_folder):
		subfolder_path = os.path.join(root_folder, subfolder)
		timestamp_folder_path = os.path.join(root_folder, subfolder, "processed", "timestamps")
		lidar_folder_path = os.path.join(root_folder, subfolder, "lidar")
		
		if os.path.isdir(timestamp_folder_path):
			try:
				break_counter += 1
				# if break_counter == 5:
				# 	break
				
				# lidar_info = get_lidar_info(lidar_folder_path)
				# print(lidar_info)
				scenario_data = get_scenario_info_for_subfolder(subfolder, subfolder_path)
				if scenario_data:
					all_scenarios.extend(scenario_data)
				
			except Exception as e:
				print(f"Error processing subfolder {subfolder_path}: {e}")

	df_frame_count = pd.DataFrame(all_scenarios)
	df_frame_count.to_csv("scenario_info_frames_comp.csv", index=False)

# Example usage
root_folder = "/Volumes/TASI-VRU Data Storage/Reordered_drive/Raw_Data"  # Replace with your actual root folder path
problematic_root_folder = "/Volumes/TASI-VRU Data Storage/Problematic_Datasets"  # Replace with your actual root folder path

process_subfolders(root_folder)