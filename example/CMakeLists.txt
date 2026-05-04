cmake_minimum_required (VERSION 3.23)

project(builtin_fs_example
        VERSION 0.1
        DESCRIPTION "a small example of using builtin_fs in CMake")

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_subdirectory(my_builtin_fs)

add_executable(test test.cpp)
target_link_libraries(test PUBLIC my_builtin_fs__images)

