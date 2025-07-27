#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2022-2025 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

"""
Sub file for makeprojects.
Subroutines for Apple Computer XCode projects

@package makeprojects.xcode_utils
This module contains classes needed to generate
project files intended for use by Apple's XCode IDE

@var makeprojects.xcode_utils.TEMP_EXE_NAME
Build executable pathname

@var makeprojects.xcode_utils.PERFORCE_PATH
Path of the perforce executable

"""

# pylint: disable=useless-object-inheritance
# pylint: disable=consider-using-f-string
# pylint: disable=too-many-lines

from __future__ import absolute_import, print_function, unicode_literals

from ide_gen import xcode_calcuuid, JSONArray, JSONDict

# Build executable pathname
TEMP_EXE_NAME = "${CONFIGURATION_BUILD_DIR}/${EXECUTABLE_NAME}"

# Path of the perforce executable
PERFORCE_PATH = "/opt/local/bin/p4"

########################################


def get_sdk_root(solution):
    """
    Determine the main Xcode root sdk

    Args:
        solution: Solution object

    Returns:
        String of the Xcode SDKROOT
    """

    # Check if there is an override?
    for project in solution.project_list:
        for configuration in project.configuration_list:
            sdkroot = configuration.get_chained_value("xc_sdkroot")

            # Use the override
            if sdkroot:
                return sdkroot

    # Punt
    if solution.project_list[0].configuration_list[0].platform.is_ios():
        return "iphoneos"
    return "macosx"

########################################


class PBXShellScriptBuildPhase(JSONDict):
    """
    Each PBXShellScriptBuildPhase entry

    Attributes:
        files: JSONArray of files
    """

    def __init__(self, input_data, output, command):
        """
        Init PBXShellScriptBuildPhase

        Args:
            input_data: Input file references
            output: String for the output file that will be built
            command: Script to build
        """

        # Get the UUID
        uuid = xcode_calcuuid(
            "PBXShellScriptBuildPhase" + "".join(input_data) +
            output + command)

        # Init the parent
        JSONDict.__init__(self, uuid,"ShellScript",
                          uuid=uuid,
                          isa="PBXShellScriptBuildPhase")

        self.add_dict_entry("buildActionMask", "2147483647")

        # Internal files, if any
        files = JSONArray("files")
        self.files = files
        self.add_item(files)

        # Paths to input files
        input_paths = JSONArray("inputPaths", disable_if_empty=True)
        for item in input_data:
            input_paths.add_string_entry(item)
        self.add_item(input_paths)

        # Path to the output file
        output_paths = JSONArray("outputPaths")
        output_paths.add_string_entry(output)
        self.add_item(output_paths)

        # Always run
        self.add_dict_entry(
            "runOnlyForDeploymentPostprocessing", "0")

        # Path to the shell
        self.add_dict_entry("shellPath", "/bin/sh")

        # The actual script to run
        self.add_dict_entry("shellScript", "{}\\n".format(command))

        # Don't show the environment variables
        self.add_dict_entry("showEnvVarsInLog", "0")

########################################

def copy_tool_to_bin():
    """
    Create a PBXShellScriptBuildPhase to copy to bin

    Create a PBXShellScriptBuildPhase to take a binary tool file,
    append a suffix, and then copy it to a "bin" folder.

    Return:
        PBXShellScriptBuildPhase set up for the operation
    """

    # Get the input file
    input_data = [TEMP_EXE_NAME]

    # Store to bin folder with suffix
    output = ("${SRCROOT}/bin/${EXECUTABLE_PREFIX}${PRODUCT_NAME}"
              "${SUFFIX}${EXECUTABLE_SUFFIX}")

    # Create the bin folder, then perform the copy
    command = (
        "if [ ! -d ${{SRCROOT}}/bin ];"
        " then mkdir ${{SRCROOT}}/bin; fi\\n"
        "${{CP}} {0} {1}").format(TEMP_EXE_NAME, output)

    return PBXShellScriptBuildPhase(input_data, output, command)
