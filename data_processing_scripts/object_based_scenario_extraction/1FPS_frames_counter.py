import os
import csv
import pandas as pd

# Hardcoded paths
BASE_PATH = '/path/to/your/base/folder'  # Replace with the actual path to your base folder
OUTPUT_CSV_PATH = '/path/to/save/new_data_frame_summary.csv'  # Replace with the actual path to save the CSV file

def count_csv_rows(file_path):
    try:
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            rows = list(reader)
            return len(rows) - 1  # Exclude header row
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

def process_folders(base_path):
    summary_data = []
    grand_total_frames = 0
    grand_total_duration_sec = 0
    
    parent_folders = sorted(os.listdir(base_path))
    for parent_folder in parent_folders:
        parent_folder_path = os.path.join(base_path, parent_folder)
        if os.path.isdir(parent_folder_path):
            parent_total_frames = 0
            parent_total_duration_sec = 0
            
            subfolders = os.listdir(parent_folder_path)
            for subfolder in subfolders:
                subfolder_path = os.path.join(parent_folder_path, subfolder)
                if os.path.isdir(subfolder_path):
                    fps_folder_path = os.path.join(subfolder_path, "1 FPS")
                    if os.path.isdir(fps_folder_path):
                        csv_file_path = os.path.join(fps_folder_path, "synced_sensor_timestamps_1FPS.csv")
                        if os.path.isfile(csv_file_path):
                            frames = count_csv_rows(csv_file_path)
                            duration_sec = frames
                            
                            summary_data.append([parent_folder, subfolder, frames, duration_sec])
                            parent_total_frames += frames
                            parent_total_duration_sec += duration_sec
                            
            # Append parent folder total
            summary_data.append([parent_folder, "Total", parent_total_frames, parent_total_duration_sec, parent_total_duration_sec / 60])
            grand_total_frames += parent_total_frames
            grand_total_duration_sec += parent_total_duration_sec
            
            # Print progress for parent folder
            print(f"Processed {parent_folder}: {parent_total_frames} frames, {parent_total_duration_sec} seconds")
            print(f"Cumulative Total: {grand_total_frames} frames, {grand_total_duration_sec} seconds")
    
    # Append grand total
    summary_data.append(["Grand Total", "", grand_total_frames, grand_total_duration_sec, grand_total_duration_sec / 60, grand_total_duration_sec / 3600])
    
    # Save to CSV
    summary_df = pd.DataFrame(summary_data, columns=["Parent Folder", "Subfolder", "Frames", "Duration (sec)", "Duration (min)", "Duration (hours)"])
    summary_df.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"Processing complete. Summary saved to {OUTPUT_CSV_PATH}")

# Process the folders
process_folders(BASE_PATH)
