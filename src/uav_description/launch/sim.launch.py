import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_uav_description = get_package_share_directory('uav_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Paths
    xacro_file = os.path.join(pkg_uav_description, 'urdf', 'drone.urdf.xacro')
    world_file = os.path.join(pkg_uav_description, 'urdf', 'drone_world.sdf')
    bridge_config_file = os.path.join(pkg_uav_description, 'config', 'ros_gz_bridge.yaml')

    # Parse Xacro
    robot_description_raw = xacro.process_file(xacro_file).toxml()

    # 1. Robot State Publisher Node
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_raw, 'use_sim_time': True}]
    )

    # 2. Gazebo Sim Launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_file}'}.items()
    )

    # 3. Spawn Drone Model in Gazebo
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=['-string', robot_description_raw,
                   '-name', 'uav_drone',
                   '-z', '0.5']
    )

    # 4. ROS <-> Gazebo Parameter Bridge Node
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': bridge_config_file,
            'use_sim_time': True
        }],
        output='screen'
    )

    return LaunchDescription([
        node_robot_state_publisher,
        gazebo,
        spawn_entity,
        ros_gz_bridge
    ])