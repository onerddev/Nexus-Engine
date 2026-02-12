cmake_minimum_required(VERSION 3.20)
project(NexusEngine LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=native -Wall -Wextra")

# Find required packages
find_package(Threads REQUIRED)
find_package(OpenMP REQUIRED)

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Core library
file(GLOB CORE_SOURCES "src/*.cpp")
add_library(nexus_core SHARED ${CORE_SOURCES})
target_link_libraries(nexus_core PUBLIC Threads::Threads OpenMP::OpenMP_CXX)

# Test executable
file(GLOB TEST_SOURCES "tests/*.cpp")
add_executable(nexus_test ${TEST_SOURCES})
target_link_libraries(nexus_test PRIVATE nexus_core)

# Install
install(TARGETS nexus_core
        LIBRARY DESTINATION lib
        ARCHIVE DESTINATION lib)
install(DIRECTORY include/ DESTINATION include/nexus)
