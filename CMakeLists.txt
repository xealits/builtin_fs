cmake_minimum_required (VERSION 3.23)

project(builtin_fs
        VERSION 0.1
        DESCRIPTION "a generated bunch of binaries with file contents")

if (NOT DEFINED CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 23)
endif()

set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

message(STATUS "${PROJECT_NAME} ${nesting_spaces}> configuring via a bootstrap CMakeLists.txt")

file(GLOB SUBDIRS LIST_DIRECTORIES true RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} ${CMAKE_CURRENT_SOURCE_DIR}/*)
foreach(subdir_name ${SUBDIRS})
  set(subdir_path ${CMAKE_CURRENT_SOURCE_DIR}/${subdir_name})

  if(${subdir_name} STREQUAL "example")
    continue()
  endif()

  if(NOT IS_DIRECTORY ${subdir_path})
    continue()
  endif()

  if(NOT EXISTS "${subdir_path}/CMakeLists.txt")
    continue()
  endif()

  message(STATUS "${PROJECT_NAME} ${nesting_spaces}> adding a builtin_fs root at ${subdir_path}")
  add_subdirectory(${subdir_path})
endforeach()
