########################################################################
# CMake configuration
########################################################################
CMAKE_MINIMUM_REQUIRED(VERSION 2.6)
PROJECT(praxyk C CXX)
ENABLE_TESTING()

SET(praxyk_VERSION_MAJOR 0)
SET(praxyk_VERSION_MINOR 0)
SET(praxyk_VERSION_PATCH 1)

SET(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake/Modules;${CMAKE_MODULE_PATH}")

########################################################################
# Search for dependencies here
########################################################################
FIND_PACKAGE(CLANDMARK REQUIRED)
FIND_PACKAGE(Tesseract REQUIRED)
FIND_PACKAGE(MLPack REQUIRED)
FIND_PACKAGE(LibXml2 2.6.0 REQUIRED)
FIND_PACKAGE(OpenCV REQUIRED)

FIND_PACKAGE(OpenMP)
IF(OPENMP_FOUND)
    SET(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
ELSE(OPENMP_FOUND)
    SET(USE_OPENMP OFF)
ENDIF(OPENMP_FOUND)

########################################################################
# Global flags
########################################################################
IF(CMAKE_COMPILER_IS_GNUCXX OR "${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")
    SET(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -fvisibility=hidden")
    SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -fvisibility=hidden -std=c++11")
ENDIF(CMAKE_COMPILER_IS_GNUCXX OR "${CMAKE_CXX_COMPILER_ID}" STREQUAL "Clang")

########################################################################
# Create uninstall target
########################################################################
CONFIGURE_FILE(
    ${CMAKE_SOURCE_DIR}/cmake/cmake_uninstall.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake
@ONLY)

ADD_CUSTOM_TARGET(uninstall
    ${CMAKE_COMMAND} -P ${CMAKE_CURRENT_BINARY_DIR}/cmake_uninstall.cmake
)

####################################################################
# Set install subdirectories
####################################################################
IF(NOT DEFINED LIB_SUFFIX AND REDHAT AND CMAKE_SYSTEM_PROCESSOR MATCHES "64$")
    SET(LIB_SUFFIX 64)
ENDIF()
SET(LIB_SUFFIX ${LIB_SUFFIX} CACHE STRING "lib directory suffix")
SET(RUNTIME_DIR bin)
SET(LIBRARY_DIR lib${LIB_SUFFIX})
SET(INCLUDE_DIR include)
SET(PKG_DATA_DIR share/praxyk)
SET(DOCS_DIR share/doc/praxyk)

ADD_SUBDIRECTORY(include)
ADD_SUBDIRECTORY(lib)
ADD_SUBDIRECTORY(python)
ADD_SUBDIRECTORY(tests)

####################################################################
# Install CLandmark trained data
####################################################################
SET(clandmark_data
    ${CMAKE_SOURCE_DIR}/Praxyk-data/clandmark/clandmark_model.xml
    ${CMAKE_SOURCE_DIR}/Praxyk-data/clandmark/haarcascade_frontalface_alt.xml
)
INSTALL(
    FILES ${clandmark_data}
    DESTINATION ${PKG_DATA_DIR}/clandmark
)

####################################################################
# Install MLPack trained data
####################################################################
SET(mlpack_data
    ${CMAKE_SOURCE_DIR}/Praxyk-data/mlpack/features.txt
    ${CMAKE_SOURCE_DIR}/Praxyk-data/mlpack/training.csv

)
INSTALL(
    FILES ${mlpack_data}
    DESTINATION ${PKG_DATA_DIR}/mlpack
)

####################################################################
# Install CLandmark trained data
####################################################################
SET(tesseract_data
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.cube.bigrams
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.cube.fold
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.cube.lm
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.cube.nn
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.cube.params
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.cube.size
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.cube.word-freq
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.tesseract_cube.nn
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.traineddata
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.user-patterns
    ${CMAKE_SOURCE_DIR}/Praxyk-data/tessdata/eng.user-words
)
INSTALL(
    FILES ${tesseract_data}
    DESTINATION ${PKG_DATA_DIR}/tessdata
)

####################################################################
# Final Display
####################################################################
MESSAGE(STATUS "")
MESSAGE(STATUS "Building Praxyk - POD Library.")
MESSAGE(STATUS " - Build type: ${CMAKE_BUILD_TYPE}")
MESSAGE(STATUS " - Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
MESSAGE(STATUS "")
