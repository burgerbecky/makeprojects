#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration file on how to build and clean projects in a specific folder.

This file is parsed by the cleanme, buildme, rebuildme and makeprojects
command line tools to clean, build and generate project files.

"""

## \package makeprojects.build_rules

from __future__ import absolute_import, print_function, unicode_literals

## Default build function list, priority / entrypoint
BUILD_LIST = (
    #(1, 'prebuild'),
    (40, 'build_rules'),
    #(99, 'post_build')
)

########################################


def clean_rules(working_directory, root=True):
    """
    Called by ``cleanme``.

    When the command ``cleanme`` is executed, it will call this
    function for all behavior for cleaning the work folder.

    The parameter working_directory is required, and if it has no default
    parameter, this function will only be called with the folder that this
    file resides in. If there is a default parameter of ``None``, it will be called with
    any folder that cleanme is invoked on. If the default parameter is a directory, this
    function will only be called if that directory is desired for cleaning.

    The optional parameter of root alerts cleanme if subsequent processing of other
    build_rules files is needed or if set to have a default parameter of True, processing
    will end once the call to clean_rules() is completed.

    Arg:
        working_directory: Directory for this function to clean
        root: If set to True, exit cleaning upon completion of this function
    Returns:
        Zero on no error, non-zero on error

    """

    # Call functions to delete files and / or folders
    # Examples are as follows

    # Remove these directories
    # burger.clean_directories(
    #    working_directory,
    #    ('Release', 'Debug', 'temp', '*_Data', '* Data', '__pycache__'),
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

    # Allow purging user data in XCode project directories
    # burger.clean_xcode(working_directory)

    # Purge data for setup.py
    # burger.clean_setup_py(working_directory)

    # Return error code or zero if no errors
    return 0

########################################


def build_rules(working_directory):
    """
    Called by ``buildme``.

    When the command ``buildme`` is executed, it will call this
    function for building the code / data in this working_directory.

    The parameter working_directory is required, and if it has no default
    parameter, this function will only be called with the folder that this
    file resides in. If there is a default parameter of ``None``, it will be called with
    any folder that buildme is invoked on.

    Arg:
        working_directory: Directory for this function to build.
    Returns:
        Zero on no error, non-zero on error.
    """
    return 0

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
