from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='uav_navigation',
            executable='path_planner_node',
            name='fpga_path_planner_node',
            output='screen',
            parameters=[
                {'voxel_resolution': 0.25},
                {'bitstream_path': 'fpga/hardware/output/system.bit'}
            ]
        )
    ])