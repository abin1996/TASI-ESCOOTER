import os
import pandas as pd
import shutil
import time

# Hardcoded folder paths
base_folder_path = '/Users/IUPUI/TASI/Test_data'
backup_folder_path = '/Users/IUPUI/TASI/Backup'

# Function to process each subfolder
def process_subfolder(subfolder_path, subfolder_index):
    print(f"Processing subfolder index: {subfolder_index+1}")
    start_time = time.time()
    
    # Check and delete '1FPS' folder if it exists
    fps_folder_path = os.path.join(subfolder_path, '1FPS')
    if os.path.exists(fps_folder_path):
        shutil.rmtree(fps_folder_path)
    
    # Create '1FPS' folder
    os.makedirs(fps_folder_path)
    
    # Read the 'sync_sce.csv' file
    sync_sce_csv_path = os.path.join(subfolder_path, 'sync_sce.csv')
    if not os.path.exists(sync_sce_csv_path):
        print(f"Error: 'sync_sce.csv' not found in {subfolder_path}")
        return

    df = pd.read_csv(sync_sce_csv_path, usecols=['images1', 'images2', 'images3', 'images4', 'images5', 'images6', 'lidar'])
    
    # Select every 10th row
    df_1fps = df.iloc[::10]
    
    # Save the new CSV in the '1FPS' folder
    new_csv_path = os.path.join(fps_folder_path, 'sync_sce_1fps.csv')
    df_1fps.to_csv(new_csv_path, index=False)
    
    # Copy the files based on the new CSV
    for column in df_1fps.columns:
        col_folder_path = os.path.join(fps_folder_path, column)
        os.makedirs(col_folder_path)
        
        for file_name in df_1fps[column].dropna():
            src_file_path = os.path.join(subfolder_path, column, file_name)
            dest_file_path = os.path.join(col_folder_path, file_name)
            
            if os.path.exists(src_file_path):
                shutil.copy(src_file_path, dest_file_path)
            else:
                print(f"Error: {src_file_path} not found")
    
    # Backup the '1FPS' folder
    backup_subfolder_path = os.path.join(backup_folder_path, os.path.relpath(subfolder_path, base_folder_path))
    backup_fps_folder_path = os.path.join(backup_subfolder_path, '1FPS')
    
    if not os.path.exists(backup_subfolder_path):
        os.makedirs(backup_subfolder_path)
    
    shutil.copytree(fps_folder_path, backup_fps_folder_path)
    
    end_time = time.time()
    print(f"Time taken for subfolder index {subfolder_index+1}: {end_time - start_time} seconds")


# Function to process each parent folder
def process_parent_folder(parent_folder_path):
    print(f"Processing parent folder: {parent_folder_path}")
    start_time = time.time()

    subfolders = [f.path for f in os.scandir(parent_folder_path) if f.is_dir()]
    for i, subfolder_path in enumerate(subfolders):
        process_subfolder(subfolder_path, i)

    end_time = time.time()
    print(f"Time taken for parent folder {parent_folder_path}: {(end_time - start_time)/60} minutes")


# Main processing loop
def main():
    start_time = time.time()
    
    parent_folders = [f.path for f in os.scandir(base_folder_path) if f.is_dir()]
    for parent_folder_path in parent_folders:
        process_parent_folder(parent_folder_path)
    
    end_time = time.time()
    print(f"Total time taken: {(end_time - start_time)/60} minutes")


if __name__ == "__main__":
    main()
