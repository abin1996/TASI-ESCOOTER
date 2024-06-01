import os
import shutil
import pandas as pd
from datetime import datetime

import time

def read_folder_list_from_text_file(folder_list_file):
	with open(folder_list_file, 'r') as file:
		folders = file.readlines()
		folders = [f.strip() for f in folders]
	return folders

def get_timestamps(filename):
	"""
	This function reads timestamps in nanoseconds from a text file,
	calculates the difference in milliseconds between consecutive timestamps,
	and prints the total number of timestamps, average difference in milliseconds,
	and individual differences.

	Args:
	filename: The path to the text file containing timestamps in nanoseconds.
	"""

	timestamps = []
	# Read timestamps from the file
	with open(filename, 'r') as file:
		for line in file:
			timestamp = int(line.strip())
			timestamps.append(timestamp)

	# Check if there are enough timestamps for comparison
	if len(timestamps) < 2:
		print("Error: Not enough timestamps in the file.")
		return None, None, None

	# Corrected conversion to milliseconds (avoiding datetime)
	timestamps_ms = [timestamp / 1000000 for timestamp in timestamps]
	return timestamps_ms

def get_camera_timestamps(timestamp_folder):

	all_timestamps = {}
	if os.path.isdir(timestamp_folder):
		print(f"Processing folder {timestamp_folder}")
		for timestamp_file in os.listdir(timestamp_folder):
			filename = os.path.join(timestamp_folder, timestamp_file)
			if filename.endswith(".txt"):
				try:
					timestamp_file_name = timestamp_file.split(".")[0]
					timestamp_list = get_timestamps(filename)
					if timestamp_list:
						all_timestamps[timestamp_file_name] = timestamp_list
				except ValueError as e:
					print(f"Error processing file {filename}: {e}")
	return all_timestamps

def fix_missing_timestamps_for_lidar_and_camera(six_camera_timestamps, df_total_timestamps, subfolder_path):
	#Check the average time gap between the timestamps in the lidar data
	#Iterate through df_total_timestamps and check the df_total_timestamps['lidar_timestamp_gap'] and if it is greater than 200ms then insert the missing timestamp which
	#is average of the previous and next timestamp in the df_laser_timestamp and also in the column ['inserted'] set it to the value of previous timestamp
	print(f"Total timestamps in lidar data: {len(df_total_timestamps)}")
	lidar_missing_timestamps_count = 0
	i=1
	while i < df_total_timestamps.shape[0]:
		if df_total_timestamps['lidar_timestamp_gap'].iloc[i] > (1000*60):
			print(f"WARNING: Large Gap in Lidar: {df_total_timestamps['lidar_timestamp_gap'].iloc[i]}")
		if df_total_timestamps['lidar_timestamp_gap'].iloc[i] > 200:
			num_missing_timestamps = int(df_total_timestamps['lidar_timestamp_gap'].iloc[i] / 100)
			# print(f"Missing timestamps: {num_missing_timestamps}")
			missing_timestamp_df = pd.DataFrame()
			for j in range(1, num_missing_timestamps):
				missing_timestamp = df_total_timestamps['lidar_timestamps'].iloc[i-1] + 100*j
				gap_ms = 100
				lidar_missing_timestamps_count += 1
				missing_timestamp_df = pd.concat([missing_timestamp_df, pd.DataFrame([[missing_timestamp,gap_ms,1]], columns=['lidar_timestamps', 'lidar_timestamp_gap','inserted_lidar_frame'])], ignore_index=True)
			df_total_timestamps = pd.concat([df_total_timestamps.iloc[:i], missing_timestamp_df, df_total_timestamps.iloc[i:]], ignore_index=True)
			df_total_timestamps.reset_index(drop=True, inplace=True)
			i += num_missing_timestamps
			df_total_timestamps.at[i-1,"lidar_timestamp_gap"] = df_total_timestamps["lidar_timestamps"].iloc[i-1] - missing_timestamp
		else:
			i += 1
	print(f"Missing timestamps in lidar data: {lidar_missing_timestamps_count}")
	#Iterate through lidar timestamps and for each timestamp pick the closest timestamp for each camera and insert it in the respective column for the camera
	inserted_frames_all_cameras = dict()
	for camera in six_camera_timestamps.keys():
		df_total_timestamps[camera] = 0
		df_total_timestamps[camera+"_gap"] = 0
		df_total_timestamps[camera+"_inserted_frame"] = 0
		inserted_frames_all_cameras[camera] = set()
	
	for i in range(df_total_timestamps.shape[0]):
		lidar_timestamp = df_total_timestamps['lidar_timestamps'].iloc[i]
		#Find the closest timestamp for each camera
		for camera in six_camera_timestamps.keys():
			camera_timestamps = six_camera_timestamps[camera]
			closest_timestamp = min(camera_timestamps, key=lambda x:abs(x-lidar_timestamp))
			#Check if the closest timestamp is already inserted
			if closest_timestamp in inserted_frames_all_cameras[camera]:
				df_total_timestamps[camera+"_inserted_frame"].iloc[i] = 1
			else:
				inserted_frames_all_cameras[camera].add(closest_timestamp)
			gap_ms = abs(closest_timestamp - lidar_timestamp)
			#Insert the closest timestamp in the respective column for the camera
			df_total_timestamps[camera].iloc[i] = closest_timestamp
			df_total_timestamps[camera+"_gap"].iloc[i] = gap_ms
			
	#Save the df_total_timestamps to a csv file
	if os.path.exists(subfolder_path+"/processed/synchronized_timestamps"):
		df_total_timestamps.to_csv(subfolder_path+"/processed/synchronized_timestamps/synchronized_timestamps.csv", index=False)
	else:
		os.makedirs(subfolder_path+"/processed/synchronized_timestamps", exist_ok=True)
		df_total_timestamps.to_csv(subfolder_path+"/processed/synchronized_timestamps/synchronized_timestamps.csv", index=False)
	
	print(f"Total synchronized frames: {len(df_total_timestamps)}")
	return len(df_total_timestamps)


#Main function to process all the subfolders
def process_subfolders(root_folder, folders_to_process, local_path, processed_subfolders, processed_subfolders_with_error, path_to_processed_subfolders, path_to_processed_subfolders_with_error):
	"""
	Iterates through all subfolders in the root folder, processes timestamp files, and creates a DataFrame.

	Args:
	root_folder: The path to the root folder containing subfolders.
	"""

	data = []
	start_time = time.time()

	for subfolder in os.listdir(root_folder):
		if subfolder.strip() not in folders_to_process:
			continue
		if subfolder in processed_subfolders:
			print(f"Subfolder {subfolder} already processed. Skipping...")
			continue
		if subfolder in processed_subfolders_with_error:
			print(f"Subfolder {subfolder} already processed with error. Skipping...")
			continue
		timestamp_folder_path = os.path.join(root_folder, subfolder, "processed", "timestamps")
		
		print(f"Processing subfolder {subfolder}")
		try:
			#Copy the contents of the subfolder to a new folder and process the new folder
			subfolder_new_local_path = os.path.join(local_path, subfolder)
			local_timestamp_folder_path = os.path.join(subfolder_new_local_path, "processed", "timestamps")

			if not os.path.exists(subfolder_new_local_path):
				os.makedirs(subfolder_new_local_path, exist_ok=True)
			#Check if timestamp folder is copied completely with all the files and subfolders
			if os.path.isdir(local_timestamp_folder_path) and len(os.listdir(timestamp_folder_path)) == len(os.listdir(local_timestamp_folder_path)):
				print(f"Timestamp folder present.")
			elif os.path.isdir(timestamp_folder_path):
				shutil.rmtree(local_timestamp_folder_path, ignore_errors=True)
				shutil.copytree(timestamp_folder_path, local_timestamp_folder_path)

			
			if os.path.isdir(timestamp_folder_path):
				six_camera_timestamps  = get_camera_timestamps(local_timestamp_folder_path)
			len_synced_frames = -1
			if os.path.exists(subfolder_new_local_path+"/processed/lidar_timestamps"):
				df_total_timestamps = pd.read_csv(subfolder_new_local_path+"/processed/lidar_timestamps/lidar_timestamps.csv")
				duration = df_total_timestamps['lidar_timestamps'].iloc[-1] - df_total_timestamps['lidar_timestamps'].iloc[0]
				if len(six_camera_timestamps.keys()) == 6 and len(df_total_timestamps.index) > 0:
					len_synced_frames = fix_missing_timestamps_for_lidar_and_camera(six_camera_timestamps, df_total_timestamps, subfolder_new_local_path)
			else:
				raise Exception(f"Lidar timestamps not found for subfolder {subfolder}")
			data=[]
			data.append({
			"Subfolder": subfolder,
			"Duration from lidar(minutes)": round(duration/600),
			"Duration of synced frames(minutes)": round(len_synced_frames/10/60) if len_synced_frames > 0 else -1,
			"Total_synced_frames": len_synced_frames
			})
			print(data[-1])
			df = pd.DataFrame(data)
			#Append the data to the csv file
			if os.path.exists("synchronized_raw_data_summary.csv"):
				df.to_csv("synchronized_raw_data_summary.csv", mode='a', header=False, index=False)
			else:
				df.to_csv("synchronized_raw_data_summary.csv", index=False)
			#Delete the local lidar and timestamp folders
			# shutil.rmtree(subfolder_new_local_path)
			if os.path.exists(path_to_processed_subfolders):
				with open(path_to_processed_subfolders, "a") as file:
					file.write(subfolder + "\n")
			else:
				with open(path_to_processed_subfolders, "w") as file:
					file.write(subfolder + "\n")
				
		except Exception as e:
			print(f"Error processing subfolder {subfolder}: {e}")
			#Remove the extracted lidar folders
			# shutil.rmtree(subfolder_new_local_path, ignore_errors=True)
			if os.path.exists(path_to_processed_subfolders_with_error):
				with open(path_to_processed_subfolders_with_error, "a") as file:
					file.write(subfolder + "\n")
			else:
				with open(path_to_processed_subfolders_with_error, "w") as file:
					file.write(subfolder + "\n")

	print(f"Processing took {round((time.time() - start_time)/60)} minutes")

# Example usage
# source_raw_dath_path = "/media/abinmath/TASI_ESCOOTER_Drive1/Extracted_Raw_Data" 
# local_dest_raw_data_path = "/media/abinmath/TASI_ESCOOTER_Drive1/Extracted_Raw_Data"
# source_raw_dath_path = "/media/abinmath/wait_for_quality_check/Extracted_Raw_Data" 
# local_dest_raw_data_path = "/media/abinmath/wait_for_quality_check/Extracted_Raw_Data"

source_raw_dath_path = "/mnt/tasismb/Reordered_drive/Raw_Data" 
local_dest_raw_data_path = "/mnt/tasismb/Reordered_drive/Raw_Data"
path_to_folders_to_process = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/sync_folders_network_drive.txt"

# path_to_folders_to_process = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/sync_folders_wait_for_quality_drive.txt"

# path_to_folders_to_process = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/sync_folders.txt"
# path_to_processed_subfolders = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/sync_processed_subfolders_wait_for_quality_drive.txt"
path_to_processed_subfolders = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/sync_processed_subfolders_network_drive.txt"

path_to_processed_subfolders_with_error = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/sync_processed_subfolders_with_error.txt"


folders_to_process = read_folder_list_from_text_file(path_to_folders_to_process)
if os.path.exists(path_to_processed_subfolders):
	processed_subfolders = read_folder_list_from_text_file(path_to_processed_subfolders)
else:
	processed_subfolders = []
if os.path.exists(path_to_processed_subfolders_with_error):
	processed_subfolders_with_error = read_folder_list_from_text_file(path_to_processed_subfolders_with_error)
else:
	processed_subfolders_with_error = []

process_subfolders(source_raw_dath_path, folders_to_process, local_dest_raw_data_path, processed_subfolders, processed_subfolders_with_error, path_to_processed_subfolders, path_to_processed_subfolders_with_error)