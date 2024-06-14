import os
import pandas as pd
def read_folder_list_from_text_file(folder_list_file):
	with open(folder_list_file, 'r') as file:
		folders = file.readlines()
		folders = [f.strip() for f in folders]
	return folders

def check_lidar_location(all_lidar_df, lidar_list1, lidar_list2):
    #Iterate through all_list_df and check if the lidar location is in the lidar_list1 or lidar_list2
    #If it is in list1, then add the value "TASI Network Drive" or if it is in list2, then add the value "Wait_for_quality_drive"
    #If it is not in either list, then add the value "TASI_Escooter_drive1"
    #Add the column 'lidar_location' to the all_lidar_df and return the dataframe

    all_lidar_df['lidar_location'] = ""
    for index, row in all_lidar_df.iterrows():
        if row['Subfolder'] in lidar_list1:
            all_lidar_df.loc[index, 'lidar_location'] = "TASI Network Drive"
        elif row['Subfolder'] in lidar_list2:
            all_lidar_df.loc[index, 'lidar_location'] = "Wait_for_quality_drive"
        else:
            all_lidar_df.loc[index, 'lidar_location'] = "TASI_Escooter_drive1"
    
    return all_lidar_df

all_lidar_df = pd.read_csv('/home/abinmath@ads.iu.edu/TASI-ESCOOTER/synchronized_raw_data_summary.csv')

lidar_list1 = read_folder_list_from_text_file('/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/sync_folders_network_drive.txt')
lidar_list2 = read_folder_list_from_text_file('/home/abinmath@ads.iu.edu/TASI-ESCOOTER/data_processing_scripts/sync_folders_wait_for_quality_drive.txt')

all_lidar_df = check_lidar_location(all_lidar_df, lidar_list1, lidar_list2)
all_lidar_df.to_csv('synced_raw_data_summary_with_lidar_location.csv', index=False)