import json
import os
import pandas as pd
from datetime import datetime
import cv2
import bagpy

def get_video_length(video_folder_path):
	"""
	This function takes the path to a video file and returns the length of the video in seconds.

	Args:
	video_path: The path to the video file.

	Returns:
	The length of the video in seconds.
	"""
	video_duration = -1
	if os.path.isdir(video_folder_path):
		print(f"Processing folder {video_folder_path}")
		for video_file in os.listdir(video_folder_path):
	# Load the video file
			video_path = os.path.join(video_folder_path, video_file)
			cap = cv2.VideoCapture(video_path)

			# Get the number of frames in the video
			num_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)

			# Get the frame rate of the video
			fps = cap.get(cv2.CAP_PROP_FPS)

			# Calculate the duration of the video in seconds
			duration = round(num_frames / fps)
			video_duration = round(duration / 60, 2)
			# Release the video capture object
			cap.release()

	return video_duration



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

def get_metadata(subfolder,subfolder_path):
	"""
	This function reads metadata from a json file and returns the metadata as a dictionary.

	Args:
	timestamp_folder: The path to the folder containing the metadata json file.

	Returns:
	A dictionary containing the metadata.
	"""
	# Check if the metadata file exists

	metadata_file = os.path.join(subfolder_path, "{}.json".format(subfolder))
	metadata_file_alt = os.path.join(subfolder_path, "{}_proc.json".format(subfolder))
	if not os.path.exists(metadata_file):
		if not os.path.exists(metadata_file_alt):
			print(f"Metadata file not found in {subfolder_path}")
			return None, None
		else:
			metadata_file = metadata_file_alt
  # Read metadata from the file
	with open(metadata_file, 'r') as file:
		metadata = json.load(file)
		clicks = int(metadata["joystick_clicks"])
		video_minutes = float("{:.2f}".format(metadata["video_info"]["video_duration"]["video1"]))
	return clicks, video_minutes

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
			scenario_info = {}
			#The scenario_folder looks like this: 28-07-22_15-39-58_15341600_3_002_010
			#The different parts are separated by underscores, 28-07-22_15-39-58 is the timestamp, 15341600 is the from time(15min 34sec) and to time(16min 00sec), 2 is the city number, 001 is the scenario number, and 100 is the ecsoote/bicycle information
			scenario_info["video_subfolder"] = subfolder
			scenario_info["from_time"] = scenario_folder.split("_")[2][:4]
			scenario_info["from_time_minutes"] = scenario_info["from_time"][:2]
			scenario_info["from_time_seconds"] = scenario_info["from_time"][2:]
			scenario_info["to_time"] = scenario_folder.split("_")[2][-4:]
			scenario_info["to_time_minutes"] = scenario_info["to_time"][:2]
			scenario_info["to_time_seconds"] = scenario_info["to_time"][2:]
			scenario_info["city_number"] = scenario_folder.split("_")[3]
			scenario_info["scenario_number"] = scenario_folder.split("_")[4]
			scenario_info["escooter_bicycle"] = scenario_folder.split("_")[5]
			scenario_info["annotation_info_exists"] = check_if_annotation_info_exists(scenario_folder)
			# print(scenario_info)
			all_scenarios_for_subfolder.append(scenario_info)
	return all_scenarios_for_subfolder

def get_lidar_info(lidar_folder_path):
	lidar_info_list = []
	for lidar_file in os.listdir(lidar_folder_path):
		if lidar_file.endswith(".bag"):
			bag = bagpy.bagreader(os.path.join(lidar_folder_path,lidar_file))
			print(bag.start_time)
			LASER_MSG=bag.message_by_topic('/os_node/lidar_packets')
			df_laser = pd.read_csv(LASER_MSG)
			print(df_laser.describe())
			lidar_info = {}
			lidar_info["num_frames"] = len(df_laser)
			lidar_info["duration"] = bag.end_time - bag.start_time
			lidar_info["frame_rate"] = lidar_info["num_frames"] / lidar_info["duration"]
			lidar_info_list.append(lidar_info)
	return lidar_info_list
def get_lidar_bag_count(lidar_folder_path):
	bag_count = 0
	if os.path.isdir(lidar_folder_path):
		print(f"Processing folder {lidar_folder_path}")
		for lidar_file in os.listdir(lidar_folder_path):
			if lidar_file.endswith(".bag"):
				bag_count += 1
	else:
		print(f"Folder {lidar_folder_path} does not exist")
		bag_count = -1
	return bag_count
def process_problematic_datasets(root_folder):
	data = []
	break_counter = 0
	for subfolder in os.listdir(root_folder):
		subfolder_path = os.path.join(root_folder, subfolder)
		timestamp_folder_path = os.path.join(root_folder, subfolder, "processed", "timestamps")
		videos_folder_path = os.path.join(root_folder, subfolder, "processed","videos")
		lidar_folder_path = os.path.join(root_folder, subfolder, "lidar")
		print(f"Processing subfolder {subfolder}")
		is_timestamp_present = False
		try:
			video_minutes = None
			break_counter += 1
			# if break_counter == 5:
			# 	break
			
			lidar_count = get_lidar_bag_count(lidar_folder_path)
			# print(lidar_info)
			avg_differences, max_diffs, total_frames = calculate_timestamp_differences_for_folder(timestamp_folder_path)
			if os.path.isdir(timestamp_folder_path) and total_frames:
				is_timestamp_present = True
			
			if total_frames: 
				video_minutes = float("{:.2f}".format(max(total_frames) / 600))
			elif not video_minutes and not total_frames:
				video_minutes = get_video_length(videos_folder_path)
			# print(avg_differences)
			# print(max_diffs)
			# print(total_frames)
			individual_differences = []
			if avg_differences and total_frames:
				for i, avg_diff in enumerate(avg_differences):
					individual_differences.append(round((total_frames[i] / (1000/avg_diff))/60))
			data.append({
			"Subfolder": subfolder,
			"Timestamps Present": is_timestamp_present,
			"Duration of minutes (minutes)": video_minutes,
			"Number of LiDAR Bags": lidar_count,
			"Cam 1 Expected Duration (minutes)": individual_differences[0] if individual_differences else -1,
			"Cam 2 Expected Duration (minutes)": individual_differences[1] if individual_differences else -1,
			"Cam 3 Expected Duration (minutes)": individual_differences[2] if individual_differences else -1,
			"Cam 4 Expected Duration (minutes)": individual_differences[3] if individual_differences else -1,
			"Cam 5 Expected Duration (minutes)": individual_differences[4] if individual_differences else -1,
			"Cam 6 Expected Duration (minutes)": individual_differences[5] if individual_differences else -1,
			"Max Deviation across 6 cams (ms)": max(individual_differences) - min(individual_differences) if len(individual_differences) > 1 else -1,
			"Timestamp Cam 1 Total Frames": total_frames[0] if total_frames else -1,
			"Timestamp Cam 2 Total Frames": total_frames[1] if total_frames else -1,
			"Timestamp Cam 3 Total Frames": total_frames[2] if total_frames else -1,
			"Timestamp Cam 4 Total Frames": total_frames[3] if total_frames else -1,
			"Timestamp Cam 5 Total Frames": total_frames[4] if total_frames else -1,
			"Timestamp Cam 6 Total Frames": total_frames[5] if total_frames else -1,
			"Max Total Frame Deviation across 6 cams": max(total_frames) - min(total_frames) if len(total_frames) > 1 else -1,
			"Max Deviation across 6 cams (ms)": max(avg_differences) - min(avg_differences) if len(avg_differences) > 1 else -1,
			"Timestamp Cam 1 Avg Diff btwn frames(ms)": avg_differences[0] if avg_differences else -1,
			"Timestamp Cam 2 Avg Diff(ms) btwn frames": avg_differences[1] if avg_differences else -1,
			"Timestamp Cam 3 Avg Diff(ms) btwn frames": avg_differences[2] if avg_differences else -1,
			"Timestamp Cam 4 Avg Diff(ms) btwn frames": avg_differences[3] if avg_differences else -1, 
			"Timestamp Cam 5 Avg Diff(ms) btwn frames": avg_differences[4] if avg_differences else -1,
			"Timestamp Cam 6 Avg Diff(ms) btwn frames": avg_differences[5] if avg_differences else -1,
			"Timestamp Cam 1 Max Time Diff btwn frames(ms)": max_diffs[0] if max_diffs else -1,
			"Timestamp Cam 2 Max Time Diff btwn frames(ms)": max_diffs[1] if max_diffs else -1,
			"Timestamp Cam 3 Max Time Diff btwn frames(ms)": max_diffs[2] if max_diffs else -1,
			"Timestamp Cam 4 Max Time Diff btwn frames(ms)": max_diffs[3] if max_diffs else -1,
			"Timestamp Cam 5 Max Time Diff btwn frames(ms)": max_diffs[4] if max_diffs else -1,
			"Timestamp Cam 6 Max Time Diff btwn frames(ms)": max_diffs[5] if max_diffs else -1,
			
			})


		except Exception as e:
			print(f"Error processing subfolder {subfolder_path}: {e}")
  # print(data)
	df = pd.DataFrame(data)
	df.to_csv("problematic_video_folder_info.csv", index=False)


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
		print(f"Processing subfolder {subfolder}")
		if os.path.isdir(timestamp_folder_path):
			try:
				break_counter += 1
				# if break_counter == 5:
				# 	break
				
				# lidar_info = get_lidar_info(lidar_folder_path)
				# print(lidar_info)
				avg_differences, max_diffs, total_frames = calculate_timestamp_differences_for_folder(timestamp_folder_path)
				clicks, video_minutes = get_metadata(subfolder,subfolder_path)
				scenario_data = get_scenario_info_for_subfolder(subfolder, subfolder_path)
				if scenario_data:
					all_scenarios.extend(scenario_data)
				
				if not video_minutes:
					video_minutes = float("{:.2f}".format(max(total_frames) / 600))
				# print(avg_differences)
				# print(max_diffs)
				# print(total_frames)
				if avg_differences:
					data.append({
					"Subfolder - Step 1": subfolder,
					"Duration (minutes)": video_minutes,
					"Joystick Clicks": clicks,
					"Scenarios Identified - Step 2":len(scenario_data),
					"Scenarios Annotated(XML) - Step 3": sum([1 for scenario in scenario_data if scenario["annotation_info_exists"]]),
					"Max Deviation across 6 cams (ms)": max(avg_differences) - min(avg_differences) if len(avg_differences) > 1 else 0,
					"Timestamp Cam 1 Avg Diff btwn frames(ms)": avg_differences[0],
					"Timestamp Cam 2 Avg Diff(ms) btwn frames": avg_differences[1],
					"Timestamp Cam 3 Avg Diff(ms) btwn frames": avg_differences[2],
					"Timestamp Cam 4 Avg Diff(ms) btwn frames": avg_differences[3],
					"Timestamp Cam 5 Avg Diff(ms) btwn frames": avg_differences[4],
					"Timestamp Cam 6 Avg Diff(ms) btwn frames": avg_differences[5],
					"Timestamp Cam 1 Max Time Diff btwn frames(ms)": max_diffs[0],
					"Timestamp Cam 2 Max Time Diff btwn frames(ms)": max_diffs[1],
					"Timestamp Cam 3 Max Time Diff btwn frames(ms)": max_diffs[2],
					"Timestamp Cam 4 Max Time Diff btwn frames(ms)": max_diffs[3],
					"Timestamp Cam 5 Max Time Diff btwn frames(ms)": max_diffs[4],
					"Timestamp Cam 6 Max Time Diff btwn frames(ms)": max_diffs[5],
					"Timestamp Cam 1 Total Frames": total_frames[0],
					"Timestamp Cam 2 Total Frames": total_frames[1],
					"Timestamp Cam 3 Total Frames": total_frames[2],
					"Timestamp Cam 4 Total Frames": total_frames[3],
					"Timestamp Cam 5 Total Frames": total_frames[4],
					"Timestamp Cam 6 Total Frames": total_frames[5],
					"Max Total Frame Dev across 6 cams": max(total_frames) - min(total_frames) if len(total_frames) > 1 else 0,

					})


			except Exception as e:
				print(f"Error processing subfolder {subfolder_path}: {e}")
  # print(data)
	df = pd.DataFrame(data)
	df.to_csv("video_folder_info.csv", index=False)
	df_frame_count = pd.DataFrame(all_scenarios)
	df_frame_count.to_csv("scenario_info.csv", index=False, columns=["video_subfolder", "annotation_info_exists","from_time_minutes", "from_time_seconds", "to_time_minutes", "to_time_seconds", "city_number", "scenario_number", "escooter_bicycle"])

# Example usage
root_folder = "/Volumes/TASI-VRU Data Storage/Reordered_drive/Raw_Data"  # Replace with your actual root folder path
problematic_root_folder = "/Volumes/TASI-VRU Data Storage/Problematic_Datasets"  # Replace with your actual root folder path

# process_subfolders(root_folder)
process_problematic_datasets(problematic_root_folder)
