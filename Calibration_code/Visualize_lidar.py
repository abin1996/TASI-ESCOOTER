import os
import open3d as o3d
import pandas as pd
import numpy as np
import plotly.express as px
import laspy

def visualize_lidar_data(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.csv':
        # Read CSV file
        lidar_data = pd.read_csv(file_path)

        # Calculate distance from the origin
        lidar_data['distance'] = np.sqrt(lidar_data['X']**2 + lidar_data['Y']**2 + lidar_data['Z']**2)

        # Plot using Plotly
        fig = px.scatter_3d(x=lidar_data['X'], y=lidar_data['Y'], z=lidar_data['Z'], color=lidar_data['distance'], color_continuous_scale='Turbo')
        fig.update_traces(marker=dict(size=1), selector=dict(mode='markers'))
        fig.update_layout(scene_aspectmode='data')
        fig.show()

    elif file_extension == '.pcd':
        # Read PCD file
        pcd = o3d.io.read_point_cloud(file_path)
        pcd_points = np.asarray(pcd.points)

        # Calculate distance from the origin
        distances = np.linalg.norm(pcd_points, axis=1)

        # Plot using Plotly
        fig = px.scatter_3d(x=pcd_points[:, 0], y=pcd_points[:, 1], z=pcd_points[:, 2], color=distances, color_continuous_scale='Turbo')
        fig.update_traces(marker=dict(size=1), selector=dict(mode='markers'))
        fig.update_layout(scene_aspectmode='data')
        fig.show()

    elif file_extension == '.las':
        # Read LAS file
        las_file = laspy.read(file_path)
        las_points = np.vstack((las_file.x, las_file.y, las_file.z)).T

        # Calculate distance from the origin
        distances = np.linalg.norm(las_points, axis=1)

        # Plot using Plotly
        fig = px.scatter_3d(x=las_points[:, 0], y=las_points[:, 1], z=las_points[:, 2], color=distances, color_continuous_scale='Turbo')
        fig.update_traces(marker=dict(size=1), selector=dict(mode='markers'))
        fig.update_layout(scene_aspectmode='data')
        fig.show()

    else:
        print("Unsupported file format.")

# Give the path to the .csv, .pcd or .las file containing the lidar data below
visualize_lidar_data("Test_Files/lidar_1652568488001.las")
