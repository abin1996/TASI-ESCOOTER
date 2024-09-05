import os
import pandas as pd
import shutil
import time

# Hardcoded folder paths
base_folder_path = '/home/dp75@ads.iu.edu/TASI/Working/1FPS_Testing/Data'
backup_folder_path = '/home/dp75@ads.iu.edu/TASI/Working/1FPS_Testing/Backup1'
summary_csv_path = '/home/dp75@ads.iu.edu/TASI/Working/1FPS_Testing/summary.csv'

# Function to process each subfolder
def process_subfolder(subfolder_path, summary):
    subfolder_name = os.path.basename(subfolder_path)
    print(f"Processing subfolder: {subfolder_name}")
    start_time = time.time()

    # Read the 'sync_sce.csv' file
    sync_sce_csv_path = os.path.join(subfolder_path, 'sync_sce.csv')
    if not os.path.exists(sync_sce_csv_path):
        print(f"Error: 'sync_sce.csv' not found in {subfolder_path}")
        return

    df = pd.read_csv(sync_sce_csv_path, usecols=['images1', 'images2', 'images3', 'images4', 'images5', 'images6', 'lidar'])
    original_num_rows = df.shape[0]

    # Select every 10th row
    df_1fps = df.iloc[::10]
    num_rows = df_1fps.shape[0]

    # Create '1FPS' folder in the backup location
    fps_backup_folder_path = os.path.join(backup_folder_path, os.path.relpath(subfolder_path, base_folder_path), '1FPS')
    if os.path.exists(fps_backup_folder_path):
        shutil.rmtree(fps_backup_folder_path)
    os.makedirs(fps_backup_folder_path)

    # Save the new CSV in the '1FPS' folder in the backup location
    new_csv_path = os.path.join(fps_backup_folder_path, 'sync_sce_1fps.csv')
    df_1fps.to_csv(new_csv_path, index=False)

    # Copy the files based on the new CSV
    for column in df_1fps.columns:
        col_folder_path = os.path.join(fps_backup_folder_path, column)
        os.makedirs(col_folder_path)

        for file_name in df_1fps[column].dropna():
            src_file_path = os.path.join(subfolder_path, column, file_name)
            dest_file_path = os.path.join(col_folder_path, file_name)

            if os.path.exists(src_file_path):
                shutil.copy(src_file_path, dest_file_path)
            else:
                print(f"Error: {src_file_path} not found")

    # Copy the 'calibration_matrix.json' file
    calibration_matrix_path = os.path.join(subfolder_path, 'Calibration_matrix.json')
    if os.path.exists(calibration_matrix_path):
        shutil.copy(calibration_matrix_path, os.path.join(fps_backup_folder_path, 'Calibration_matrix.json'))
    else:
        print(f"Error: 'calibration_matrix.json' not found in {subfolder_path}")

    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken for subfolder {subfolder_name}: {time_taken} seconds")
    
    # Update summary
    summary.append({
        'Parent Folder': os.path.basename(os.path.dirname(subfolder_path)),
        'Subfolder Name': subfolder_name,
        'Original Num Rows': original_num_rows,
        'Num Frames': num_rows,
        'Time Taken (seconds)': time_taken
    })

# Function to process each parent folder
def process_parent_folder(parent_folder_path, summary):
    print(f"Processing parent folder: {parent_folder_path}")
    start_time = time.time()
    parent_folder_name = os.path.basename(parent_folder_path)

    subfolders = [f.path for f in os.scandir(parent_folder_path) if f.is_dir()]
    for subfolder_path in subfolders:
        process_subfolder(subfolder_path, summary)

    end_time = time.time()
    time_taken = end_time - start_time
    print(f"Time taken for parent folder {parent_folder_path}: {time_taken / 60} minutes")

    # Update parent folder summary
    parent_summary = {
        'Parent Folder': parent_folder_name,
        'Total Original Rows': sum(item['Original Num Rows'] for item in summary if item['Parent Folder'] == parent_folder_name and 'Subfolder Name' in item),
        'Total Frames': sum(item['Num Frames'] for item in summary if item['Parent Folder'] == parent_folder_name and 'Subfolder Name' in item),
        'Total Time Taken (seconds)': sum(item['Time Taken (seconds)'] for item in summary if item['Parent Folder'] == parent_folder_name and 'Subfolder Name' in item)
    }
    summary.append(parent_summary)

# Main processing loop
def main():
    start_time = time.time()
    summary = []

    parent_folders = sorted([f.path for f in os.scandir(base_folder_path) if f.is_dir()])
    for parent_folder_path in parent_folders:
        process_parent_folder(parent_folder_path, summary)

    end_time = time.time()
    total_time_taken = end_time - start_time
    total_original_rows = sum(item['Original Num Rows'] for item in summary if 'Subfolder Name' in item)
    total_frames = sum(item['Num Frames'] for item in summary if 'Subfolder Name' in item)
    
    # Final summary
    summary.append({
        'Parent Folder': 'Grand Total',
        'Total Original Rows': total_original_rows,
        'Total Frames': total_frames,
        'Total Time Taken (seconds)': total_time_taken
    })

    # Save the summary CSV
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(summary_csv_path, index=False)
    print(f"Summary saved to {summary_csv_path}")

    print(f"Total time taken: {total_time_taken / 60} minutes")

if __name__ == "__main__":
    main()
