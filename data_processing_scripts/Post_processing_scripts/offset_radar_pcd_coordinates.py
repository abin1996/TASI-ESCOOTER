import os
import glob
import time
import numpy as np
import open3d as o3d

# Offset to be added to the coordinates
OFFSET = np.array([2.98, 0, -0.66])

def process_pcd_file(file_path):
    # Read the PCD file using Open3D
    pcd = o3d.io.read_point_cloud(file_path)
    
    # Convert to numpy array
    points = np.asarray(pcd.points)
    
    # Add offset
    points += OFFSET
    
    # Update the point cloud with new coordinates
    pcd.points = o3d.utility.Vector3dVector(points)
    
    # Save the updated PCD file
    o3d.io.write_point_cloud(file_path, pcd)

def process_radar_pcd_folder(radar_pcd_folder):
    # Process each PCD file in the radar_pcd folder
    pcd_files = glob.glob(os.path.join(radar_pcd_folder, '*.pcd'))
    
    for pcd_file in pcd_files:
        process_pcd_file(pcd_file)

def process_1fps_folder(parent_folder, index):
    start_time = time.time()
    
    # Iterate through all subfolders in the parent folder
    subfolders = glob.glob(os.path.join(parent_folder, '*/1FPS'))
    for subfolder in subfolders:
        radar_pcd_folders = glob.glob(os.path.join(subfolder, '*/radar_pcd'))
        for radar_pcd_folder in radar_pcd_folders:
            process_radar_pcd_folder(radar_pcd_folder)
    
    elapsed_time = time.time() - start_time
    print(f'Parent folder processed: {parent_folder} in {elapsed_time:.2f} seconds')
    return elapsed_time

def main(root_folder):
    index = 0
    for parent_folder in glob.glob(os.path.join(root_folder, '*/')):
        # Process each parent folder and keep track of the index
        index += 1
        process_1fps_folder(parent_folder, index)

    print(f'Total folders processed: {index}')

if __name__ == "__main__":
    # Replace with the path to your root folder
    root_folder = '/media/pate2372/DA 21/Work_temp/Input'
    main(root_folder)