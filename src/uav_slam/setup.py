from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'uav_slam'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='UAV Developer',
    maintainer_email='dev@uav.org',
    description='ROS 2 SLAM and OctoMap mapping package',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'pointcloud_filter_node = uav_slam.pointcloud_filter_node:main',
            'geometric_controller_node = uav_slam.geometric_controller_node:main',
        ],
    },
)
