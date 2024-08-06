import os
import csv
import pandas as pd

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
                            
                            summary_data.append([subfolder, frames, duration_sec])
                            parent_total_frames += frames
                            parent_total_duration_sec += duration_sec
                            
            # Append parent folder total
            summary_data.append([parent_folder, parent_total_frames, parent_total_duration_sec, parent_total_duration_sec / 60])
            grand_total_frames += parent_total_frames
            grand_total_duration_sec += parent_total_duration_sec
            
            print(f"Processed {parent_folder}: {parent_total_frames} frames, {parent_total_duration_sec} seconds")
    
    # Append grand total
    summary_data.append(["Grand Total", grand_total_frames, grand_total_duration_sec, grand_total_duration_sec / 60, grand_total_duration_sec / 3600])
    
    # Save to CSV
    summary_df = pd.DataFrame(summary_data, columns=["Folder", "Frames", "Duration (sec)", "Duration (min)", "Duration (hours)"])
    summary_df.to_csv(os.path.join(base_path, "new_data_frame_summary.csv"), index=False)
    print("Processing complete. Summary saved to new_data_frame_summary.csv")

# Replace 'your_base_folder_path' with the actual path to your base folder
process_folders('your_base_folder_path')
