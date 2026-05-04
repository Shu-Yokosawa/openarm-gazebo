cmake_minimum_required(VERSION 3.8)
project(openarm_bringup)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS scripts/scene_setup.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
