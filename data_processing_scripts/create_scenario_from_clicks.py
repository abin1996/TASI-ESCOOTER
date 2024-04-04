import pandas as pd
import datetime
import numpy as np
import os
import time
import shutil

joystick_button_type_dict={
'[0 0 0 0 0 0 0 0 0 0 0]': 'back_click',
'[1 0 0 0 0 0 0 0 0 0 0]': 'escooter',
'[0 0 1 0 0 0 0 0 0 0 0]': 'bike',
'[0 1 0 0 0 0 0 0 0 0 0]': 'pedestrian',
'[0 0 0 1 0 0 0 0 0 0 0]': 'interesting',
'[0 0 0 0 1 0 0 0 0 0 0]': 'can_ignore'
}

def read_folder_list_from_text_file(folder_list_file):
	with open(folder_list_file, 'r') as file:
		folders = file.readlines()
		folders = [f.strip() for f in folders]
	return folders

def convert_click(click_file_dir):
	with open(click_file_dir) as f:
		contents = f.readlines()
	timestamp = []
	buttons = []
	direction_b = []
#   print(contents)
	for i in range(0,len(contents),9):
		timestamp.append(int(contents[i+3].split(':')[-1]))
		buttons.append(eval(contents[i+7].split(':')[-1]))
		direction_b.append((contents[i+6].split(':')[-1]))
	#print(contents[i+3])

	buttons =np.asarray(buttons)
	direction_b = np.asarray(direction_b)

	df_click = pd.DataFrame()
	df_click['click_timestamp'] = timestamp
	df_click['click_timestamp_readable']=[str(datetime.datetime.fromtimestamp(i)) for i in timestamp]
	df_click['button']=list(buttons)
	types=[]
	for i in df_click.button:
		types.append(joystick_button_type_dict.get(str(i),'unknown click'))
	df_click['button_type']=types
#   print(df_click)
	return df_click


def add_frames(f_click, p):
	f_click['frame_start_time'] = f_click['click_timestamp'] - p
	f_click['frame_end_time'] = f_click['click_timestamp'] + p
	f_click['frame_start_time_readable'] = [datetime.datetime.fromtimestamp(i) for i in f_click['frame_start_time']]
	f_click['frame_end_time_readable'] = [datetime.datetime.fromtimestamp(i) for i in f_click['frame_end_time']]
	return f_click

def add_scenario(f_click):
	scenario_number = 1
	f_click['scenario'] = 0
	n = len(f_click)
	for i in range(1, n):
		if f_click.iloc[i]['frame_start_time'] >= f_click.iloc[i-1]['frame_end_time']:
			scenario_number += 1
		f_click.at[i, 'scenario'] = scenario_number
	return f_click

def generate_scenario_summary(df):
	scenario_summary = df.groupby('scenario').agg(
		start_time=('frame_start_time', 'min'),
		end_time=('frame_end_time', 'max'),
		start_time_readable=('frame_start_time_readable','min'),
		end_time_readable=('frame_end_time_readable','max'),
		escooter_clicks=('button_type', lambda x: (x == 'escooter').sum()),
		bike_clicks=('button_type', lambda x: (x == 'bike').sum()),
		pedestrian_clicks=('button_type', lambda x: (x == 'pedestrian').sum())
	).reset_index()
	return scenario_summary


def create_scenarios(input_file, videostart, folder_name, local_path_to_save):
	df_click = convert_click(input_file)
	frame_periods = [20, 10, 5, 7]
	period_wise_summary = {}
	for i, period in enumerate(frame_periods, start=1):
		df_click_period = add_frames(df_click.copy(), period)
		df_click_period = add_scenario(df_click_period)
		df_click_period = df_click_period[(df_click_period['button_type'] != 'back_click') &
										(df_click_period['button_type'] != 'can_ignore') &
									   (df_click_period['button_type'] != 'interesting') &
									   (df_click_period['button_type'] != 'unknown click')]
		df_new = generate_scenario_summary(df_click_period)
		df_new['duration(s)'] = df_new['end_time'] - df_new['start_time']
		df_new['video_start_time (s)'] = df_new['start_time'] - videostart
		df_new['video_end_time (s)'] = df_new['end_time'] - videostart
		df_new['folder'] = folder_name
		output_folder = os.path.join(local_path_to_save, folder_name)
		os.makedirs(output_folder, exist_ok=True)

	# Save dataframe to CSV
		df_new.to_csv(f'{output_folder}/joystick_clicks_period_{period}.csv', index=False)

		period_wise_summary[period] = {}
		period_wise_summary[period]['Number of scenarios'] = df_click_period['scenario'].nunique()
		period_wise_summary[period]['Number of ESCOOTER clicks'] = len(df_click_period[df_click_period['button_type'] == 'escooter'])
		period_wise_summary[period]['Number of BIKE clicks'] = len(df_click_period[df_click_period['button_type'] == 'bike'])
		period_wise_summary[period]['Number of PEDESTRIAN clicks'] = len(df_click_period[df_click_period['button_type'] == 'pedestrian'])
		period_wise_summary[period]['Total Duration'] = sum(df_new['duration(s)'])

	print("Scenarios created for folder {}".format(folder_name))
	return period_wise_summary

def get_starting_timestamps(filename):
	starting_timestamp = None
	# Read timestamps from the file
	with open(filename, 'r') as file:
		starting_timestamp = int(file.readline().strip())
	# Corrected conversion to milliseconds (avoiding datetime)
	starting_timestamp_secs = starting_timestamp / 1000000000
	return starting_timestamp_secs

def get_earliest_camera_timestamps(timestamp_folder):

	earliest_starting_timestamp = None
	if os.path.isdir(timestamp_folder):
		# print(f"Processing folder {timestamp_folder}")
		for timestamp_file in os.listdir(timestamp_folder):
			filename = os.path.join(timestamp_folder, timestamp_file)
			if filename.endswith(".txt"):
				try:
					starting_timestamp_for_cam = get_starting_timestamps(filename)
					if not earliest_starting_timestamp or starting_timestamp_for_cam < earliest_starting_timestamp:
						earliest_starting_timestamp = starting_timestamp_for_cam
					
				except ValueError as e:
					print(f"Error processing file {filename}: {e}")
	return earliest_starting_timestamp

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

	period_wise_total_summary = {}
	start_time = time.time()

	for subfolder in os.listdir(root_folder):
		if subfolder.strip() not in folders_to_process:
			continue
		if subfolder in processed_subfolders_with_error:
			print(f"Subfolder {subfolder} already processed with error. Skipping...")
			continue
		if subfolder in processed_subfolders:
			print(f"Subfolder {subfolder} already processed. Skipping...")
			continue
		print(f"Processing subfolder {subfolder}")
		# try:
		subfolder_path = os.path.join(root_folder, subfolder)
		joystick_file_path = os.path.join(subfolder_path, "joystick", subfolder+".txt")

		if not os.path.exists(joystick_file_path):
			print(f"Joystick file not found for subfolder {subfolder}. Skipping...")
			continue
		timestamp_folder_path = os.path.join(subfolder_path, "processed", "timestamps")
		video_timestamp = get_earliest_camera_timestamps(timestamp_folder_path)

		period_wise_summary_for_folder = create_scenarios(joystick_file_path, video_timestamp, subfolder, local_path)
		for period, summary in period_wise_summary_for_folder.items():
			if period not in period_wise_total_summary:
				period_wise_total_summary[period] = {}
				period_wise_total_summary[period]['Number of scenarios'] = 0
				period_wise_total_summary[period]['Number of ESCOOTER clicks'] = 0
				period_wise_total_summary[period]['Number of BIKE clicks'] = 0
				period_wise_total_summary[period]['Number of PEDESTRIAN clicks'] = 0
				period_wise_total_summary[period]['Total Duration(s)'] = 0
				period_wise_total_summary[period]['Total Duration(min)'] = period_wise_total_summary[period]['Total Duration(s)']/60
			period_wise_total_summary[period]['Number of scenarios'] += summary['Number of scenarios']
			period_wise_total_summary[period]['Number of ESCOOTER clicks'] += summary['Number of ESCOOTER clicks']
			period_wise_total_summary[period]['Number of BIKE clicks'] += summary['Number of BIKE clicks']
			period_wise_total_summary[period]['Number of PEDESTRIAN clicks'] += summary['Number of PEDESTRIAN clicks']
			period_wise_total_summary[period]['Total Duration(s)'] += summary['Total Duration']
			period_wise_total_summary[period]['Total Duration(min)'] = period_wise_total_summary[period]['Total Duration(s)']/60
		
		for period, summary in period_wise_total_summary.items():
			df = pd.DataFrame(summary, index=[0])
			if os.path.exists("scenario_creation_summary_{period}.csv"):
				df.to_csv(f"{local_path}/scenario_creation_summary_{period}.csv", mode='a', header=False, index=False)
			else:
				df.to_csv(f"{local_path}/scenario_creation_summary_{period}.csv", index=False)
	
		#Delete the local lidar and timestamp folders
		# shutil.rmtree(subfolder_new_local_path)
		if os.path.exists(path_to_processed_subfolders):
			with open(path_to_processed_subfolders, "a") as file:
				file.write(subfolder + "\n")
		else:
			with open(path_to_processed_subfolders, "w") as file:
				file.write(subfolder + "\n")
			
		# except Exception as e:
		# 	print(f"Error processing subfolder {subfolder_path}: {e}")
		# 	#Remove the extracted lidar folders
		# 	# shutil.rmtree(subfolder_new_local_path, ignore_errors=True)
		# 	if os.path.exists(path_to_processed_subfolders_with_error):
		# 		with open(path_to_processed_subfolders_with_error, "a") as file:
		# 			file.write(subfolder + "\n")
		# 	else:
		# 		with open(path_to_processed_subfolders_with_error, "w") as file:
		# 			file.write(subfolder + "\n")
	print(f"Processing took {round((time.time() - start_time)/60)} minutes")

# Example usage
source_raw_dath_path = "/mnt/tasismb/Reordered_drive/Raw_Data" 
local_dest_raw_data_path = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/click_based_scenarios"

path_to_folders_to_process = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/scenario_creation_folders.txt"
path_to_processed_subfolders = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/scenario_creation_processed_subfolders.txt"
path_to_processed_subfolders_with_error = "/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/scenario_creation_processed_subfolders_with_error.txt"


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
