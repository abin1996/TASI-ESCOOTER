import os
from io import open

lidar_folders_file = "/home/abinmath@ads.iu.edu/Documents/TASI-ESCOOTER/folders_to_copy.txt"
lidar_folders_source_path = "/media/abinmath/TASI_ESCOOTER_Drive1/Extracted_Raw_Data"
lidar_folders_raw_data_path = "/mnt/TASI-VRU1/Reordered_drive/Raw_Data"
destination_path = "/mnt/TASI-VRU2/RAW_DATA"
lidar_timestamp_folder = "processed/lidar_timestamps"
lidar_sync_timestamp_folder = "processed/synchronized_timestamps"
lidar_data_processed_folder = "processed/lidar_data"
error_file_log = "/home/abinmath@ads.iu.edu/Documents/TASI-ESCOOTER/copying_error_folders.txt"
success_file_log = "/home/abinmath@ads.iu.edu/Documents/TASI-ESCOOTER/copying_sucess_folders.txt"
def read_folder_list_from_text_file(folder_list_file):
    with open(folder_list_file, 'r') as file:
        folders = file.readlines()
        folders = [f.strip() for f in folders]
    return folders
def save_success_folders_to_file(success_folder, success_file):
    if os.path.exists(success_file):
        with open(success_file, "a") as file:
            file.write(success_folder + "\n")
    else:
        with open(success_file, "w") as file:
            file.write(success_folder + "\n")
    print("Success folders written to file: ", success_file)

def save_error_folders_to_file(error_folder, error_file):
    if os.path.exists(error_file_log):
        with open(error_file_log, "a") as file:
            file.write(error_folder + "\n")
    else:
        with open(error_file_log, "w") as file:
            file.write(error_folder + "\n")
    print("Error folders written to file: ", error_file)

def transfer_lidar_folders(lidar_folders_file, lidar_folders_source_path, lidar_folders_raw_data_path, destination_path, error_file_log="error_folders.txt", success_file_log="success_folders.txt"):
    lidar_folders = read_folder_list_from_text_file(lidar_folders_file)
 
    for folder in lidar_folders:
        try:
            raw_data_folder_path = os.path.join(lidar_folders_raw_data_path, folder)
            source_folder_path = os.path.join(lidar_folders_source_path, folder)
            if not os.path.exists(raw_data_folder_path):
                print("Raw Data Folder does not exist: ", raw_data_folder_path)
                save_error_folders_to_file([folder], error_file_log)
                continue
            if not os.path.exists(source_folder_path):
                print("Extracted Lidar Path does not exist: ", source_folder_path)
                save_error_folders_to_file([folder], error_file_log)
                continue

            print("Transferring folder: ", folder)
            destination_folder_path = os.path.join(destination_path, folder)
            destination_processed_path = os.path.join(destination_folder_path, 'processed')

            raw_data_gps_path = os.path.join(raw_data_folder_path, "gps")
            raw_data_joystick_path = os.path.join(raw_data_folder_path, "joystick")
            raw_data_processed_path = os.path.join(raw_data_folder_path, "processed")
            #Create the destination folder
            os.system("mkdir -p " + destination_folder_path)
            os.system("rsync -avzh --progress " + raw_data_gps_path + " " + destination_folder_path)
            os.system("rsync -avzh --progress " + raw_data_joystick_path + " " + destination_folder_path)
            os.system("rsync -avzh --progress " + raw_data_processed_path + " " + destination_folder_path)
            
            lidar_timestamps = os.path.join(source_folder_path, lidar_timestamp_folder)
            lidar_sync_timestamps = os.path.join(source_folder_path, lidar_sync_timestamp_folder)
            lidar_data = os.path.join(source_folder_path, lidar_data_processed_folder)

            if not os.path.exists(destination_processed_path):
                os.system("mkdir -p " + destination_processed_path)
            #Copy the lidar data into the destination folder processed path
            os.system("rsync -avzh --progress " + lidar_timestamps + " " + destination_processed_path)
            os.system("rsync -avzh --progress " + lidar_sync_timestamps + " " + destination_processed_path)
            os.system("rsync -avzh --progress " + lidar_data + " " + destination_processed_path)
            save_success_folders_to_file(folder, success_file_log)
        except Exception as e:
            print("Error occurred: ", e)
            save_error_folders_to_file(folder, error_file_log)
            
transfer_lidar_folders(lidar_folders_file, lidar_folders_source_path, lidar_folders_raw_data_path, destination_path, error_file_log, success_file_log)