import numpy as np
import pandas as pd
import os
import cv2
import csv
import rosbag
import math
import plotly.express as px
import json
from os1.packet import (
    AZIMUTH_BLOCK_COUNT,
    CHANNEL_BLOCK_COUNT,
    azimuth_angle,
    azimuth_block,
    azimuth_measurement_id,
    azimuth_timestamp,
    channel_signal_photons,
    azimuth_valid,
    channel_block,
    channel_range,
    unpack,
)


# All the inputs here!!
# Change the raw data folder path
input_folder = '/home/dp75@ads.iu.edu/TASI/TASI_Project/Calibration_code/20-06-22_22-18-30'

# Taking the video number for choosing the camera
video_number = int(input("Enter the video number you want to grab (1 to 6): "))

# The config data is imported here
beam_altitude_angles =[]
beam_azimuth_angles =[]
with open("config.json") as json_file:
    data = json.load(json_file)
    beam_altitude_angles = data['beam_altitude_angles']
    beam_azimuth_angles = data['beam_azimuth_angles']

# To get the correct camera intrinsic matrix
if video_number == 1:
    k = np.array([[1033.23379748766,	0,	1016.01489820476],
                  [0,   1038.61744751735,	1043.44387613757],
                  [0,	0,	1]])
elif video_number == 2:
    k = np.array([[2335.84070767099,	0,	1095.01424290238],
                  [0,	2388.19737415055,	1603.08968082779],
                  [0,	0,	1]])
elif video_number == 3:
    k = np.array([[1167.6100038541,	    0,	967.480172954816],
                  [0,	1150.37099372804,	985.647777291194],
                  [0,	0,	1]])
elif video_number == 4:
    k = np.array([[1114.69712964981,    0,	993.047280303644],
                  [0,	1115.50271181832,	1005.27437164983],
                  [0,	0,	1]])
elif video_number == 5:
    k = np.array([[1122.79229006074,    0,	1002.35362307102],
                  [0,	1121.63153441121,	1026.32657908432],
                  [0,	0,	1]])
elif video_number == 6:
    k = np.array([[2511.41526616201,    0,	933.745797711871],
                  [0,	2524.72683116961,	1208.95510763454],
                  [0,	0,	1]])
camera_matrix = k

dist_coeffs = np.zeros(5)  # Make sure the number of distortion coefficients matches what is expected

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

# Function for extracting the desired frame from the video as an image
def extract_image_frame(video_file):
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

# Function for extractig the desired lidar frame from the lidar data
def extract_lidar_frame(bag_file, frame_number):
    X = []
    Y = []
    Z = []
    Intensity = []
    bag = rosbag.Bag(bag_file)
    track = 0
    frame = 0
    for topic, msg, t in bag.read_messages(topics=['/os_node/lidar_packets']):
        track += 1
        raw_packet=msg.buf[:-1]
        if not isinstance(raw_packet, tuple):
            packet = unpack(raw_packet)
        for b in range(AZIMUTH_BLOCK_COUNT):  #Azimuth loop contains 16 azimuth blocks  azimuth angles
           az_block = azimuth_block(b, packet)
           enc = az_block[3]
           for i in range(64): ##64 channel blocks in every data block
               ch_block = channel_block(i,az_block)
               ch_range = channel_range(ch_block)
               theta  = 2*math.pi*( (enc/90112) + ((beam_azimuth_angles[i])/360) )
               phi    = 2*math.pi*( beam_altitude_angles[i] / 360 )
               r = ch_range/1000 #/1000 #/1000000
               x_point =   r * math.cos(theta) * math.cos(phi)
               y_point =  -1 * r * math.sin(theta) * math.cos(phi)
               z_point =   r * math.sin(phi)
               ch_int = channel_signal_photons(ch_block)
               X.append( x_point )
               Y.append( y_point )
               Z.append( z_point )
               Intensity.append( ch_int )
        
        # Construct output file path
        calibration_folder = os.path.join(input_folder, 'calibration')
        output_folder = os.path.join(calibration_folder, 'lidar_frames/')
        os.makedirs(output_folder, exist_ok=True)

        if track == 128:
            track = 0
            frame += 1
            filename = output_folder + 'lidar_frame_' + str(frame) + '_' + '.csv'

            # Writing to CSV
            if frame == frame_number: 
                print("Running.....",frame)
                with open(filename, 'w', newline='') as csvfile:
                    fieldnames = ['X', 'Y', 'Z', 'Intensity']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    for x, y, z, intensity in zip(X, Y, Z, Intensity):
                        writer.writerow({'X': x, 'Y': y, 'Z': z, 'Intensity': intensity})
                data = {'X': X, 'Y': Y, 'Z': Z, 'Intensity': Intensity}
                lidar = pd.DataFrame(data)
                break
                X = []
                Y = []
                Z = []
                Intensity = []
    return lidar

# Function for extracting the points from the image frame
def extract_image_points(img):
    # Resize image to fit within screen size
    screen_height, screen_width = 1080, 1920  # Adjust these values according to your screen resolution
    img_height, img_width = img.shape[:2]
    if img_height > screen_height or img_width > screen_width:
        scaling_factor = min(screen_height / img_height, screen_width / img_width)
        img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
    
    img_copy = img.copy()
    img_points = []

    def mouse_callback(event, x, y, flags, param):
        nonlocal img_points

        if event == cv2.EVENT_LBUTTONDOWN:
            if len(img_points) < 8:
                cv2.circle(img_copy, (x, y), 3, (0, 255, 0), -1)
                cv2.putText(img_copy, f"img_pt_{len(img_points) + 1}", (x + 5, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                img_points.append([x, y])
                cv2.imshow('image', img_copy)

    cv2.namedWindow('image', cv2.WINDOW_NORMAL)  # Create resizable window
    cv2.setMouseCallback('image', mouse_callback)

    while True:
        cv2.imshow('image', img_copy)
        key = cv2.waitKey(1) & 0xFF

        # If 'enter' is pressed, exit loop
        if key == 13:  # ASCII code for Enter key
            break
    cv2.destroyAllWindows()
    return img_points

# Function to visualize the lidar points
def visualize_lidar(lidar):
    fig = px.scatter_3d(lidar, x='X' , y='Y', z='Z')
    fig.update_traces(marker=dict(size=1),selector=dict(mode = 'markers'))
    fig.update_layout(scene_aspectmode = 'data')
    fig.show()
    print('Visualizing lidar....')

# Function for inputing the lidar points corresponding to the image points
def get_lidar_points():
    while True:
        try:
            num_points = int(input("Enter the number of lidar points: "))
            if num_points <= 0:
                print("Number of points must be greater than zero.")
            else:
                break
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

    lidar_points = []

    for i in range(1, num_points + 1):
        while True:
            try:
                x, y, z = map(float, input(f"Enter coordinates for lidar_pt_{i}: ").split())
                lidar_points.append([x, y, z])
                break
            except ValueError:
                print("Invalid input. Please enter three floating-point numbers separated by spaces.")

    return lidar_points

# Function to get the extrinsic matrix
def estimate_extrinsic_matrix(lidar_points, image_points, camera_matrix, dist_coeffs):
    # Estimate the extrinsic matrix using cv2.solvePnP
    lidar_points = (np.array(lidar_points)).astype(np.float32).reshape(-1, 1, 3)
    image_points = (np.array(image_points)).astype(np.float32).reshape(-1, 1, 2)
    _, rvec, tvec,pt = cv2.solvePnPRansac(lidar_points, image_points, camera_matrix, dist_coeffs)

    # Convert the rotation vector to a rotation matrix
    rmat, _ = cv2.Rodrigues(rvec)

    # Create the extrinsic matrix
    extrinsic_matrix = np.hstack((rmat, tvec))

    return True, rvec, tvec, extrinsic_matrix

bag_file, video_file = grab_files(input_folder, video_number)
img, frame_number = extract_image_frame(video_file)
lidar = extract_lidar_frame(bag_file, frame_number)
img_points = extract_image_points(img)
visualize_lidar(lidar)
lidar_points = get_lidar_points()
success, rotation_vector, translation_vector, extrinsic_matrix = estimate_extrinsic_matrix(lidar_points, img_points, camera_matrix, dist_coeffs)

if success:
    print("Rotation Vector:\n", rotation_vector)
    print("Translation Vector:\n", translation_vector)
    print("Extrinsic Matrix:\n", extrinsic_matrix)
else:
    print("Extrinsic matrix generation failed.")

def adjust_extrinsic_matrix(rotation_vector,translation_vector,img):
    uvrgb_list = []
    for i in range(len(lidar)):
        X = np.array([(lidar.X.iloc[i],lidar.Y.iloc[i],lidar.Z.iloc[i])])
        (nose_end_point2D, jacobian) = cv2.projectPoints(X, rotation_vector, translation_vector, camera_matrix, dist_coeffs)
        u,v = ( int(nose_end_point2D[0][0][0]), int(nose_end_point2D[0][0][1]))
        g = 255 #maps(refl,init,fin,0,255)
        r,g,b = 0,g,0 
        uvrgb_list.append([u,v,r,g,b]) 
    for i in range(len(uvrgb_list)):
        u = uvrgb_list[i][0]
        v = uvrgb_list[i][1]
        r,g,b = uvrgb_list[i][4],uvrgb_list[i][3],uvrgb_list[i][2]
        if ( u > 0 and u < 2048 and v > 0 and v < 2048 ):
            cv2.line(img,(u,v),(u,v),(r,g,b),8) 
    scale_percent = 40 # percent of original size
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    # resize image
    resized_func = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    return resized_func
       
def Key_pressed(x):
    print("key pressed")
    pass

scale_percent = 40 # percent of original size
width = int(img.shape[1] * scale_percent / 100)
height = int(img.shape[0] * scale_percent / 100)
dim = (width, height)
# resize image
disp_image = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
disp_image_og =disp_image

cv2.namedWindow('image')
## create trackbars for color change
cv2.createTrackbar('R','image',0,255,Key_pressed)
cv2.createTrackbar('G','image',0,255,Key_pressed)
cv2.createTrackbar('B','image',0,255,Key_pressed)

r_addition_vector_1 = np.array([[ 0.002],[ 0.0 ],[ 0.0],])  
r_addition_vector_2 = np.array([[ 0.0],[ 0.002],[ 0.0],])    
r_addition_vector_3 = np.array([[ 0.0],[ 0.0 ],[ 0.002],])
r_subtraction_vector_1 = np.array([[ -0.002],[ 0.0 ],[ 0.0],])  
r_subtraction_vector_2 = np.array([[ 0.0],[ -0.002],[ 0.0],])    
r_subtraction_vector_3 = np.array([[ 0.0],[ 0.0 ],[ -0.002],])

addition_vector_1 = np.array([[ 0.105],[ 0.0 ],[ 0.0],])  
addition_vector_2 = np.array([[ 0.0],[ 0.105],[ 0.0],])    
addition_vector_3 = np.array([[ 0.0],[ 0.0 ],[ 0.105],])
subtraction_vector_1 = np.array([[ -0.105],[ 0.0 ],[ 0.0],])  
subtraction_vector_2 = np.array([[ 0.0],[ -0.105],[ 0.0],])    
subtraction_vector_3 = np.array([[ 0.0],[ 0.0 ],[ -0.105],])
    
#create switch for ON/OFF functionality
switch = '0 : OFF \n1 : ON'
cv2.createTrackbar(switch, 'image',0,1,Key_pressed)

while(1):
    #cv2.imshow('image', disp_image)
    cv2.imshow('image', disp_image)
    k = cv2.waitKey(1) # & 0xFF
    if not k == -1:
        print(k)
    if k == 27: # esc
        break
    elif k == 113: # q Moves the lidar superposition slightly up and very slightly left
        rotation_vector = rotation_vector + r_addition_vector_1
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 119: # w Moves the lidar superposition slightly up and slightly right
        rotation_vector = rotation_vector + r_addition_vector_2
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 101: # e Moves the lidar superposition very slightly up and slightly left
        rotation_vector = rotation_vector + r_addition_vector_3
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 114: # r  Moves the lidar superimposition right 
        translation_vector  = translation_vector + addition_vector_1
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 116: # t  Moves the lidar superimposition down
        translation_vector  = translation_vector + addition_vector_2
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 121: # y  Moves the lidar superimposition farther into the image (away from viewer)
        translation_vector  = translation_vector + addition_vector_3
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 97: # a Moves the lidar superposition slightly down and very slightly right
        rotation_vector = rotation_vector + r_subtraction_vector_1
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 115: # s Moves the lidar superposition slightly down and slightly left
        rotation_vector = rotation_vector + r_subtraction_vector_2
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 100: # d Moves the lidar superposition very slightly down and slightly right
        rotation_vector = rotation_vector + r_subtraction_vector_3
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 102: # f  Moves the lidar superimposition left
        translation_vector  = translation_vector + subtraction_vector_1
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 103: # g  Moves the lidar superimposition up
        translation_vector  = translation_vector + subtraction_vector_2
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)
    elif k == 104: # h  Moves the lidar superimposition nearer out of the image (towarsds the viewer)
        translation_vector  = translation_vector + subtraction_vector_3
        disp_image = adjust_extrinsic_matrix(rotation_vector, translation_vector,img)

    s = cv2.getTrackbarPos(switch,'image') 
    
final_rotation_vector = rotation_vector 
final_translation_vector = translation_vector
frmat = cv2.Rodrigues(final_rotation_vector)[0]
fcam_pos  = -np.matrix(frmat).T * np.matrix(final_translation_vector)


output_data = {
    "final_rotation_vector": final_rotation_vector.tolist(),
    "final_translation_vector": final_translation_vector.tolist(),
    "final_rotational_matrix": frmat.tolist()}

output_directory = "Final_Outputs"

# Check if the directory exists, if not, create it
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Convert rotation, translation and rotational vectors to numpy arrays
final_rotation_matrix = np.array(final_rotation_vector)
final_translation_matrix = np.array(final_translation_vector)
final_rmat =  np.array(frmat)

# Save all three matices in a single JSON file
output_data = {
    "final_rotation_vector": final_rotation_vector.tolist(),
    "final_translation_vector": final_translation_vector.tolist(),
    "final_rotational_matrix": frmat.tolist()}
with open(os.path.join(output_directory, "output_data.json"), 'w') as f:
    json.dump(output_data, f)

# Save the final image
cv2.imwrite(os.path.join(output_directory, "final_image.jpg"), disp_image)
print("All files saved in Final_Outputs folder")

print ("final_rotation", final_rotation_vector)
print ("final_translation", final_translation_vector)
print ("final_rotational_matrix", frmat)
cv2.destroyAllWindows()

