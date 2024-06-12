import pandas as pd
import pickle
import numpy as np
import os 
import sys
#count down the time
import tqdm


def read_pkl(file_path
                        ):
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    return data

def save_numpy_as_pcd(data, file_path):
    header = """# .PCD v0.7 - Point Cloud Data file format
VERSION 0.7
FIELDS x y z intensity
SIZE 4 4 4 4
TYPE F F F F
COUNT 1 1 1 1
WIDTH {}
HEIGHT 1
VIEWPOINT 0 0 0 1 0 0 0
POINTS {}
DATA ascii
""".format(data.shape[0], data.shape[0])
    
    with open(file_path, 'w') as f:
        f.write(header)
        for row in data:
            f.write(f"{row[0]} {row[1]} {row[2]} {row[3]}\n")

def prepare_annotate_folder(folder_dir,save_folder):
    # folder_dir = '/media/rtian2/New Volume/Jimmy/escooter_2024/data_preprocessed/sample_data/05-08-22_10-33-20_25202545_2_004_110/'
    folder_name = folder_dir.split('/')[-1]
    #/media/rtian2/New Volume/Jimmy/escooter_2024/data_preprocessed/sample_data/05-08-22_10-33-20_25202545_2_004_110/05-08-22_10-33-20_25202545_2_004_110_images
    image_folder = os.path.join(folder_dir, folder_name+'_images')
    lidar_file_name =  folder_dir.split('/')[-1] + '_case_pcd_ts.pkl'
    lidar_file = os.path.join(folder_dir, lidar_file_name)
    selection_file_name = folder_dir.split('/')[-1] + '_frame_combine_selection.pkl'
    selection_file = os.path.join(folder_dir, selection_file_name)
    lidar_data = read_pkl(lidar_file)
    frame_selection = read_pkl(selection_file)
    
    assert len(frame_selection['back_mid'][0]) == len(frame_selection['front_left'][0]) == len(frame_selection['front_right'][0]) == len(frame_selection['bd'])
    #make pcd dir
    op_pcd_dir = os.path.join(save_folder, folder_name,'pointcloud')
    if not os.path.exists(op_pcd_dir):
        os.makedirs(op_pcd_dir)
    #make image dir
    op_img_dir = os.path.join(save_folder, folder_name,'related_images')
    if not os.path.exists(op_img_dir):
        os.makedirs(op_img_dir)
    
    #save pcd and image tqdm
    #for i in tqdm.tqdm(range(len(frame_selection['bd']))):
    for i in tqdm.tqdm(range(100,230)):
    #for i in range(len(frame_selection['bd'])):
        #'/content/05-08-22_10-33-20_25202545_2_004_110/05-08-22_10-33-20_25202545_2_004_110_bird_eye/05-08-22_10-33-20_25202545_2_004_110_15166.png',

        pcd_id = frame_selection['bd'][i].split('_')[-1].split('.')[0]
        pcd = lidar_data[int(pcd_id)]
        #pcd float8
        pcd = pcd.astype(np.float16)
        #00001.pcd
        output_id = str(i).zfill(5)
        op_pcd_name = output_id + '.pcd'
        op_image_folder_name =  output_id+'_pcd'
        output_pcd_dir = os.path.join(op_pcd_dir, op_pcd_name)
        save_numpy_as_pcd(pcd, output_pcd_dir)
        
        #save image
        for camera in [ 'front_mid', 'front_right','front_left']:
    
        #for camera in ['back_mid', 'front_left', 'back_right', 'front_mid', 'back_left', 'front_right']:
            cam_img_names = frame_selection[camera][1][i].split('/')
            cam_img_name = cam_img_names[-2]+'/' + cam_img_names[-1]
            image_dir = os.path.join(image_folder, cam_img_name)
            #copy to the new folder
            op_image_folder = os.path.join(op_img_dir, op_image_folder_name)
            if not os.path.exists(op_image_folder):
                os.makedirs(op_image_folder)
            op_image_dir = os.path.join(op_image_folder, camera+'.png')
            os.system('cp "{}" "{}" '.format(image_dir, op_image_dir))
    print('Done with {}'.format(folder_name))
    return

if __name__ == "__main__":
    folder_dir = '/media/rtian2/New Volume/Jimmy/escooter_2024/data_preprocessed/sample_data/05-08-22_10-33-20_25202545_2_004_110'
    # lidar_file_name =  folder_dir.split('/')[-1] + '_case_pcd_ts.pkl'
    # lidar_file = os.path.join(folder_dir, lidar_file_name)
    # selection_file_name = folder_dir.split('/')[-1] + '_frame_combine_selection.pkl'
    # selection_file = os.path.join(folder_dir, selection_file_name)
    # lidar_data = read_pkl(lidar_file)
    # frame_selection = read_pkl(selection_file)

    save_folder = "/media/rtian2/New Volume/Jimmy/escooter_2024/data_preprocessed/sample_annotate_data"
    prepare_annotate_folder(folder_dir,save_folder)