cmake_minimum_required(VERSION 3.10)
project(bkg2d C)

set(CMAKE_C_STANDARD 11)

include_directories(include)

# bkg2d CLI tool
add_executable(bkg2d
    src/bkg2d.c
    src/bkg2d_main.c
)
target_link_libraries(bkg2d m)

# pst_background static library
add_library(pst_background STATIC
    src/pst_background.c
)
target_include_directories(pst_background PUBLIC include)
target_link_libraries(pst_background m)
