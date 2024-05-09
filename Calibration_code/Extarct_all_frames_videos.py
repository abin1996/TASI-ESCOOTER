import os
import cv2

# Function to extarct all the frames from a given video into the output folder
def extract_frames(video_file, output_folder):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Open the video file
    cap = cv2.VideoCapture(video_file)
    
    # Initialize frame counter
    frame_count = 0
    
    # Extract frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Save frame as image
        frame_path = os.path.join(output_folder, f"frame_{frame_count}.jpg")
        cv2.imwrite(frame_path, frame)
        
        # Increment frame counter
        frame_count += 1
    
    # Release the video capture object
    cap.release()

# Function to iterate through all the videos in the raw data folder
# and extarct all the frames for all the video file and save them in
# individual sub folders in the processed folder
def extract_frames_from_videos(input_folder):
    calibration_folder = os.path.join(input_folder, 'calibration')
    processed_folder = os.path.join(input_folder, 'processed')
    videos_folder = os.path.join(processed_folder, 'videos')
    extracted_frames_folder = os.path.join(calibration_folder, 'extracted_frames')
    
    # Get list of video files
    video_files = [f for f in os.listdir(videos_folder) if f.startswith('image')]
    
    # Extract frames from each video
    for video_file in sorted(video_files):
        video_path = os.path.join(videos_folder, video_file)
        video_name = os.path.splitext(video_file)[0]
        output_folder = os.path.join(extracted_frames_folder, video_name[:37])
        extract_frames(video_path, output_folder)
        print(f"Frames extracted from {video_file} and saved in {output_folder}")


# Provide the raw data folder path
input_folder = '/home/dp75@ads.iu.edu/TASI/TASI_Project/Calibration_code/20-06-22_22-18-30'
extract_frames_from_videos(input_folder)
