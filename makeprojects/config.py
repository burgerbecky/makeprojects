#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2023 by Rebecca Ann Heineman becky@burgerbecky.com
#
# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

"""
Package that reads, parses and processes the configuration file

@package makeprojects.config

@var makeprojects.config._XCODEPROJECT_FILE
The filename project.pbxproj

@var makeprojects._XCODEPROJ_MATCH
Match *.xcodeproj

@var makeprojects._HLSL_MATCH
Match *.hlsl

@var makeprojects._GLSL_MATCH
Match *.glsl

@var makeprojects._X360SL_MATCH
Match *.x360sl

@var makeprojects._VITACG_MATCH
Match *.vitacg

@var makeprojects._MAKEFILE_MATCH
Match *.mak

@var makeprojects.config.BUILD_RULES_PY
build_rules.py file to detect secondly

@var makeprojects.config._BUILD_RULES_VAR
BUILD_RULES_PY location environment variable

@var makeprojects.config.USER_HOME
Location of the user's home directory

@var makeprojects.config.PROJECTS_HOME
Location of makeprojects home directory if redirected

@var makeprojects.config.DEFAULT_BUILD_RULES
Full pathname of the configuration file
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
from shutil import copyfile
from re import compile as re_compile
from burger import get_windows_host_type

# "project.pbxproj"
_XCODEPROJECT_FILE = "project.pbxproj"

# Match *.xcodeproj
_XCODEPROJ_MATCH = re_compile("(?is).*\\.xcodeproj\\Z")

# Match *.hlsl
_HLSL_MATCH = re_compile("(?is).*\\.hlsl\\Z")

# Match *.glsl
_GLSL_MATCH = re_compile("(?is).*\\.glsl\\Z")

# Match *.x360sl
_X360SL_MATCH = re_compile("(?is).*\\.x360sl\\Z")

# Match *.vitacg
_VITACG_MATCH = re_compile("(?is).*\\.vitacg\\Z")

# Match *.mak
_MAKEFILE_MATCH = re_compile("(?is).*\\.mak\\Z")

# build_rules.py file to detect secondly
BUILD_RULES_PY = "build_rules.py"

# BUILD_RULES_PY location environment variable
_BUILD_RULES_VAR = "BUILD_RULES"

# Location of the user's home directory
USER_HOME = os.path.expanduser("~")

if "MAKE_PROJECTS_HOME" in os.environ:
    # Location of makeprojects home directory if redirected
    PROJECTS_HOME = os.environ["MAKE_PROJECTS_HOME"]
else:
    PROJECTS_HOME = USER_HOME

########################################


def save_default(working_directory=None, destinationfile=BUILD_RULES_PY):
    """
    Calls the internal function to save a default .projectsrc file

    Given a pathname, create and write out a default .projectsrc file
    that can be used as input to makeprojects to generate project files.

    Args:
        working_directory: Directory to save the destination file
        destinationfile: Pathname of where to save the default configuation file
    Returns:
        0 if no error, an error code if the file couldn't be saved.
    """

    # If the destination is not an absolute path...
    if not os.path.isabs(destinationfile):

        # Prepend the working directory
        if not working_directory:
            working_directory = os.getcwd()

        # Create the path to store the configuration file
        destinationfile = os.path.join(working_directory, destinationfile)

    # Get the source file path
    src = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), BUILD_RULES_PY)

    # Copy the file
    try:
        copyfile(src, destinationfile)
    except OSError as error:
        print(error)
        return 10

    return 0

########################################


def find_default_build_rules():
    """
    Search for the build_rules.py file.

    Scan for the build_rules.py file starting from the current working directory
    and search downwards until the root directoy is it. If not found, search in
    the user's home directory or for linux/macOS, in /etc

    Returns:
        Pathname of the configuration file, or None if no file was found.
    """

    locations = []
    # See if there's an environment variable pointing to a file
    if _BUILD_RULES_VAR in os.environ and os.path.exists(
            os.environ[_BUILD_RULES_VAR]):
        locations.append(os.environ[_BUILD_RULES_VAR])

    # If "~" doesn't expand or /root, use the current folder
    if USER_HOME not in ("~", "/root"):
        # Check the user's home folder
        locations.append(os.path.join(USER_HOME, BUILD_RULES_PY))
        locations.append(os.path.join(USER_HOME, ".config", BUILD_RULES_PY))

    # If not found, use /etc/build_rules.py for system globals on non
    # windows platforms
    if not get_windows_host_type():
        locations.append("/etc/" + BUILD_RULES_PY)

    # Try the locations until there's a hit
    for result in locations:
        if os.path.isfile(result):
            return result

    # Use the one built into makeprojects
    return os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)),
        BUILD_RULES_PY)


# Full pathname of the default configuration file
DEFAULT_BUILD_RULES = find_default_build_rules()
