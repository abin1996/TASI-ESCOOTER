import json
import os
import shutil
import pandas as pd
from datetime import datetime
import cv2
import bagpy
import time
import struct

def read_folder_list_from_text_file(folder_list_file):
	with open(folder_list_file, 'r') as file:
		folders = file.readlines()
		folders = [f.strip() for f in folders]
	return folders

def get_lidar_bag_info(df_lidar, df_total_lidar_timestamps):
			#Check the average time gap between the timestamps in the lidar data
	average_diff =  df_lidar['Time'].diff().mean()
	max_diff = df_lidar['Time'].diff().max()
	#combine 128 entries in the original df_laser to get the timestamps for each frame
	df_lidar['Time'] = df_lidar['Time'].rolling(128).mean()
	mean_values = []
	for i in range(0, df_lidar.shape[0], 128):
		mean_value = df_lidar['Time'].iloc[i:i+128].mean()
		mean_value = round(mean_value * 1000)  # Round to nearest millisecond
		mean_values.append(int(mean_value))

	# Create a new DataFrame with mean values
	df_mean = pd.DataFrame(mean_values, columns=['lidar_timestamps'])
	df_total_lidar_timestamps = pd.concat([df_total_lidar_timestamps, df_mean['lidar_timestamps']], ignore_index=True)
	# print(df_total_lidar_timestamps.head())
	return df_total_lidar_timestamps, average_diff, max_diff
	

def clean_up_lidar_folder(lidar_folder_path):
	#Remove all the extracted lidar folders from the source lidar folder
	for lidar_file in sorted(os.listdir(lidar_folder_path)):
		if not lidar_file.endswith(".bag"):
			shutil.rmtree(os.path.join(lidar_folder_path, lidar_file))
	print(f"Cleaned up the lidar folder.")

def save_lidar_bag_as_csv(df_lidar, lidar_file_name, local_subfolder_path):
	#Save the original lidar data to a csv file
	if os.path.exists(local_subfolder_path+"/processed/lidar_data"):
		df_lidar.to_csv(local_subfolder_path+"/processed/lidar_data/"+lidar_file_name.split(".")[0]+".csv", index=False)
	else:
		os.makedirs(local_subfolder_path+"/processed/lidar_data", exist_ok=True)
		df_lidar.to_csv(local_subfolder_path+"/processed/lidar_data/"+lidar_file_name.split(".")[0]+".csv", index=False)

def save_combined_lidar_timestamps(df_total_timestamps, local_subfolder_path):
	#Save the lidar timestamps to a csv file
	if os.path.exists(local_subfolder_path+"/processed/lidar_timestamps"):
		df_total_timestamps.to_csv(local_subfolder_path+"/processed/lidar_timestamps/lidar_timestamps.csv", index=False)
	else:
		os.makedirs(local_subfolder_path+"/processed/lidar_timestamps", exist_ok=True)
		df_total_timestamps.to_csv(local_subfolder_path+"/processed/lidar_timestamps/lidar_timestamps.csv", index=False)
	print(f"Saved the combined lidar timestamps to a csv file.")

def get_lidar_statistics(lidar_filename, df_laser, bag, average_diff, max_diff):
	#Get Lidar statistics
	lidar_info = {}
	lidar_info["bag_file"] = lidar_filename
	lidar_info["num_frames"] = float(len(df_laser)/128)
	lidar_info["duration"] = bag.end_time - bag.start_time
	lidar_info["lidar_frame_rate"] = round(float(lidar_info["num_frames"] / lidar_info["duration"]),2)
	lidar_info["average_diff"] = average_diff
	lidar_info["max_diff"] = max_diff
	return lidar_info, lidar_info["duration"]

def extract_lidar_data(lidar_folder_path, local_subfolder_path):
	lidar_info_list = []
	start_time_overall = time.time()
	total_lidar_duration = 0
	df_total_timestamps = pd.DataFrame()
	number_of_error_bags = 0
	average_lidar_frame_rate = 0
	number_of_bad_bags = 0
	if os.path.exists(local_subfolder_path+"/processed/lidar_data") and (len(os.listdir(lidar_folder_path)) == len(os.listdir(local_subfolder_path+"/processed/lidar_data"))):
		if os.path.exists(local_subfolder_path+"/processed/lidar_timestamps/lidar_timestamps.csv"):
			print(f"Folder already processed.")
			df_total_timestamps = pd.read_csv(local_subfolder_path+"/processed/lidar_timestamps/lidar_timestamps.csv")
			return [], 0, 0, 0, 0, df_total_timestamps
		else:
			print(f"LiDAR data already extracted. Processing the timestamps.")
			for lidar_csv in sorted(os.listdir(local_subfolder_path+"/processed/lidar_data")):
				print(f"Reading csv file: {lidar_csv}")
				df_laser = pd.read_csv(local_subfolder_path+"/processed/lidar_data/"+lidar_csv)
				df_total_timestamps, average_diff, max_diff = get_lidar_bag_info(df_laser, df_total_timestamps)	
	else:			  
		for lidar_file in sorted(os.listdir(lidar_folder_path)):
			if lidar_file.endswith(".bag"):
				try:
					bag_dir = os.path.join(lidar_folder_path,lidar_file)
					bag = bagpy.bagreader(bag_dir)
					LASER_MSG=bag.message_by_topic('/os_node/lidar_packets')
					df_laser = pd.read_csv(LASER_MSG)

					#Save the original lidar data to a csv file
					save_lidar_bag_as_csv(df_laser, lidar_file, local_subfolder_path)
					#Get the timestamps for each bag and combine them to get the timestamps for all the bags
					df_total_timestamps, average_diff, max_diff = get_lidar_bag_info(df_laser, df_total_timestamps)
					#Get Lidar statistics
					lidar_stats, lidar_duration = get_lidar_statistics(lidar_file, df_laser, bag, average_diff, max_diff)
					
					lidar_info_list.append(lidar_stats)
					total_lidar_duration += lidar_duration
				except Exception as e:
					print(f"Error processing file {lidar_file}: {e}")
					lidar_info = {}
					lidar_info["bag_file"] = lidar_file
					lidar_info["num_frames"] = -1
					lidar_info["duration"] = -1
					lidar_info["lidar_frame_rate"] = -1
					lidar_info["average_diff"] = -1
					lidar_info["max_diff"] = -1
					lidar_info_list.append(lidar_info)
					number_of_error_bags += 1
					continue
	
	if len(lidar_info_list) > 0:
		average_lidar_frame_rate = round(sum([info["lidar_frame_rate"] for info in lidar_info_list]) / len(lidar_info_list),2)
		number_of_bad_bags = len([info for info in lidar_info_list if info["lidar_frame_rate"] < 9.8])
	
	# print(df_total_timestamps.head())
	#Rename the column 0 to lidar_timestamps
	df_total_timestamps.columns = ['lidar_timestamps']
	df_total_timestamps["lidar_timestamp_gap"] = df_total_timestamps["lidar_timestamps"].diff()
	df_total_timestamps["inserted_lidar_frame"] = 0
	
	save_combined_lidar_timestamps(df_total_timestamps, local_subfolder_path)
	clean_up_lidar_folder(lidar_folder_path)

	total_time = round((time.time() - start_time_overall)/60,2)
	print(f"Time taken for all bags is {total_time} mins")
	return lidar_info_list, total_lidar_duration, average_lidar_frame_rate, number_of_bad_bags, total_time, number_of_error_bags

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
	for camera in six_camera_timestamps.keys():
		df_total_timestamps[camera] = 0
		df_total_timestamps[camera+"_gap"] = 0
	for i in range(df_total_timestamps.shape[0]):
		lidar_timestamp = df_total_timestamps['lidar_timestamps'].iloc[i]
		#Find the closest timestamp for each camera
		for camera in six_camera_timestamps.keys():
			camera_timestamps = six_camera_timestamps[camera]
			closest_timestamp = min(camera_timestamps, key=lambda x:abs(x-lidar_timestamp))
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

# Main function to process all subfolders
def process_subfolders(root_folder, folders_to_process, local_path, processed_subfolders, processed_subfolders_with_error,  path_to_processed_subfolders, path_to_processed_subfolders_with_error):
	"""
	This function processes all the subfolders in the root folder and extracts the lidar data and timestamps.

	Args:
	root_folder: The path to the root folder containing subfolders.
	folders_to_process: A list of subfolders to process.
	local_path: The path to the local folder where the subfolders will be copied.
	processed_subfolders: A list of subfolders that have already been processed.
	processed_subfolders_with_error: A list of subfolders that have already been processed with errors.
	path_to_processed_subfolders: The path to the text file containing the list of processed subfolders.
	path_to_processed_subfolders_with_error: The path to the text file containing the list of processed subfolders with errors.
	"""

	break_counter = 0
	start_time = time.time()
	lidar_info_generated_folders = []
	for subfolder in os.listdir(local_path):
		if subfolder.endswith(".csv"):
			#CSV name looks like this: lidar_info_26-06-22_21-19-14.csv, get the subfolder name from this: 26-06-22_21-19-14
			lidar_info_generated_folders.append(subfolder.split("_")[2]+"_"+subfolder.split("_")[3].split(".")[0])
	# print(lidar_info_generated_folders)

	for subfolder in os.listdir(root_folder):
		if subfolder.strip() not in folders_to_process:
			continue
		if subfolder in processed_subfolders or subfolder in lidar_info_generated_folders:
			print(f"Subfolder {subfolder} already processed. Skipping...")
			continue
		if subfolder in processed_subfolders_with_error:
			print(f"Subfolder {subfolder} already processed with error. Skipping...")
			continue
		timestamp_folder_path = os.path.join(root_folder, subfolder, "processed", "timestamps")
		lidar_folder_path = os.path.join(root_folder, subfolder, "lidar")
	
		print(f"Processing subfolder {subfolder}")
		try:
			subfolder_path = os.path.join(root_folder, subfolder)
			#Copy the contents of the subfolder to a new folder and process the new folder

			subfolder_new_local_path = os.path.join(local_path, subfolder)
			os.makedirs(subfolder_new_local_path, exist_ok=True)

			copy_time = time.time()	
			local_timestamp_folder_path = os.path.join(subfolder_new_local_path, "processed", "timestamps")

			#Check if timestamp folder is copied completely with all the files and subfolders
			if os.path.isdir(local_timestamp_folder_path) and len(os.listdir(timestamp_folder_path)) == len(os.listdir(local_timestamp_folder_path)):
				print(f"Timestamp folder already exists.")
			elif os.path.isdir(timestamp_folder_path):
				shutil.rmtree(local_timestamp_folder_path, ignore_errors=True)
				shutil.copytree(timestamp_folder_path, local_timestamp_folder_path)

			
			local_lidar_folder_path = os.path.join(subfolder_new_local_path, "lidar")
			#Check if lidar folder is copied completely with all the files and subfolders

			if os.path.isdir(local_lidar_folder_path) and len(os.listdir(lidar_folder_path)) == len(os.listdir(local_lidar_folder_path)):
				print(f"Lidar Folder already copied.")
			else:
				shutil.rmtree(local_lidar_folder_path, ignore_errors=True)
				shutil.copytree(lidar_folder_path, local_lidar_folder_path)
				print(f"Copied subfolder {subfolder} to {subfolder_new_local_path} in {time.time() - copy_time} seconds")
		
			
			#Get the lidar timestamps and Camera timestamps
			lidar_info, total_lidar_duration, average_lidar_frame_rate, number_of_bad_bags, time_taken, number_of_error_bags = extract_lidar_data(local_lidar_folder_path, subfolder_new_local_path)
			data = []
			data.append({
			"Subfolder": subfolder,
			"Duration from lidar(minutes)": round(total_lidar_duration/60),
			"Average_lidar_frame_rate": average_lidar_frame_rate,
			"Total_Bags": len(lidar_info) if lidar_info else -1,
			"Number_of_bad_bags(<9.8fps)": number_of_bad_bags,
			"Number_of_error_bags(Failed to open)": number_of_error_bags,
			"Total_time_processing(min)": round(time_taken),
			})
			# print(data[-1])
			df = pd.DataFrame(data)
			#Append the data to the csv file
			if os.path.exists("extracted_raw_data_lidar_summary.csv"):
				df.to_csv("extracted_raw_data_lidar_summary.csv", mode='a', header=False, index=False)
			else:
				df.to_csv("extracted_raw_data_lidar_summary.csv", index=False)
			#Delete the local lidar if destionation folder is different from source folder
			if root_folder != local_path:
				shutil.rmtree(local_lidar_folder_path, ignore_errors=True)
			
			if os.path.exists(path_to_processed_subfolders):
				with open(path_to_processed_subfolders, "a") as file:
					file.write(subfolder + "\n")
			else:
				with open(path_to_processed_subfolders, "w") as file:
					file.write(subfolder + "\n")
			
		except Exception as e:
			print(f"Error processing subfolder {subfolder_path}: {e}")
			#Delete the local lidar if destionation folder is different from source folder
			if root_folder != local_path:
				shutil.rmtree(local_lidar_folder_path, ignore_errors=True)
			if os.path.exists(path_to_processed_subfolders_with_error):
				with open(path_to_processed_subfolders_with_error, "a") as file:
					file.write(subfolder + "\n")
			else:
				with open(path_to_processed_subfolders_with_error, "w") as file:
					file.write(subfolder + "\n")
	print(f"Processing took {round((time.time() - start_time)/60)} minutes")

# Example usage
source_raw_dath_path = "/mnt/tasismb/Reordered_drive/Raw_Data" 
local_dest_raw_data_path = "/media/abinmath/TASI_ESCOOTER_Drive1/Extracted_Raw_Data"

path_to_folders_to_process = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/extraction_folders.txt"
path_to_processed_subfolders = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/extraction_processed_subfolders.txt"
path_to_processed_subfolders_with_error = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/extraction_processed_subfolders_with_error.txt"


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
