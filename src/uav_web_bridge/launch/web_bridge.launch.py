import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('uav_web_bridge')
    config_file = os.path.join(pkg_dir, 'config', 'web_bridge_params.yaml')

    return LaunchDescription([
        # 1. rosbridge_websocket node (Port 9090)
        Node(
            package='rosbridge_server',
            executable='rosbridge_websocket',
            name='rosbridge_websocket',
            output='screen',
            parameters=[config_file]
        ),

        # 2. web_video_server node (Port 8080)
        Node(
            package='web_video_server',
            executable='web_video_server',
            name='web_video_server',
            output='screen',
            parameters=[config_file]
        )
    ])