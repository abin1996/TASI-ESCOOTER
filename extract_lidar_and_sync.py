import json
import os
import shutil
import pandas as pd
from datetime import datetime
import cv2
import bagpy
import time
import struct

def get_lidar_info(lidar_folder_path, subfolder_path):
	lidar_info_list = []
	#MCalculate the time taken for each bag and for all the bags in the folder
	# IMU_outdir = os.path.join(subfolder_path,'imu')
	# if not os.path.exists(IMU_outdir):
	# 	os.makedirs(IMU_outdir)
	start_time_overall = time.time()
	times_for_each_bag = []
	# Iterate through all files in the folder in ascending order
	total_lidar_duration = 0
	for lidar_file in sorted(os.listdir(lidar_folder_path)):
		if lidar_file.endswith(".bag"):
			try:
				start_time = time.time()
				bag_dir = os.path.join(lidar_folder_path,lidar_file)
				
				bag = bagpy.bagreader(bag_dir)
				# print(bag.start_time)
				LASER_MSG=bag.message_by_topic('/os_node/lidar_packets')
				df_laser = pd.read_csv(LASER_MSG)
				#Check the average time gap between the timestamps in the lidar data
				average_diff =  df_laser['Time'].diff().mean()
				max_diff = df_laser['Time'].diff().max()
			
				lidar_info = {}
				lidar_info["bag_file"] = lidar_file
				lidar_info["num_frames"] = float(len(df_laser)/128)
				# lidar_info["imu_num_frames"] = len(df_laser_imu)
				lidar_info["duration"] = bag.end_time - bag.start_time
				lidar_info["lidar_frame_rate"] = round(float(lidar_info["num_frames"] / lidar_info["duration"]),2)
				lidar_info["average_diff"] = average_diff
				lidar_info["max_diff"] = max_diff
				# lidar_info["imu_frame_rate"] = lidar_info["imu_num_frames"] / lidar_info["duration"]
				total_lidar_duration += lidar_info["duration"]
				lidar_info_list.append(lidar_info)
				times_for_each_bag.append(time.time() - start_time)
				# print(f"Time taken for {lidar_file} is {time.time() - start_time}")
			except Exception as e:
				print(f"Error processing file {lidar_file}: {e}")
				lidar_info = {}
				lidar_info["bag_file"] = lidar_file
				lidar_info["num_frames"] = 0
				lidar_info["duration"] = 0
				lidar_info["lidar_frame_rate"] = 0
				lidar_info["average_diff"] = 0
				lidar_info["max_diff"] = 0
				lidar_info_list.append(lidar_info)
				continue
	average_lidar_frame_rate = round(sum([info["lidar_frame_rate"] for info in lidar_info_list]) / len(lidar_info_list),2)
	number_of_bad_bags = len([info for info in lidar_info_list if info["lidar_frame_rate"] < 9.8])
	total_time = round((time.time() - start_time_overall)/60,2)
	print(f"Time taken for all bags is {total_time} mins and avg frame rate is {average_lidar_frame_rate}")
	return lidar_info_list, total_lidar_duration, average_lidar_frame_rate, average_lidar_frame_rate, number_of_bad_bags, total_time

def calculate_timestamp_differences(filename):
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

	# Calculate differences in milliseconds between consecutive timestamps
	differences = [(timestamps_ms[i + 1] - timestamps_ms[i]) for i in range(len(timestamps) - 1)]

	# Print results
	# print(f"Total timestamps: {len(timestamps)}")
	# print(f"Average difference (ms): {sum(differences) / len(differences):.2f}")
	# print("Individual differences (ms):")
	# for i, difference in enumerate(differences):
	#   print(f"\tDifference between timestamps {i} and {i + 1}: {difference:.2f}")
	# Print results
	# print(f"Total timestamps: {len(timestamps)}")
	# print(f"Average difference (ms): {sum(differences) / len(differences):.2f}")
	avg_diff = int(sum(differences) / len(differences))
	max_diff = int(max(differences))

	#Consider the first timestamp as time 00:00:00  and Now find the minutes:seconds where the difference between timestamp is greater than 1.5 times the average difference.
	#Each timestamp is 100 mil
	
	# for i, difference in enumerate(differences):
	# 	if difference > 1.5 * avg_diff:
	# 		print(f"\tDifference between timestamps {i} and {i + 1}: {difference:.2f}")
	# 		print(f"\tTime difference between timestamps {i} and {i + 1}: {datetime.utcfromtimestamp(timestamps_ms[i]).strftime('%M:%S')} and {datetime.utcfromtimestamp(timestamps_ms[i+1]).strftime('%M:%S')}")

	return avg_diff, max_diff, len(timestamps)

# # Example usage
# filename = "/Volumes/TASI-VRU Data Storage/Problematic_Datasets/26-06-22_21-19-14/processed/timestamps/images6_timestamps.txt"  # Replace with your actual filename
# calculate_timestamp_differences(filename)



def calculate_timestamp_differences_for_folder(timestamp_folder):
	"""
	Calculates the average difference of timestamps in nanoseconds for all files in the given folder.

	Args:
	timestamp_folder: The path to the folder containing timestamp files.

	Returns:
	A list of average differences for each file in the folder.
	"""

	avg_differences = []
	total_frames = []
	max_diffs = []
	if os.path.isdir(timestamp_folder):
		print(f"Processing folder {timestamp_folder}")
		for timestamp_file in os.listdir(timestamp_folder):
			filename = os.path.join(timestamp_folder, timestamp_file)
			try:
				avg_difference, max_diff, total_frame = calculate_timestamp_differences(filename)
				avg_differences.append(avg_difference)
				total_frames.append(total_frame)
				max_diffs.append(max_diff)
				
			except ValueError as e:
				print(f"Error processing file {filename}: {e}")

	return avg_differences, max_diffs, total_frames

def process_subfolders(root_folder, folders_to_process, local_path, processed_subfolders, processed_subfolders_with_error):
	"""
	Iterates through all subfolders in the root folder, processes timestamp files, and creates a DataFrame.

	Args:
	root_folder: The path to the root folder containing subfolders.
	"""

	data = []
	break_counter = 0
	start_time = time.time()
	lidar_info_generated_folders = []
	for subfolder in os.listdir(local_path):
		if subfolder.endswith(".csv"):
			#CSV name looks like this: lidar_info_26-06-22_21-19-14.csv, get the subfolder name from this: 26-06-22_21-19-14
			lidar_info_generated_folders.append(subfolder.split("_")[2]+"_"+subfolder.split("_")[3].split(".")[0])
	print(lidar_info_generated_folders)

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
		# synchronized_folder_path = os.path.join(root_folder, subfolder, "processed", "synchronized_timestamps")
		

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
				print(f"Folder already exists.")
			elif os.path.isdir(timestamp_folder_path):
				shutil.rmtree(local_timestamp_folder_path, ignore_errors=True)
				shutil.copytree(timestamp_folder_path, local_timestamp_folder_path)

			
			local_lidar_folder_path = os.path.join(subfolder_new_local_path, "lidar")
			#Check if lidar folder is copied completely with all the files and subfolders

			if os.path.isdir(local_lidar_folder_path) and len(os.listdir(lidar_folder_path)) == len(os.listdir(local_lidar_folder_path)):
				print(f"Folder already exists.")
			else:
				shutil.rmtree(local_lidar_folder_path, ignore_errors=True)
				shutil.copytree(lidar_folder_path, local_lidar_folder_path)

			print(f"Copied subfolder {subfolder} to {subfolder_new_local_path} in {time.time() - copy_time} seconds")
			break_counter += 1
			# if break_counter == 5:
			# 	break
			
			lidar_info, total_lidar_duration, average_lidar_frame_rate, average_lidar_frame_rate, number_of_bad_bags, time_taken = get_lidar_info(local_lidar_folder_path, subfolder_path)
			df = pd.DataFrame(lidar_info)
			df.to_csv(local_path+"/lidar_info_" + subfolder + ".csv", index=False)
			print(average_lidar_frame_rate)
			avg_differences = []
			max_diffs = []
			total_frames = []
			if os.path.isdir(timestamp_folder_path):
				avg_differences, max_diffs, total_frames = calculate_timestamp_differences_for_folder(local_timestamp_folder_path)
			# clicks, video_minutes = get_m tadata(subfolder,subfolder_path)

			
			# if not video_minutes:
			video_minutes = float("{:.2f}".format(max(total_frames) / 600)) if total_frames else -1
			# print(avg_differences)
			# print(max_diffs)
			# print(total_frames)
			data.append({
			"Subfolder": subfolder,
			"Duration from lidar(minutes)": round(total_lidar_duration/60),
			"Duration from Video(minutes)": video_minutes,
			"Average_lidar_frame_rate": average_lidar_frame_rate,
			"Total_Bags": len(lidar_info),
			"Number_of_bad_bags(<9.8fps)": number_of_bad_bags,
			"Total_time_processing(min)": round(time_taken),
			"Timestamp Cam 1 Avg Diff btwn frames(ms)": avg_differences[0] if avg_differences else -1,
			"Timestamp Cam 2 Avg Diff(ms) btwn frames": avg_differences[1] if avg_differences else -1,
			"Timestamp Cam 3 Avg Diff(ms) btwn frames": avg_differences[2] if avg_differences else -1,
			"Timestamp Cam 4 Avg Diff(ms) btwn frames": avg_differences[3] if avg_differences else -1, 
			"Timestamp Cam 5 Avg Diff(ms) btwn frames": avg_differences[4] if avg_differences else -1,
			"Timestamp Cam 6 Avg Diff(ms) btwn frames": avg_differences[5] if avg_differences else -1,
			})
			print(data[-1])
			df = pd.DataFrame(data)
			#Append the data to the csv file
			if os.path.exists("raw_data_lidar_info.csv"):
				df.to_csv("raw_data_lidar_info.csv", mode='a', header=False, index=False)
			else:
				df.to_csv("raw_data_lidar_info.csv", index=False)
			#Delete the local lidar and timestamp folders
			shutil.rmtree(subfolder_new_local_path)
			with open("processed_subfolders.txt", "a") as file:
				file.write(subfolder + "\n")
		except Exception as e:
			print(f"Error processing subfolder {subfolder_path}: {e}")
			#Remove the extracted lidar folders
			shutil.rmtree(subfolder_new_local_path, ignore_errors=True)
			with open("processed_subfolders_with_error.txt", "a") as file:
				file.write(subfolder + "\n")
  # print(data)
	
	# df.to_csv("raw_data_lidar_info.csv", index=False)
	print(f"Processing took {round((time.time() - start_time)/60)} minutes")

# Example usage
root_folder = "/mnt/tasismb/Reordered_drive/Raw_Data" 
local_raw_data_path = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/src_raw_data"
 # Replace with your actual root folder path
# problematic_root_folder = "/Volumes/TASI-VRU Data Storage/Problematic_Datasets"  # Replace with your actual root folder path
path_folders_to_process = "subfolders_to_process.txt"
path_to_processed_subfolders = "processed_subfolders.txt"
path_to_processed_subfolders_with_error = "processed_subfolders_with_error.txt"

with open(path_to_processed_subfolders_with_error, 'r') as file:
	processed_subfolders_with_error = file.readlines()
	processed_subfolders_with_error = [f.strip() for f in processed_subfolders_with_error]

with open(path_folders_to_process, 'r') as file:
	folders_to_process = file.readlines()
	folders_to_process = [f.strip() for f in folders_to_process]
# print(folders_to_process)

with open(path_to_processed_subfolders, 'r') as file:
	processed_subfolders = file.readlines()
	processed_subfolders = [f.strip() for f in processed_subfolders]
process_subfolders(root_folder, folders_to_process, local_raw_data_path, processed_subfolders, processed_subfolders_with_error)
# process_problematic_datasets(problematic_root_folder)
