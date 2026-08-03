import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    slam_dir = get_package_share_directory('uav_slam')
    controller_params = os.path.join(slam_dir, 'config', 'controller_params.yaml')

    return LaunchDescription([
        # 1. SLAM & OctoMap Launch
        Node(
            package='uav_slam',
            executable='pointcloud_filter_node',
            name='pointcloud_filter_node',
            output='screen'
        ),

        # 2. Geometric Flight Controller Node
        Node(
            package='uav_slam',
            executable='geometric_controller_node',
            name='geometric_controller_node',
            output='screen',
            parameters=[controller_params]
        )
    ])