#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Project file generator subroutines for Microsoft Visual Studio 2003-2008.

This module contains classes needed to generate project files intended for use
by Microsoft's Visual Studio 2003, 2005 and 2008.

@package makeprojects.visual_studio_utils

"""

from __future__ import absolute_import, print_function, unicode_literals

from burger import is_string

from .validators import VSStringProperty
from .enums import IDETypes, FileTypes, PlatformTypes, source_file_detect

########################################


def get_path_property(ide, pathname):
    """
    If a path is relative, return the proper object

    Check if a pathname starts with a ".", which means it's relative to the
    project. If so, return a RelativePath string, otherwise return a FileName
    string. Special case for Visual Studio 2003, it only accepts
    ``RelativePath`` as a parameter

    Args:
        ide: enums.IDETypes of the IDE being generated for.
        pathname: Pathname to test.

    Returns:
        validators.VSStringProperty of type RelativePath or FileName
    """

    if pathname.startswith(".") or ide is IDETypes.vs2003:
        return VSStringProperty("RelativePath", pathname)
    return VSStringProperty("FileName", pathname)

########################################


def get_toolset_version(ide):
    """
    Get the toolset version for the Visual Studio version

    Each version of Visual Studio uses a toolset version specific
    to that version. Return the version number for the vcxproj file.

    Strings returned are "4.0", "12.0", "14.0" and "15.0".

    Args:
        ide: enums.IDETypes of the IDE being generated

    Returns:
        String of the toolset version for the ide
    """

    # VS 2003 to 2012
    if ide < IDETypes.vs2013:
        version = "4.0"

    # VS 2013
    elif ide < IDETypes.vs2015:
        version = "12.0"

    # VS 2015
    elif ide < IDETypes.vs2017:
        version = "14.0"

    # VS 2017-2022
    else:
        version = "15.0"
    return version

########################################


def convert_file_name_vs2010(item):
    r"""
    Convert macros from to Visual Studio 2003-2008

    This table shows the conversions

    | Visual Studio 2010+ | 2003-2008 |
    | ------------------- | --------- |
    | %(RootDir)%(Directory) | \$(InputDir) |
    | %(FileName) | \$(InputName) |
    | %(Extension) | \$(InputExt) |
    | %(FullPath) | \$(InputPath) |
    | %(Identity) | \$(InputPath) |

    Args:
        item: Filename string

    Returns:
        String with converted macros
    """

    if is_string(item):
        item = item.replace("%(RootDir)%(Directory)", "$(InputDir)")
        item = item.replace("%(FileName)", "$(InputName)")
        item = item.replace("%(Extension)", "$(InputExt)")
        item = item.replace("%(FullPath)", "$(InputPath)")
        item = item.replace("%(Identity)", "$(InputPath)")
    return item

########################################


def wiiu_props(project):
    """
    If the project is for WiiU, check if there are assembly files.

    If there are assembly files, add the Nintendo supplied props file for
    assembly language support.

    Note:
        This assumes that the official WiiU SDK from Nintendo is installed
        on the machine that will build this project file.

    Args:
        project: Project to check
    """

    # Check if WiiU is a configuration
    for configuration in project.configuration_list:
        if configuration.platform is PlatformTypes.wiiu:

            # Are there any assembly source files in the project?
            if source_file_detect(project.codefiles, FileTypes.s):
                project.vs_props.append(
                    "$(VCTargetsPath)\\BuildCustomizations\\cafe2_asm.props")
                project.vs_targets.append(
                    "$(VCTargetsPath)\\BuildCustomizations\\cafe2_asm.targets")
            break

########################################


def add_masm_support(project):
    """
    If the project is has assembly files, add the props files

    This function works for Visual Studio 2003-2022.

    Note:
        * Visual Studio 2003 only supports x86 files
        * Visual Studio 2005-2015 only support x86 and x64 files
        * Visual Studio 2017+ support arm, arm64, x86, and x64 files

    Args:
        project: Project to check
    """
    # Are there any assembly source files in the project?
    if source_file_detect(project.codefiles, (FileTypes.x86, FileTypes.x64)):

        # Add support for masm on VS 2003-2008
        project.vs_rules.append("masm.rules")

        # Add support for masm on VS 2010 and beyond
        project.vs_props.append(
            "$(VCTargetsPath)\\BuildCustomizations\\masm.props")
        project.vs_targets.append(
            "$(VCTargetsPath)\\BuildCustomizations\\masm.targets")

    # Add props for ARM assembly (Only supported by VS 2017 or higher)
    if project.ide >= IDETypes.vs2017:
        if source_file_detect(
                project.codefiles, (FileTypes.arm, FileTypes.arm64)):
            # Add support for masm on VS 2010 and beyond
            project.vs_props.append(
                "$(VCTargetsPath)\\BuildCustomizations\\marmasm.props")
            project.vs_targets.append(
                "$(VCTargetsPath)\\BuildCustomizations\\marmasm.targets")
