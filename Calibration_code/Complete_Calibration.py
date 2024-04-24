import numpy as np
import pandas as pd
import os
import cv2

# All the inputs here!!
# Change the raw data folder path
input_folder = '/home/dp75@ads.iu.edu/TASI/TASI_Project/Calibration_code/20-06-22_22-18-30'

# Taking the video number for choosing the camera
video_number = int(input("Enter the video number you want to grab (1 to 6): "))


# Function for grabbing the path for lidar and video files from the raw data folder
def grab_files(input_folder, video_number):
    lidar_folder = os.path.join(input_folder, 'lidar')
    processed_folder = os.path.join(input_folder, 'processed')

    # Grab bag file from lidar folder
    bag_files = [f for f in os.listdir(lidar_folder) if f.endswith('.bag')]
    if len(bag_files) == 0:
        print("No bag file found in the 'lidar' folder....")
        return
    elif len(bag_files) == 1:
        print("Grabbing the Bag file....")
    elif len(bag_files) > 1:
        print("Multiple bag files found in the 'lidar' folder. Taking the first one.")
    bag_file = os.path.join(lidar_folder, bag_files[0])

    # Grab video file from videos folder
    videos_folder = os.path.join(processed_folder, 'videos')
    video_files = [f for f in os.listdir(videos_folder) if f.startswith('image')]
    if len(video_files) == 0:
        print("No video files found in the 'videos' folder.")
        return
    else:
        print(f"Grabbing video_{video_number}....")
    video_file = os.path.join(videos_folder, sorted(video_files)[video_number - 1])

    return bag_file, video_file

def extract_single_frame(video_file):
    # Open the video file
    cap = cv2.VideoCapture(video_file)
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total number of frames in the video: {total_frames}")
    
    # Ask the user to input a frame number
    frame_number = int(input("Enter the frame number you want to extract: "))
    frame_number_index = frame_number-1
    
    # Check if the frame number is within the valid range
    if frame_number_index < 0 or frame_number_index >= total_frames:
        print("Invalid frame number.")
        return

    # Move the video capture to the desired frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number_index)
    
    # Read the frame
    ret, frame = cap.read()
    if not ret:
        print("Error reading frame.")
        return
    
    # Close the video capture object
    cap.release()
    
    # Get the video name
    video_name = os.path.splitext(os.path.basename(video_file))[0]
    
    # Create the output folder path
    calibration_folder = os.path.join(input_folder, 'calibration')
    output_folder = os.path.join(calibration_folder, video_name[:37])
    os.makedirs(output_folder, exist_ok=True)
    
    # Save the frame as an image
    frame_path = os.path.join(output_folder, f"frame_{frame_number}.jpg")
    cv2.imwrite(frame_path, frame)
    print(f"Extracting frame_{frame_number} from video_{video_number}....")
    #print(f"Frame {frame_number} extracted and saved in {output_folder}")
    return frame, frame_number


bag_file, video_file = grab_files(input_folder, video_number)
img, frame_number = extract_single_frame(video_file)