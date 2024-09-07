import os
import numpy as np
import open3d as o3d
import time

# Offset to be added to the coordinates
OFFSET = np.array([2.98, 0, -0.66])

def process_pcd_file(file_path):
    """Process a single PCD file: load, apply offset, and save."""
    # Load the PCD file
    pcd = o3d.io.read_point_cloud(file_path)
    
    # Check if the point cloud is valid
    if not pcd.has_points():
        print(f'Error: The point cloud file {file_path} does not contain any points.')
        return
    
    # Convert to numpy array
    points = np.asarray(pcd.points)
    
    # Apply the offset
    points += OFFSET
    
    # Update the point cloud with new coordinates
    pcd.points = o3d.utility.Vector3dVector(points)
    
    # Save the updated PCD file
    o3d.io.write_point_cloud(file_path, pcd)

def process_radar_pcd_folder(radar_pcd_folder):
    """Process all PCD files in a radar_pcd folder."""
    #print(f'Searching for PCD files in folder: {radar_pcd_folder}')
    pcd_files = [f for f in os.listdir(radar_pcd_folder) if f.endswith('.pcd')]
    
    for pcd_file in pcd_files:
        process_pcd_file(os.path.join(radar_pcd_folder, pcd_file))

def process_1fps_folder(parent_folder):
    """Process all radar_pcd folders in a 1FPS folder."""
    start_time = time.time()
    
    print(f'Processing 1FPS folders in parent folder: {parent_folder}')
    
    for subfolder in os.listdir(parent_folder):
        if subfolder == ".DS_store":
            #stupid OS problems
            a = 1
        else:
            subfolder_path = os.path.join(parent_folder, subfolder, '1FPS/radar_pcd')
            process_radar_pcd_folder(subfolder_path)
    
    elapsed_time = time.time() - start_time
    print(f'Parent folder processed: {parent_folder} in {elapsed_time:.2f} seconds')
    return elapsed_time

def main(root_folder):
    """Process all parent folders."""
    index = 0
    
    for parent_folder in os.listdir(root_folder):
        parent_folder_path = os.path.join(root_folder, parent_folder)
        
        if os.path.isdir(parent_folder_path):
            # Process each parent folder
            index += 1
            process_1fps_folder(parent_folder_path)

    print(f'Total folders processed: {index}')


if __name__ == "__main__":
    root_folder = '/Users/Purdue/TASI/work/Input'
    main(root_folder)
