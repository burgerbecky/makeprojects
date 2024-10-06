#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Project file generator subroutines for Microsoft Visual Studio 2003-2008.

This module contains classes needed to generate project files intended for use
by Microsoft's Visual Studio 2003, 2005 and 2008.

@package makeprojects.visual_studio_utils

@var makeprojects.visual_studio_utils._PLATFORM_CPUS
Dict of platforms to maps to names

@sa makeprojects.visual_studio_utils.get_cpu_folder

@var makeprojects.visual_studio_utils._SLN_HEADERS
Internal list of Visual Studio headers for SLN files.

@var makeprojects.visual_studio_utils._SLN_POSTSOLUTION
UUIDs for postSolution SLN records
"""

from __future__ import absolute_import, print_function, unicode_literals

from burger import is_string

from .validators import VSStringProperty
from .enums import IDETypes, FileTypes, PlatformTypes, source_file_detect
from .util import iterate_configurations

# pylint: disable=consider-using-f-string

# Map platform CPUs to folder names
_PLATFORM_CPUS = {
    PlatformTypes.win32: "x86",
    PlatformTypes.win64: "x64",
    PlatformTypes.winarm32: "arm",
    PlatformTypes.winarm64: "arm64",
    PlatformTypes.winitanium: "ia64"
}

# Headers for each version of Visual Studio SLN files
_SLN_HEADERS = {
    IDETypes.vs2003: (
        "Microsoft Visual Studio Solution File, Format Version 8.00",
    ),
    IDETypes.vs2005: (
        "",
        "Microsoft Visual Studio Solution File, Format Version 9.00",
        "# Visual Studio 2005"),
    IDETypes.vs2008: (
        "",
        "Microsoft Visual Studio Solution File, Format Version 10.00",
        "# Visual Studio 2008"),
    IDETypes.vs2010: (
        "",
        "Microsoft Visual Studio Solution File, Format Version 11.00",
        "# Visual Studio 2010"),
    IDETypes.vs2012: (
        "",
        "Microsoft Visual Studio Solution File, Format Version 12.00",
        "# Visual Studio 2012"),
    IDETypes.vs2013: (
        "",
        "Microsoft Visual Studio Solution File, Format Version 12.00",
        "# Visual Studio 2013",
        "VisualStudioVersion = 12.0.31101.0",
        "MinimumVisualStudioVersion = 10.0.40219.1"),
    IDETypes.vs2015: (
        "",
        "Microsoft Visual Studio Solution File, Format Version 12.00",
        "# Visual Studio 14",
        "VisualStudioVersion = 14.0.25123.0",
        "MinimumVisualStudioVersion = 10.0.40219.1"),
    IDETypes.vs2017: (
        "",
        "Microsoft Visual Studio Solution File, Format Version 12.00",
        "# Visual Studio 15",
        "VisualStudioVersion = 15.0.28307.645",
        "MinimumVisualStudioVersion = 10.0.40219.1"),
    IDETypes.vs2019: (
        "",
        "Microsoft Visual Studio Solution File, Format Version 12.00",
        "# Visual Studio Version 16",
        "VisualStudioVersion = 16.0.28803.452",
        "MinimumVisualStudioVersion = 10.0.40219.1"),
    IDETypes.vs2022: (
        "",
        "Microsoft Visual Studio Solution File, Format Version 12.00",
        "# Visual Studio Version 17",
        "VisualStudioVersion = 17.1.32210.238",
        "MinimumVisualStudioVersion = 10.0.40219.1")
}

# VS 2017+ needs postSolution UUID
_SLN_POSTSOLUTION = {
    IDETypes.vs2017: "DD9C6A72-2C1C-45F2-9450-8BE7001FEE33",
    IDETypes.vs2019: "6B996D51-9872-4B32-A08B-EBDBC2A3151F",
    IDETypes.vs2022: "B6FA54F0-2622-4700-BD43-73EB0EBEFE41"
}

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

########################################


def get_cpu_folder(platform):
    """
    If the platform is a Windows type, return the CPU name

    Returns None, "x86", "x64", "arm", "arm64", or "ia64"

    Args:
        platform: enums.PlatformTypes to check
    Returns:
        None or platform CPU name.
    """

    return _PLATFORM_CPUS.get(platform, None)

########################################


def generate_solution_file(solution_lines, solution):
    """
    Serialize the solution file into a string array.

    This function generates SLN files for all versions of Visual Studio.
    It assumes the text file will be encoded using UTF-8 character encoding
    so the resulting file will be pre-pended with a UTF-8 Byte Order Mark (BOM)
    for Visual Studio 2005 or higher.

    Note:
        Byte Order Marks are not supplied by this function.

    Args:
        solution_lines: List to insert string lines.
        solution: Reference to the raw solution record
    Returns:
        Zero on success, non-zero on error.
    """

    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    # Save off the format header for the version of Visual Studio
    # being generated

    # Insert the header to the output stream
    header = _SLN_HEADERS.get(solution.ide)
    solution_lines.extend(header)

    # Output each project file included in the solution
    # This hasn't changed since Visual Studio 2003
    for project in solution.project_list:

        # Save off the project record
        solution_lines.append(
            ("Project(\"{{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}}\") "
             "= \"{}\", \"{}\", \"{{{}}}\"").format(
                 project.name,
                 project.vs_output_filename,
                 project.vs_uuid))

        # Write out the dependencies, if any
        if project.project_list or solution.ide < IDETypes.vs2005:
            solution_lines.append(
                "\tProjectSection(ProjectDependencies) = postProject")
            for dependent in project.project_list:
                solution_lines.append(
                    "\t\t{{{0}}} = {{{0}}}".format(
                        dependent.vs_uuid))
            solution_lines.append("\tEndProjectSection")
        solution_lines.append("EndProject")

    # Begin the Global record
    solution_lines.append("Global")

    # Visual Studio 2003 format is unique, write it out in its
    # own exporter

    if solution.ide is IDETypes.vs2003:

        # Only output if there are attached projects, if there are
        # no projects, there is no need to output platforms
        config_set = set()
        for configuration in iterate_configurations(solution):
            config_set.add(configuration.name)

        # List the configuration pairs (Like Xbox and Win32)
        solution_lines.append(
            "\tGlobalSection(SolutionConfiguration) = preSolution")

        for entry in sorted(config_set):
            # Since Visual Studio 2003 doesn't support
            # Platform/Configuration pairing,
            # it's faked with a space
            solution_lines.append("\t\t{0} = {0}".format(entry))
        solution_lines.append("\tEndGlobalSection")

        # List all of the projects/configurations
        solution_lines.append(
            "\tGlobalSection(ProjectConfiguration) = postSolution")
        for configuration in iterate_configurations(solution):
            # Using the faked Platform/Configuration pair used above,
            # create the appropriate pairs here and match them up.
            solution_lines.append(
                "\t\t{{{0}}}.{1}.ActiveCfg = {2}".format(
                    configuration.project.vs_uuid,
                    configuration.name,
                    configuration.vs_configuration_name))
            solution_lines.append(
                "\t\t{{{0}}}.{1}.Build.0 = {2}".format(
                    configuration.project.vs_uuid,
                    configuration.name,
                    configuration.vs_configuration_name))
        solution_lines.append("\tEndGlobalSection")

        # Put in stubs for these records.
        solution_lines.append(
            "\tGlobalSection(ExtensibilityGlobals) = postSolution")
        solution_lines.append("\tEndGlobalSection")

        solution_lines.append(
            "\tGlobalSection(ExtensibilityAddIns) = postSolution")
        solution_lines.append("\tEndGlobalSection")

    # All other versions of Visual Studio 2005 and later use this format
    # for the configurations
    else:

        if solution.project_list:
            # Write out the SolutionConfigurationPlatforms for all other
            # versions of Visual Studio

            solution_lines.append(
                "\tGlobalSection(SolutionConfigurationPlatforms) = preSolution")
            for configuration in iterate_configurations(solution):
                solution_lines.append(
                    "\t\t{0} = {0}".format(
                        configuration.vs_configuration_name))
            solution_lines.append("\tEndGlobalSection")

            # Write out the ProjectConfigurationPlatforms
            solution_lines.append(
                "\tGlobalSection(ProjectConfigurationPlatforms) = postSolution")

            for configuration in iterate_configurations(solution):
                solution_lines.append(
                    "\t\t{{{0}}}.{1}.ActiveCfg = {1}".format(
                        configuration.project.vs_uuid,
                        configuration.vs_configuration_name))
                solution_lines.append(
                    "\t\t{{{0}}}.{1}.Build.0 = {1}".format(
                        configuration.project.vs_uuid,
                        configuration.vs_configuration_name))

            solution_lines.append("\tEndGlobalSection")

        # Hide nodes section
        solution_lines.append(
            "\tGlobalSection(SolutionProperties) = preSolution")
        solution_lines.append("\t\tHideSolutionNode = FALSE")
        solution_lines.append("\tEndGlobalSection")

        # Is a postSolution required?
        uuid = _SLN_POSTSOLUTION.get(solution.ide, None)
        if uuid:
            solution_lines.append(
                "\tGlobalSection(ExtensibilityGlobals) = postSolution")
            solution_lines.append(
                "\t\tSolutionGuid = {" + uuid + "}")
            solution_lines.append("\tEndGlobalSection")

    # Close it up!
    solution_lines.append("EndGlobal")
    return 0
