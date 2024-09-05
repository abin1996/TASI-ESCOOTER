import csv
import numpy as np
import open3d as o3d
import os

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
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    unique_timestamps = np.unique(positions_array[:, 0])
    
    for timestamp in unique_timestamps:
        points = positions_array[positions_array[:, 0] == timestamp][:, 1:].astype(np.float32)
        
        # Print the numpy array for the current timestamp
        print(f"Timestamp: {timestamp}")
        print(points)
        
        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = o3d.utility.Vector3dVector(points)
        
        pcd_filename = os.path.join(output_dir, f"radar_{timestamp}.pcd")
        o3d.io.write_point_cloud(pcd_filename, point_cloud)
        print(f"Saved {pcd_filename}")

# Example usage
# csv_file = '/Users/wangshaozhi/Desktop/shaozhi/Purdue/e-scooter/Sample Data 2024-06-03_16-06-37/2024-06-03_16-06-37_2_1717445599_1717445615/1FPS/radar_objects/radar_objects.csv'
# output_dir = '/Users/wangshaozhi/Desktop/shaozhi/Purdue/e-scooter/Sample Data 2024-06-03_16-06-37/2024-06-03_16-06-37_2_1717445599_1717445615/1FPS/radar_pcd'
csv_file = 'Sample Data 2024-06-03_16-06-37/2024-06-03_16-06-37_1_1717445541_1717445551/1FPS/radar_objects/radar_objects.csv'
output_dir = 'Sample Data 2024-06-03_16-06-37/2024-06-03_16-06-37_1_1717445541_1717445551/1FPS/radar_pcd'


positions_array = extract_radar_positions(csv_file)
save_pcd_files(positions_array, output_dir)
