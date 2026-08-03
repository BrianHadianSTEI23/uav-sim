import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    slam_dir = get_package_share_directory('uav_slam')
    octomap_params = os.path.join(slam_dir, 'config', 'octomap_params.yaml')

    return LaunchDescription([
        # 1. PointCloud Filtering Node
        Node(
            package='uav_slam',
            executable='pointcloud_filter_node',
            name='pointcloud_filter_node',
            output='screen'
        ),

        # 2. OctoMap Server Node (Generates 3D Voxel Map)
        Node(
            package='octomap_server',
            executable='octomap_server_node',
            name='octomap_server',
            output='screen',
            parameters=[octomap_params],
            remappings=[
                ('cloud_in', '/drone/pointcloud_filtered')
            ]
        ),

        # 3. Static World -> Odom Frame Publisher (For SLAM Localization Anchor)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='world_to_odom_publisher',
            arguments=['0', '0', '0', '0', '0', '0', 'world', 'odom']
        )
    ])