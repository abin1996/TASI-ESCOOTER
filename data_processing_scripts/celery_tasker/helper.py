import cv2
import numpy as np
import laspy
import json

def create_birdseye_view(lidar_file, output_size=(600, 600), point_color=(255, 255, 255), background_color=(0, 0, 0), range_m=100):
    """
    Creates a bird's-eye view image from a LiDAR .las file and returns it as a NumPy array,
    focusing on a specific range (e.g., 100m x 100m).

    Parameters:
    - lidar_file: Path to the .las file.
    - output_size: Tuple specifying the output image size (width, height).
    - point_color: Color of the points in the bird's-eye view (B, G, R).
    - background_color: Background color of the image (B, G, R).
    - range_m: The range in meters to include in the bird's-eye view (default is 100m).

    Returns:
    - A NumPy array representing the bird's-eye view image.
    """
    # Load LiDAR data
    with laspy.open(lidar_file) as file:
        las = file.read()
        points = np.vstack((las.x, las.y)).transpose()  # type: ignore # Use only x and y for 2D projection

    # Filter points to include only those within the specified range
    center_x, center_y = 0, 0
    min_x, max_x = center_x - range_m / 2, center_x + range_m / 2
    min_y, max_y = center_y - range_m / 2, center_y + range_m / 2
    points_filtered = points[(points[:, 0] >= min_x) & (points[:, 0] <= max_x) & (points[:, 1] >= min_y) & (points[:, 1] <= max_y)]

    # Create a blank image
    img = np.zeros((output_size[1], output_size[0], 3), dtype=np.uint8)
    cv2.rectangle(img, (0, 0), (output_size[0], output_size[1]), background_color, -1)

    # Normalize filtered points to fit in the image dimensions
    norm_points = (points_filtered - [min_x, min_y]) / (range_m)
    scaled_points = norm_points * [output_size[0], output_size[1]]

    # Draw points on the image
    for point in scaled_points:
        cv2.circle(img, (int(point[0]), int(point[1])), 1, point_color, -1)

    return img

def get_folders_to_process(source_joy_click_folder):
    raw_data_folders = []
    with open(source_joy_click_folder, 'r') as file:
        folders = file.readlines()
        raw_data_folders = [f.strip() for f in folders]
    return raw_data_folders

def get_city_name(folder_name):
    video_date = folder_name.split('_')[0]
    #The date is in the format of DD-MM-YYYY. The city is austin if date is in the range of 01-05-22 to 31-05-22.
    date = int(video_date.split('-')[0])
    month = int(video_date.split('-')[1])
    if month == 5:
        if date >= 1 and date <= 31:
            return "austin"
    if (month == 6 and 1 <= date <= 15) or (month == 7 and 1 <= date <= 2):
        return "san_diego"
    if (month == 7 and 25 <= date <= 31) or (month == 8 and 1 <= date <= 10):
        return "boston"
    else:
        return "indy"
    
def get_lidar_config():
    beam_altitude_angles =[]
    beam_azimuth_angles =[]
    config_file = "/mnt/TASI-VRU2/configs/lidar_config.json"
    with open(config_file) as json_file:
        data = json.load(json_file)
        beam_altitude_angles = data['beam_altitude_angles'] # store altitude angles
        beam_azimuth_angles = data['beam_azimuth_angles']  # store azimuth angles
    return beam_altitude_angles, beam_azimuth_angles