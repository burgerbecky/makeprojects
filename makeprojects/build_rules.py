#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Describe how to handle building this folder
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import burger

## Top-most build_rules.py
ROOT = True

## Match *.cbp
_CODEBLOCKS_MATCH = re.compile('.*\\.cbp\\Z(?ms)')

## Match *.py
_PYTHON_MATCH = re.compile('.*\\.py\\Z(?ms)')


def clean_rules(working_directory):
    """
    When the command 'cleanme' is executed, it will call this
    function for all behavior for cleaning the work folder
    """

    burger.clean_directories(working_directory, ('appfolder',
                                                 'temp',
                                                 'ipch',
                                                 'bin',
                                                 '.vs',
                                                 '*_Data',
                                                 '* Data',
                                                 '__pycache__'))

    burger.clean_files(working_directory, ('.DS_Store',
                                           '*.suo',
                                           '*.user',
                                           '*.ncb',
                                           '*.err',
                                           '*.sdf',
                                           '*.layout.cbTemp',
                                           '*.VC.db',
                                           '*.pyc',
                                           '*.pyo'))

    # Delete the codewarrior config file
    if burger.get_windows_host_type():
        burger.delete_file(os.path.expandvars(
            "${LOCALAPPDATA}\\Metrowerks\\default.cww"))

    # If Doxygen was found using this directory, clean up
    if os.path.isfile(os.path.join(working_directory, 'Doxyfile')):
        burger.clean_files(
            working_directory,
            ('doxygenerrors.txt',
             '*.chm',
             '*.chw',
             '*.tmp'),
            recursive=True)

    # Check if the directory has a codeblocks project file and clean
    # codeblocks extra files
    list_dir = os.listdir(working_directory)
    for item in list_dir:
        if _CODEBLOCKS_MATCH.match(item):
            file_name = os.path.join(working_directory, item)
            if os.path.isfile(file_name):
                burger.clean_files(working_directory, ('*.depend', '*.layout'))
                break

    # Allow purging user data in XCode projects
    for item in list_dir:
        if item.endswith('.xcodeproj'):
            file_name = os.path.join(working_directory, item)
            if os.path.isdir(file_name):
                burger.clean_files(file_name, ('*.mode1v3', '*.pbxuser'))
                burger.clean_directories(file_name, ('xcuserdata', 'project.xcworkspace'))

    # Purge python folders
    for item in list_dir:
        if _PYTHON_MATCH.match(item):
            file_name = os.path.join(working_directory, item)
            if os.path.isfile(file_name):
                burger.clean_directories(working_directory, ('dist', 'build', '_build',
                                                             '.tox', '.pytestcache', '*.egg-info'))
                break

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
