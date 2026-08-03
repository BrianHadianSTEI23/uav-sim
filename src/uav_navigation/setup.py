from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'uav_navigation'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='UAV Developer',
    maintainer_email='dev@uav.org',
    description='ROS 2 Acceleration Node connecting PointClouds to PYNQ FPGA Path Planner',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'path_planner_node = uav_navigation.path_planner_node:main',
        ],
    },
)
