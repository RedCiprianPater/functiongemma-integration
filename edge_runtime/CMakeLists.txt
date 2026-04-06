cmake_minimum_required(VERSION 3.16)
project(FunctionGemmaEdgeRuntime VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Options
option(USE_GPU "Enable GPU acceleration" OFF)
option(BUILD_TESTS "Build unit tests" ON)
option(BUILD_EXAMPLES "Build example applications" ON)

# Find packages
find_package(Threads REQUIRED)

# TensorFlow Lite
# In production, use FetchContent or find_package
set(TFLITE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/tensorflow-lite" CACHE PATH "TensorFlow Lite directory")

if(NOT EXISTS ${TFLITE_DIR})
    message(WARNING "TensorFlow Lite not found at ${TFLITE_DIR}. Please set TFLITE_DIR.")
    # Create stub for compilation without TFLite
    add_definitions(-DNO_TFLITE)
endif()

# Source files
set(SOURCES
    litert_runtime/model_loader.cc
    litert_runtime/inference_engine.cc
    litert_runtime/function_parser.cc
)

set(HEADERS
    litert_runtime/model_loader.h
    litert_runtime/inference_engine.h
    litert_runtime/function_parser.h
)

# Create library
add_library(functiongemma_runtime STATIC ${SOURCES} ${HEADERS})

target_include_directories(functiongemma_runtime
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${TFLITE_DIR}/include
)

if(USE_GPU AND NOT NO_TFLITE)
    target_compile_definitions(functiongemma_runtime PRIVATE USE_GPU)
    target_link_libraries(functiongemma_runtime
        ${TFLITE_DIR}/lib/libtensorflowlite_gpu_delegate.so
    )
endif()

target_link_libraries(functiongemma_runtime
    Threads::Threads
    ${CMAKE_DL_LIBS}
)

if(NOT NO_TFLITE)
    target_link_libraries(functiongemma_runtime
        ${TFLITE_DIR}/lib/libtensorflow-lite.so
    )
endif()

# Examples
if(BUILD_EXAMPLES)
    add_executable(example_inference examples/example_inference.cc)
    target_link_libraries(example_inference functiongemma_runtime)
    
    add_executable(example_voice_control examples/example_voice_control.cc)
    target_link_libraries(example_voice_control functiongemma_runtime)
endif()

# Tests
if(BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# Installation
install(TARGETS functiongemma_runtime
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
)

install(FILES ${HEADERS}
    DESTINATION include/functiongemma
)

# Print configuration
message(STATUS "")
message(STATUS "FunctionGemma Edge Runtime Configuration:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  GPU Support: ${USE_GPU}")
message(STATUS "  Build Tests: ${BUILD_TESTS}")
message(STATUS "  Build Examples: ${BUILD_EXAMPLES}")
message(STATUS "  TensorFlow Lite: ${TFLITE_DIR}")
message(STATUS "")
