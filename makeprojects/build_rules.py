#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Describe how to handle building this folder
"""

from __future__ import absolute_import, print_function, unicode_literals

# import burger

## Top-most build_rules.py
ROOT = True

def clean_rules(working_directory):
    """
    When the command 'cleanme' is executed, it will call this
    function for all behavior for cleaning the work folder
    """

    # Examples are as follows

    # Remove these directories
    # burger.clean_directories(
    #    working_directory,
    #    ('temp', '*_Data', '* Data', '__pycache__'),
    #    recursive=False)

    # Recursively remove files
    # burger.clean_files(
    #    working_directory,
    #    ('.DS_Store', '*.suo', '*.user', '*.ncb', '*.err', '*.sdf', '*.layout.cbTemp',
    #     '*.VC.db', '*.pyc', '*.pyo'),
    #    recursive=False)

    # Check if the directory has a codeblocks project file and clean
    # codeblocks extra files
    # burger.clean_codeblocks(working_directory)

    # Allow purging user data in XCode projects
    # burger.clean_xcode(working_directory)

    # Purge data for setup.py
    # burger.clean_setup_py(working_directory)

    # Return error code or zero if no errors
    return 0


# Files to build
# [build]
# norecurse = temp, bin, appfolder, *.xcodeproj, *_Data, '* Data'
# watcom = makefile, *.wmk
# doxygen = doxyfile
# makerez = *.rezscript
# slicer = *.slicerscript
# codeblocks = *.cbp
# codewarrior = *.mcp

# Defaults for generating projects
# [project]
# project = tool
# configurations = Debug, Internal, Release
# deploydirectory =
# deploydirectory_enable = False
# defines = NDEBUG
# optimization = 4
# linktimecode = False

# Debug|defines = _DEBUG
# Debug|optimization = 0
# Internal|defines = _DEBUG

# windows+defines = WIN32_LEAN_AND_MEAN, _WINDOWS
# win32+defines = WIN32
# win64+defines = WIN64
# maccarbon+defines = TARGET_API_MAC_CARBON=1
# win32|deploydirectory = $(BURGER_SDKS)\window\bin\x86
# win64|deploydirectory = $(BURGER_SDKS)\window\bin\x64
# linux|deploydirectory = $(BURGER_SDKS)\linux\bin
# macosx|deploydirectory = $(BURGER_SDKS)\macosx\bin
