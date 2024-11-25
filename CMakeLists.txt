cmake_minimum_required(VERSION 3.5)

project(NussBar)

#-----------------------------------------------------------------------------
# Extension meta-information
# The extension doesn't exist yet - these links are invalid and will only work after the extension is published
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Modules/NussBar")
set(EXTENSION_CATEGORY "Preoperative Tools")
set(EXTENSION_CONTRIBUTORS "Akhil Deo")
set(EXTENSION_DESCRIPTION "This module calculates and outputs the ideal Nuss Bar given the patient's CT scan, markups indicating the location of the bar post-operative, and the desired bar length.")
set(EXTENSION_ICONURL "https://www.example.com/Slicer/Extensions/Nuss_Bar_Model_Generator.png")
set(EXTENSION_SCREENSHOTURLS "https://www.example.com/Slicer/Extensions/Nuss_Bar_Model_Generator/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(NussBar)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})

cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)
