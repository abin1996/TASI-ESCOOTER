import numpy as np
import cv2
import pandas as pd
import os
import laspy
import plotly.express as px
import matplotlib.pyplot as plt
import open3d as o3d
import shutil

#texas

K_1 = np.array([[1033.233797, 0, 1016.014898], [0, 1038.617448, 1043.443876], [0, 0, 1]])
K_2 = np.array([[2335.840708, 0, 1095.014243], [0, 2388.197374, 1603.089681], [0, 0, 1]])
K_3 = np.array([[1167.610004, 0, 967.480173], [0, 1150.370994, 985.6477773], [0, 0, 1]])
K_4 = np.array([[1114.69713, 0, 993.0472803], [0, 1115.502712, 1005.274372], [0, 0, 1]])
K_5 = np.array([[1122.79229, 0, 1002.353623], [0, 1121.631534, 1026.326579], [0, 0, 1]])
K_6 = np.array([[2511.415266, 0, 933.7457977], [0, 2524.726831, 1208.955108], [0, 0, 1]])

Extrinsic_matrix_1 =  [[-0.78589995,  0.60338363, -0.13523855, -0.78569811]
 [ 0.1963648,   0.0361422,  -0.97986459, -0.14593076],
 [-0.58634643, -0.79663162, -0.14688746, -1.18402034]]

Extrinsic_matrix_2 =  [[-0.13370937, -0.98728953,  0.08591379, -0.10159966],
 [-0.32974187, -0.03743114, -0.94332879,  0.16688552],
 [ 0.9345545,  -0.15446127, -0.3205458,  -1.65365814]]

Extrinsic_matrix_3 =  [[ 0.85995333,  0.50604688,  0.06630859,  0.10349485],
 [ 0.11448021, -0.0646474,  -0.99131982, -0.28036357],
 [-0.49736763,  0.8600798,  -0.1135261,  -0.7033595 ]]

Extrinsic_matrix_4 =  [[-0.91765706, -0.39516873,  0.0417995,   0.27993   ],
 [-0.1287632,   0.19619017, -0.97207482, -0.22725004],
 [ 0.37593292, -0.89741356, -0.23091849, -0.59818496]]

Extrinsic_matrix_5 =  [[ 0.64580222, -0.76279194,  0.03298416,  0.18530389],
 [-0.1735367,  -0.18871739, -0.96657683, -0.10114308],
 [ 0.74352169,  0.6184935,  -0.2542465,  -0.89450736]]

Extrinsic_matrix_6 =  [[ 0.10355953,  0.99455911, -0.01129566,  0.26178784],
 [ 0.13931167, -0.02574888, -0.98991376, -0.07730908],
 [-0.9848186,   0.10094139, -0.14122023, -2.20626577]]


def project_lidar_points_to_image(lidar_points, intrinsic_matrix, extrinsic_matrix, image):
    """
    Project 3D LiDAR points to 2D image coordinates using intrinsic and extrinsic matrices and overlay them on the given image.

    Parameters:
    - lidar_points: A numpy array (N, 3) representing the (x, y, z) coordinates of multiple LiDAR points.
    - intrinsic_matrix: A 3x3 numpy array representing the camera intrinsic parameters.
    - extrinsic_matrix: A 3x4 numpy array representing the camera extrinsic parameters (rotation and translation).
    - image: A numpy array representing the 2D image onto which LiDAR points are to be projected.

    Returns:
    - A numpy array representing the image with projected points overlayed.
    """
    # Create a homogenous coordinate array from LiDAR points
    num_points = lidar_points.shape[0]
    homogeneous_lidar_points = np.hstack((lidar_points, np.ones((num_points, 1))))

    # Transform the LiDAR points to camera coordinates
    camera_coords = np.dot(extrinsic_matrix, homogeneous_lidar_points.T)

    # Project to pixel coordinates
    pixel_coords = np.dot(intrinsic_matrix, camera_coords[:3, :])  # Use only x, y, z for intrinsic multiplication

    # Normalize by the third (z) coordinate to convert to homogeneous 2D coordinates
    pixel_coords /= pixel_coords[2, :]  # Normalize (x, y, z) by z to get (x/z, y/z, 1)

    # Round the coordinates and change to integer type for image indexing
    pixel_coords = np.rint(pixel_coords[:2, :]).astype(int)

    # Overlay points on the image
    for x, y in pixel_coords.T:
        if x >= 0 and y >= 0 and x < image.shape[1] and y < image.shape[0]:
            cv2.circle(image, (x, y), 3, (0, 255, 0), -1)  # Draw green circles on the projected points

    return image

#save las to pcd

def convert_las_to_pcd(las_file_path, pcd_file_path):
    # Load LAS file
    las = laspy.read(las_file_path)
    
    # Extract points as numpy array
    points = np.vstack((las.x, las.y, las.z)).transpose()
    intensity = las.intensity
    # Create Open3D point cloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    # Optionally add colors if they exist
    if hasattr(las, 'red') and hasattr(las, 'green') and hasattr(las, 'blue'):
        colors = np.vstack((las.red, las.green, las.blue)).transpose() / 65535.0  # Normalize colors
        pcd.colors = o3d.utility.Vector3dVector(colors)

    # Save PCD file
    o3d.io.write_point_cloud(pcd_file_path, pcd)
    print(f"PCD file saved to {pcd_file_path}")


def convert_las_to_pcd_with_intensity(las_file_path, pcd_file_path):
    # Load the LAS file using laspy
    las = laspy.read(las_file_path)
    
    # Extract coordinates and intensity
    points = np.vstack((las.x, las.y, las.z)).transpose()
    intensity = las.intensity

    # Create a PCD file that includes the intensity
    with open(pcd_file_path, 'w') as file:
        file.write("VERSION .7\n")
        file.write("FIELDS x y z intensity\n")
        file.write("SIZE 4 4 4 4\n")
        file.write("TYPE F F F F\n")
        file.write("COUNT 1 1 1 1\n")
        file.write("WIDTH {}\n".format(len(points)))
        file.write("HEIGHT 1\n")
        file.write("VIEWPOINT 0 0 0 1 0 0 0\n")
        file.write("POINTS {}\n".format(len(points)))
        file.write("DATA ascii\n")
        for point, i in zip(points, intensity):
            file.write("{} {} {} {}\n".format(point[0], point[1], point[2], i))
    
    print(f"PCD file with intensity data saved to {pcd_file_path}")



# if __name__ == "__main__":

    folder_dir = "/media/rtian2/New Volume/Jimmy/escooter_2024/data_preprocessed/sample_scenario_output2/14-05-22_18-47-48_1652568488000_1652568528000/"
    sync_sce_dir = os.path.join(folder_dir, "sync_sce.csv")
    sync_sce = pd.read_csv(sync_sce_dir)

    for test_idx in range(0,400,50):
        test_image1_dir =  sync_sce.iloc[test_idx]["images1"]
        test_lidar_dir = sync_sce.iloc[test_idx]["lidar"]

        test_image1_dir = os.path.join(folder_dir, "images1", test_image1_dir)
        test_lidar_dir = os.path.join(folder_dir, "lidar", test_lidar_dir)

        test_image1 = cv2.imread(test_image1_dir)
        test_image1 = cv2.cvtColor(test_image1, cv2.COLOR_BGR2RGB)


        #read lidar (.las file)
        lidar_points = laspy.read(test_lidar_dir)
        lidar_points = np.vstack((lidar_points.x, lidar_points.y, lidar_points.z)).T
        lidar_points_df = pd.DataFrame(lidar_points, columns=["x", "y", "z"])
        lidar_points_df = lidar_points_df[(lidar_points_df["x"] < 0) & (lidar_points_df["y"] > -100)]
        lidar_points = lidar_points_df.to_numpy()



        f_im = project_lidar_points_to_image(lidar_points, K_1, Extrinsic_matrix_1, test_image1)
        plt.imshow(f_im)
        plt.show()

    # plt.scatter(pts[:,0],pts[:,1])
    # plt.xlim(-3000,3000)
    # plt.ylim(-3000,3000)
    # plt.show()
    
    #read pkl file
    # pkl_file_path = os.path.join("/media/rtian2/New Volume/Jimmy/escooter_2024/calibration_matrices/cali_test_data/san_diego/28-06-22_12-56-23_32083317_1_005_110_case_pcd_ts.pkl")
    # lidar_points = pd.read_pickle(pkl_file_path)
    # lidar_points_test = lidar_points[19300.0][:,:3]
    # test_image1 = cv2.imread("/media/rtian2/New Volume/Jimmy/escooter_2024/calibration_matrices/cali_test_data/san_diego/images1/28-06-22_12-56-23_32083317_1_005_110_frame19300.png")
    # test_image1 = cv2.cvtColor(test_image1, cv2.COLOR_BGR2RGB)
    # f_im,pts = fuse_lidar_to_image(lidar_points_test, test_image1, K_1, rotation_vector_1, translation_vector_1, Extrinsic_matrix_1)
    # plt.imshow(f_im)
    # plt.show()

    # folder_dir = "/media/rtian2/New Volume/Jimmy/escooter_2024/data_preprocessed/sample_scenario_output2/14-05-22_18-47-48_1652570283000_1652570456000/"
    # sync_sce_dir = os.path.join(folder_dir, "sync_sce.csv")
    # sync_sce = pd.read_csv(sync_sce_dir)
    # op_dir = "/media/rtian2/New Volume/Jimmy/escooter_2024/calibration_matrices/cali_test_data/austin2"
    # for test_idx in range(670,675):
    #     test_image1_dir =  sync_sce.iloc[test_idx]["images1"]
    #     test_image2_dir =  sync_sce.iloc[test_idx]["images2"]
    #     test_image3_dir =  sync_sce.iloc[test_idx]["images3"]
    #     test_image4_dir =  sync_sce.iloc[test_idx]["images4"]
    #     test_image5_dir =  sync_sce.iloc[test_idx]["images5"]
    #     test_image6_dir =  sync_sce.iloc[test_idx]["images6"]

    #     test_lidar_dir = sync_sce.iloc[test_idx]["lidar"]

    #     test_image1_dir = os.path.join(folder_dir, "images1", test_image1_dir)
    #     test_image2_dir = os.path.join(folder_dir, "images2", test_image2_dir)
    #     test_image3_dir = os.path.join(folder_dir, "images3", test_image3_dir)
    #     test_image4_dir = os.path.join(folder_dir, "images4", test_image4_dir)
    #     test_image5_dir = os.path.join(folder_dir, "images5", test_image5_dir)
    #     test_image6_dir = os.path.join(folder_dir, "images6", test_image6_dir)

    #     test_lidar_dir = os.path.join(folder_dir, "lidar", test_lidar_dir)

    #     # test_image1 = cv2.imread(test_image1_dir)
    #     # test_image1 = cv2.cvtColor(test_image1, cv2.COLOR_BGR2RGB)

    #     #read lidar (.las file)
    #     op_path_lidar = os.path.join(op_dir,"lidar",f"{test_idx}.pcd")
    #     op_path_images1 = os.path.join(op_dir,"images1",f"{test_idx}.png")
    #     op_path_images2 = os.path.join(op_dir,"images2",f"{test_idx}.png")
    #     op_path_images3 = os.path.join(op_dir,"images3",f"{test_idx}.png")
    #     op_path_images4 = os.path.join(op_dir,"images4",f"{test_idx}.png")
    #     op_path_images5 = os.path.join(op_dir,"images5",f"{test_idx}.png")
    #     op_path_images6 = os.path.join(op_dir,"images6",f"{test_idx}.png")

    #     if not os.path.exists(os.path.dirname(op_path_lidar)):
    #         os.makedirs(os.path.dirname(op_path_lidar))
    #     if not os.path.exists(os.path.dirname(op_path_images1)):
    #         os.makedirs(os.path.dirname(op_path_images1))
    #     if not os.path.exists(os.path.dirname(op_path_images2)):
    #         os.makedirs(os.path.dirname(op_path_images2))
    #     if not os.path.exists(os.path.dirname(op_path_images3)):
    #         os.makedirs(os.path.dirname(op_path_images3))
    #     if not os.path.exists(os.path.dirname(op_path_images4)):
    #         os.makedirs(os.path.dirname(op_path_images4))
    #     if not os.path.exists(os.path.dirname(op_path_images5)):
    #         os.makedirs(os.path.dirname(op_path_images5))
    #     if not os.path.exists(os.path.dirname(op_path_images6)):
    #         os.makedirs(os.path.dirname(op_path_images6))
            

    #     convert_las_to_pcd_with_intensity(test_lidar_dir, op_path_lidar)
    #     shutil.copy(test_image1_dir,op_path_images1)
    #     shutil.copy(test_image2_dir,op_path_images2)
    #     shutil.copy(test_image3_dir,op_path_images3)
    #     shutil.copy(test_image4_dir,op_path_images4)
    #     shutil.copy(test_image5_dir,op_path_images5)
    #     shutil.copy(test_image6_dir,op_path_images6)
