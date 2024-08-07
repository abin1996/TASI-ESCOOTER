import os
import csv
import zipfile
import time
from datetime import timedelta

# Hardcoded paths
BASE_PATH = '/path/to/your/base/folder'  # Replace with the actual path to your base folder
DESTINATION_PATH = '/path/to/save/zipped/folders'  # Replace with the actual path to save the zipped folders

REQUIRED_ITEMS = {'folders': ['images1', 'images2', 'images3', 'images4', 'images5', 'images6', 'lidar'],
                  'files': ['Calibration_matrix.json', 'sensor_data_mapping.csv']}

def count_csv_rows(file_path):
    try:
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            rows = list(reader)
            return len(rows) - 1  # Exclude header row
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

def check_folder_structure(subfolder_path):
    fps_folder_path = os.path.join(subfolder_path, "1FPS")
    if not os.path.exists(fps_folder_path):
        return False, "1FPS folder missing"
    
    items_in_fps = os.listdir(fps_folder_path)
    folders_present = [f for f in items_in_fps if os.path.isdir(os.path.join(fps_folder_path, f))]
    files_present = [f for f in items_in_fps if os.path.isfile(os.path.join(fps_folder_path, f))]
    
    missing_folders = set(REQUIRED_ITEMS['folders']) - set(folders_present)
    missing_files = set(REQUIRED_ITEMS['files']) - set(files_present)
    
    if missing_folders or missing_files:
        return False, f"Missing folders: {missing_folders}, Missing files: {missing_files}"
    
    # Check number of items in folders and compare with CSV row count
    sensor_data_csv_path = os.path.join(fps_folder_path, 'sensor_data_mapping.csv')
    if not os.path.isfile(sensor_data_csv_path):
        return False, "sensor_data_mapping.csv missing"
    
    row_count = count_csv_rows(sensor_data_csv_path)
    
    for folder in REQUIRED_ITEMS['folders']:
        folder_path = os.path.join(fps_folder_path, folder)
        items_in_folder = os.listdir(folder_path)
        if len(items_in_folder) != row_count:
            return False, f"Mismatch in item count for folder {folder}"
    
    return True, "All checks passed"

def zip_folder(parent_folder_path, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(parent_folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, parent_folder_path))

def process_folders(base_path, destination_path):
    parent_folders = sorted(os.listdir(base_path))
    issues = []
    total_folders_zipped = 0
    total_start_time = time.time()
    
    # Check all parent folders first
    for parent_folder in parent_folders:
        parent_folder_path = os.path.join(base_path, parent_folder)
        if os.path.isdir(parent_folder_path):
            parent_has_issues = False
            
            subfolders = os.listdir(parent_folder_path)
            for subfolder in subfolders:
                subfolder_path = os.path.join(parent_folder_path, subfolder)
                if os.path.isdir(subfolder_path):
                    status, message = check_folder_structure(subfolder_path)
                    if not status:
                        issues.append((parent_folder, subfolder, message))
                        parent_has_issues = True
            
            # Print progress for parent folder
            print(f"Checked {parent_folder}")
    
    # Show findings
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"Parent folder: {issue[0]}, Subfolder: {issue[1]}, Issue: {issue[2]}")
    
    # Ask user if they want to zip the folders
    while True:
        user_input = input("Do you want to zip the folders? (Y/N): ")
        if user_input.lower() == 'y':
            # Zip each parent folder
            for parent_folder in parent_folders:
                parent_folder_path = os.path.join(base_path, parent_folder)
                if os.path.isdir(parent_folder_path):
                    zip_start_time = time.time()
                    zip_file_path = os.path.join(destination_path, f"{parent_folder}.zip")
                    zip_folder(parent_folder_path, zip_file_path)
                    zip_end_time = time.time()
                    zip_duration = zip_end_time - zip_start_time
                    print(f"Zipped {parent_folder} in {str(timedelta(seconds=zip_duration))}")
                    total_folders_zipped += 1
            break
        elif user_input.lower() == 'n':
            print("Process terminated.")
            break
        else:
            print("Invalid input. Please enter 'Y' or 'N'.")
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    print(f"Total processing time: {str(timedelta(seconds=total_duration))}")
    print(f"Total folders zipped: {total_folders_zipped}")

# Process the folders
process_folders(BASE_PATH, DESTINATION_PATH)
