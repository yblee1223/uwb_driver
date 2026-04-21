cmake_minimum_required(VERSION 3.8)
project(uwb_driver)

find_package(ament_cmake REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/UwbRange.msg"
  DEPENDENCIES std_msgs
)

install(
  PROGRAMS
    scripts/uwb_serial_node.py
    scripts/uwb_parser.py
    scripts/uwb_logger_node.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
