from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory('uwb_driver')
    default_config = os.path.join(pkg_share, 'config', 'uwb_driver.yaml')

    return LaunchDescription([
        DeclareLaunchArgument(
            'config',
            default_value=default_config,
            description='Path to parameter YAML file',
        ),
        Node(
            package='uwb_driver',
            executable='uwb_serial_node.py',
            name='uwb_serial_node',
            output='screen',
            emulate_tty=True,
            parameters=[LaunchConfiguration('config')],
        ),
    ])
