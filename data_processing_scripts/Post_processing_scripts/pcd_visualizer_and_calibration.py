import open3d as o3d
import numpy as np
import plotly.express as px

def load_pcd(file_path):
    """Load a PCD file and return its points as a numpy array."""
    pcd = o3d.io.read_point_cloud(file_path)
    return np.asarray(pcd.points)

def adjust_points(points, adjustments):
    """Apply coordinate adjustments to the points."""
    return points + adjustments

def visualize_pcds(points1, points2):
    """Visualize two point clouds using Plotly."""
    
    # Calculate distance from the origin for both point clouds
    distances1 = np.linalg.norm(points1, axis=1)
    distances2 = np.linalg.norm(points2, axis=1)
    
    # Create a DataFrame for Plotly Express
    import pandas as pd
    df1 = pd.DataFrame(points1, columns=['x', 'y', 'z'])
    df1['distance'] = distances1
    df2 = pd.DataFrame(points2, columns=['x', 'y', 'z'])
    df2['distance'] = distances2
    
    # Plot using Plotly Express
    fig = px.scatter_3d(df1, x='x', y='y', z='z', color='distance', color_continuous_scale='Turbo', title='Point Cloud 1')
    fig.update_traces(marker=dict(size=1), selector=dict(mode='markers'))
    fig.update_layout(scene_aspectmode='data')

    # Add the second point cloud
    fig.add_trace(px.scatter_3d(pd.DataFrame(points2, columns=['x', 'y', 'z']), x='x', y='y', z='z').data[0])
    fig.update_traces(marker=dict(size=1.05, color='red'), selector=dict(name='Point Cloud 2'))
    
    fig.show()

def main():
    # File paths for your PCD files
    pcd_file1 = '/home/pate2372/TASI/Work/pcd/1/point_cloud/lidar_1717197321031.pcd'
    pcd_file2 = '/media/pate2372/DA 21/Work_temp/Input/2024-06-03_16-06-37/2024-06-03_16-06-37_1_1717445541_1717445551/1FPS/radar_pcd/radar_1717445541015.pcd'
    
    # Load the point clouds
    points1 = load_pcd(pcd_file1)
    points2 = load_pcd(pcd_file2)
    
    # Adjustments for the second point cloud (x, y, z)
    # adjustments = np.array([2.98, 0, -0.66])
    adjustments = np.array([0, 0, 0])
    adjusted_points2 = adjust_points(points2, adjustments)
    
    # Visualize the point clouds
    visualize_pcds(points1, adjusted_points2)

if __name__ == "__main__":
    main()
