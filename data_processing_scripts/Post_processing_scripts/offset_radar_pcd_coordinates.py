import os
import glob
import time
import numpy as np
import open3d as o3d

# Offset to be added to the coordinates
OFFSET = np.array([2.98, 0, -0.66])

def process_pcd_file(file_path):
    try:
        # Read the PCD file using Open3D
        pcd = o3d.io.read_point_cloud(file_path)
        
        # Check if point cloud has points
        if len(pcd.points) == 0:
            print(f'Warning: The point cloud file {file_path} is empty or corrupted.')
            return
        
        # Convert to numpy array
        points = np.asarray(pcd.points)
        
        # Add offset
        points += OFFSET
        
        # Update the point cloud with new coordinates
        pcd.points = o3d.utility.Vector3dVector(points)
        
        # Save the updated PCD file
        o3d.io.write_point_cloud(file_path, pcd)
        print(f'Successfully processed: {file_path}')
    except Exception as e:
        print(f'Error processing file {file_path}: {e}')

def process_radar_pcd_folder(radar_pcd_folder):
    print(f'Searching for PCD files in folder: {radar_pcd_folder}')
    # Process each PCD file in the radar_pcd folder
    pcd_files = glob.glob(os.path.join(radar_pcd_folder, '*.pcd'))
    
    if not pcd_files:
        print(f'No PCD files found in folder: {radar_pcd_folder}')
    
    for pcd_file in pcd_files:
        process_pcd_file(pcd_file)

def process_1fps_folder(parent_folder, index):
    start_time = time.time()
    
    print(f'Processing 1FPS folders in parent folder: {parent_folder}')
    
    # Iterate through all subfolders in the parent folder
    subfolders = glob.glob(os.path.join(parent_folder, '*/1FPS'))
    
    if not subfolders:
        print(f'No 1FPS folders found in parent folder: {parent_folder}')
    
    for subfolder in subfolders:
        print(f'Checking for radar_pcd folders in 1FPS folder: {subfolder}')
        radar_pcd_folders = glob.glob(os.path.join(subfolder, '*/radar_pcd'))
        
        if not radar_pcd_folders:
            print(f'No radar_pcd folders found in 1FPS folder: {subfolder}')
        
        for radar_pcd_folder in radar_pcd_folders:
            print(f'Processing radar_pcd folder: {radar_pcd_folder}')
            process_radar_pcd_folder(radar_pcd_folder)
    
    elapsed_time = time.time() - start_time
    print(f'Parent folder processed: {parent_folder} in {elapsed_time:.2f} seconds')
    return elapsed_time

def main(root_folder):
    index = 0
    parent_folders = glob.glob(os.path.join(root_folder, '*/'))
    
    if not parent_folders:
        print(f'No main folders found in root folder: {root_folder}')
    
    for parent_folder in parent_folders:
        # Process each parent folder and keep track of the index
        index += 1
        process_1fps_folder(parent_folder, index)

    print(f'Total folders processed: {index}')

if __name__ == "__main__":
    root_folder = '/media/pate2372/DA 21/Work_temp/Input'
    main(root_folder)