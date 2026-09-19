from launch.substitutions import LaunchConfiguration
import xacro
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():

    pkg_path = get_package_share_directory('rover_description')

    urdf_file = os.path.join(
        pkg_path,
        'urdf',
        'rover.xacro'
    )

    rviz_config = os.path.join(
        pkg_path,
        'config',
        'urdf.rviz'
    )

    world_file = os.path.join(
        pkg_path,
        'worlds',
        'empty_world.sdf'
    )

    bridge_config = os.path.join(
        pkg_path,
        'config',
        'bridge.yaml'
    )

    # Gazebo resource path
    gazebo_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=os.path.dirname(pkg_path)
    )

    robot_description_config = xacro.process_file(urdf_file)
    robot_description = {
        'robot_description': robot_description_config.toxml()
    }

    # Launch Gazebo Harmonic
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': f'-r {world_file}'
        }.items()
    )

    # Spawn robot in Gazebo Harmonic
    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'rover',
            '-y', '0.4',
            '-z', '0.2'
        ],
        output='screen'
    )

    # RViz2
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        parameters=[
            {'use_sim_time': True}
        ],
        arguments=['-d', rviz_config],
        output='screen'
    )

    # ROS-Gazebo bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        parameters=[
            {
                'config_file': bridge_config,
                'use_sim_time': True
            }
        ],
        output='screen'
    )

    # Robot State Publisher
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            robot_description,
            {'use_sim_time': True}
        ],
        remappings=[
            ('/tf', 'tf'),
            ('/tf_static', 'tf_static')
        ]
    )

    ekf_node = Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[
                os.path.join(pkg_path, 'config', 'ekf.yaml'),
                {'use_sim_time': True},
                 ]
        )

    return LaunchDescription([
        gazebo_resource_path,
        gazebo,
        spawn,
        rviz,
        bridge,
        rsp,
        ekf_node
    ])