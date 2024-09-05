import csv
import numpy as np
import open3d as o3d
import os
import shutil
import time

def extract_radar_positions(csv_file):
    positions = []
    timestamps = []

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        # Skip the first row
        next(reader)
        for row in reader:
            timestamp = row[0]
            radar_info = row[1]
            
            if radar_info.strip():  # Check if radar_info is not empty
                # Extract position information using string operations
                try:
                    start_index = 0
                    while True:
                        start_index = radar_info.find('position', start_index)
                        if start_index == -1:
                            break
                        end_index = radar_info.find('orientation', start_index)
                        position_info = radar_info[start_index:end_index].strip()
                        
                        # Parse position information
                        # Extract x, y, z values
                        x_str = position_info.split('y:')[0].strip().split('x:')[1].strip().strip(',')
                        y_str = position_info.split('z:')[0].strip().split('y:')[1].strip().strip(',')
                        z_str = position_info.split('z:')[1].strip().strip(',')
                        
                        # Convert to floats
                        x = float(x_str)
                        y = float(y_str)
                        z = float(z_str)

                        positions.append([timestamp, x, y, z])
                        start_index = end_index
                except ValueError as e:
                    print(f"Failed to parse position data at timestamp {timestamp}: {e}")
            else:
                print(f"Empty radar_info at timestamp {timestamp}")
    
    positions_array = np.array(positions)
    return positions_array

def save_pcd_files(positions_array, output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    unique_timestamps = np.unique(positions_array[:, 0])
    
    for timestamp in unique_timestamps:
        points = positions_array[positions_array[:, 0] == timestamp][:, 1:].astype(np.float32)
        
        # Print the numpy array for the current timestamp
        #print(f"Timestamp: {timestamp}")
        #print(points)
        
        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = o3d.utility.Vector3dVector(points)
        
        pcd_filename = os.path.join(output_dir, f"radar_{timestamp}.pcd")
        o3d.io.write_point_cloud(pcd_filename, point_cloud)
        #print(f"Saved {pcd_filename}")

def process_folders(root_folder):
    start_time = time.time()
    parent_folders = [folder for folder in os.listdir(root_folder) if folder != 'logs' and os.path.isdir(os.path.join(root_folder, folder))]
    
    for idx, parent_folder in enumerate(parent_folders, start=1):
        parent_folder_path = os.path.join(root_folder, parent_folder)
        folder_start_time = time.time()
        
        print(f"Processing parent folder {idx}/{len(parent_folders)}: {parent_folder}")
        
        pcd_files_count = 0
        radar_csv_files_count = 0
        expected_file_count = 0
        
        for subfolder in os.listdir(parent_folder_path):
            subfolder_path = os.path.join(parent_folder_path, subfolder)
            if os.path.isdir(subfolder_path):
                radar_objects_folder = os.path.join(subfolder_path, "1FPS", "radar_objects")
                radar_csv = os.path.join(radar_objects_folder, "radar_objects.csv")
                
                if os.path.exists(radar_csv):
                    radar_csv_files_count += 1
                    radar_pcd_folder = os.path.join(subfolder_path, "1FPS", "radar_pcd")
                    #print(f"Processing {radar_csv}")
                    positions_array = extract_radar_positions(radar_csv)
                    save_pcd_files(positions_array, radar_pcd_folder)
                    pcd_files_count += len(np.unique(positions_array[:, 0]))

                    # Count files in front_left, front_right, and point_cloud
                    front_left_count = len(os.listdir(os.path.join(subfolder_path, "1FPS", "front_left")))
                    front_right_count = len(os.listdir(os.path.join(subfolder_path, "1FPS", "front_right")))
                    point_cloud_count = len(os.listdir(os.path.join(subfolder_path, "1FPS", "point_cloud")))
                    expected_file_count += (front_left_count + front_right_count + point_cloud_count) // 3
                
                else:
                    print(f"Error: radar_objects.csv not found in {radar_objects_folder}")
        
        folder_elapsed_time = time.time() - folder_start_time
        print(f"Finished processing parent folder {idx}/{len(parent_folders)}: {parent_folder}")
        print(f"Time taken: {folder_elapsed_time:.2f} seconds")
        print(f"Generated PCD files: {pcd_files_count}, Expected PCD files: {expected_file_count}")
        if pcd_files_count != expected_file_count:
            print(f"Error: Number of generated PCD files does not match the expected count in {parent_folder}")

    total_elapsed_time = time.time() - start_time
    print(f"Total elapsed time: {total_elapsed_time:.2f} seconds")

# Example usage
root_folder = '/media/dp75/TASI-ESC-BKCP/Extracted_Object_Based_Scenarios_2024'
#root_folder = '/home/dp75@ads.iu.edu/TASI/Working/1FPS_Testing/for_new_data'
process_folders(root_folder)