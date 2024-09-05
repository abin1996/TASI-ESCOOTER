import os
import csv

# Hardcoded paths
BASE_PATH = '/media/dp75/TASI-ESC-BKCP/1FPS_error_corrected_backup_iMerit'  # Replace with the actual path to your base folder

REQUIRED_FOLDERS = ['images1', 'images2', 'images3', 'images4', 'images5', 'images6', 'lidar']
REQUIRED_FILES = ['Calibration_matrix.json', 'sensor_data_mapping.csv']

def check_folder_structure(subfolder_path):
    fps_folder_path = os.path.join(subfolder_path, "1FPS")
    if not os.path.exists(fps_folder_path):
        return False, "1FPS folder missing", {}
    
    items_in_fps = os.listdir(fps_folder_path)
    folders_present = [f for f in items_in_fps if os.path.isdir(os.path.join(fps_folder_path, f))]
    files_present = [f for f in items_in_fps if os.path.isfile(os.path.join(fps_folder_path, f))]
    
    missing_folders = set(REQUIRED_FOLDERS) - set(folders_present)
    missing_files = set(REQUIRED_FILES) - set(files_present)
    
    if missing_folders or missing_files:
        return False, f"Missing folders: {missing_folders}, Missing files: {missing_files}", {}

    # Check number of items in folders
    folder_item_counts = {}
    item_counts_set = set()
    for folder in REQUIRED_FOLDERS:
        folder_path = os.path.join(fps_folder_path, folder)
        items_in_folder = os.listdir(folder_path)
        folder_item_counts[folder] = len(items_in_folder)
        item_counts_set.add(len(items_in_folder))
    
    if len(item_counts_set) > 1:
        return False, "Item count mismatch between folders", folder_item_counts
    
    return True, "All checks passed", folder_item_counts

def process_folders(base_path):
    parent_folders = sorted(os.listdir(base_path))
    healthy_folders = []
    unhealthy_folders = []
    healthy_index = 0
    unhealthy_index = 0
    
    for parent_folder in parent_folders:
        parent_folder_path = os.path.join(base_path, parent_folder)
        if os.path.isdir(parent_folder_path):
            parent_healthy = True
            subfolder_issues = []
            
            subfolders = os.listdir(parent_folder_path)
            for subfolder in subfolders:
                subfolder_path = os.path.join(parent_folder_path, subfolder)
                if os.path.isdir(subfolder_path):
                    status, message, folder_item_counts = check_folder_structure(subfolder_path)
                    if not status:
                        parent_healthy = False
                        subfolder_issues.append((subfolder, message, folder_item_counts))
            
            if parent_healthy:
                healthy_index += 1
                healthy_folders.append((healthy_index, parent_folder))
            else:
                unhealthy_index += 1
                unhealthy_folders.append((unhealthy_index, parent_folder, subfolder_issues))
    
    # Print healthy parent folders
    print("\nHealthy Parent Folders:")
    for index, folder in healthy_folders:
        print(f"{index}. {folder}")
    
    # Print unhealthy parent folders and subfolders with details
    print("\nUnhealthy Parent Folders and Subfolders:")
    for index, parent_folder, subfolder_issues in unhealthy_folders:
        print(f"\n{index}. {parent_folder}")
        for subfolder, message, folder_item_counts in subfolder_issues:
            print(f"  Subfolder: {subfolder}, Issue: {message}")
            item_counts = ', '.join(f"{folder}: {count} items" for folder, count in folder_item_counts.items())
            print(f"    {item_counts}")

# Process the folders
process_folders(BASE_PATH)
