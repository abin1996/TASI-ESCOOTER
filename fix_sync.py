import json
import os
import pandas as pd
from datetime import datetime
import cv2
import bagpy
import time
import struct

def get_lidar_info(lidar_folder_path, subfolder_path):
	lidar_info_list = []
	#MCalculate the time taken for each bag and for all the bags in the folder
	IMU_outdir = os.path.join(subfolder_path,'imu')
	if not os.path.exists(IMU_outdir):
		os.makedirs(IMU_outdir)
	start_time_overall = time.time()
	times_for_each_bag = []
	# Iterate through all files in the folder in ascending order

	for lidar_file in sorted(os.listdir(lidar_folder_path)):
		if lidar_file.endswith(".bag"):
			start_time = time.time()
			bag_dir = os.path.join(lidar_folder_path,lidar_file)
			
			bag = bagpy.bagreader(bag_dir)
			print(bag.start_time)
			# LASER_MSG=bag.message_by_topic('/os_node/lidar_packets')
			# df_laser = pd.read_csv(LASER_MSG)

			LASER_MSG_imu=bag.message_by_topic('/os_node/imu_packets')
			df_laser_imu = pd.read_csv(LASER_MSG_imu)
			IMU_data = pd.DataFrame(columns=['buf_time','imu_time','acc_time','gyro_time','Accx','Accy','Accz','Rotx','Roty','Rotz'])
			for ind,row in df_laser_imu.iterrows():
				buf  = row.buf
				raw_packet=eval(buf)
				buf_time = row.Time
				imu_time = struct.unpack('q', raw_packet[:8])[0]
				acc_time = struct.unpack('q', raw_packet[8:16])[0]
				gyro_time =struct.unpack('q', raw_packet[16:24])[0]
				Accx = struct.unpack('f',raw_packet[24:28])[0]
				Accy = struct.unpack('f',raw_packet[28:32])[0]
				Accz = struct.unpack('f',raw_packet[32:36])[0]
				Rotx=struct.unpack('f',raw_packet[36:40])[0]
				Roty=struct.unpack('f',raw_packet[40:44])[0]
				Rotz = struct.unpack('f',raw_packet[44:48])[0]
				IMU_data=pd.concat([IMU_data,pd.DataFrame([[buf_time,imu_time,acc_time,gyro_time,Accx,Accy,Accz,Rotx,Roty,Rotz]],columns=['buf_time','imu_time','acc_time','gyro_time','Accx','Accy','Accz','Rotx','Roty','Rotz'])])
			IMU_data.to_csv(os.path.join(IMU_outdir,bag_dir.split('_')[-1]+'.csv'))
			# print(df_laser.describe())
			lidar_info = {}
			# lidar_info["num_frames"] = len(df_laser)
			lidar_info["imu_num_frames"] = len(df_laser_imu)
			lidar_info["duration"] = bag.end_time - bag.start_time
			# lidar_info["lidar_frame_rate"] = lidar_info["num_frames"] / lidar_info["duration"]
			lidar_info["imu_frame_rate"] = lidar_info["imu_num_frames"] / lidar_info["duration"]
			lidar_info_list.append(lidar_info)
			times_for_each_bag.append(time.time() - start_time)
			print(f"Time taken for {lidar_file} is {time.time() - start_time}")
	
	print(f"Time taken for all bags is {time.time() - start_time_overall}")
	return lidar_info_list

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

def process_subfolders(root_folder):
	"""
	Iterates through all subfolders in the root folder, processes timestamp files, and creates a DataFrame.

	Args:
	root_folder: The path to the root folder containing subfolders.
	"""

	data = []
	break_counter = 0
	for subfolder in os.listdir(root_folder):
		subfolder_path = os.path.join(root_folder, subfolder)
		timestamp_folder_path = os.path.join(root_folder, subfolder, "processed", "timestamps")
		synchronized_folder_path = os.path.join(root_folder, subfolder, "processed", "synchronized_timestamps")
		lidar_folder_path = os.path.join(root_folder, subfolder, "lidar")

		print(f"Processing subfolder {subfolder}")
		if os.path.isdir(timestamp_folder_path):
			try:
				break_counter += 1
				# if break_counter == 5:
				# 	break
				
				lidar_info = get_lidar_info(lidar_folder_path, subfolder_path)
				print(lidar_info)
				# avg_differences, max_diffs, total_frames = calculate_timestamp_differences_for_folder(timestamp_folder_path)
				# clicks, video_minutes = get_m tadata(subfolder,subfolder_path)

				
				# if not video_minutes:
				# 	video_minutes = float("{:.2f}".format(max(total_frames) / 600))
				# print(avg_differences)
				# print(max_diffs)
				# print(total_frames)
				data.append({
				"Subfolder - Step 1": subfolder,
				# "Duration (minutes)": video_minutes
				})


			except Exception as e:
				print(f"Error processing subfolder {subfolder_path}: {e}")
  # print(data)
	df = pd.DataFrame(data)
	df.to_csv("video_folder_info.csv", index=False)

# Example usage
root_folder = "/Users/abinmath/Documents/TASI-ESCOOTER/dataset"  # Replace with your actual root folder path
problematic_root_folder = "/Volumes/TASI-VRU Data Storage/Problematic_Datasets"  # Replace with your actual root folder path

process_subfolders(root_folder)
# process_problematic_datasets(problematic_root_folder)
