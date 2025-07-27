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

from uuid import NAMESPACE_DNS, UUID
from hashlib import md5
from burger import is_string, convert_to_windows_slashes

from .validators import VSStringProperty
from .enums import IDETypes, FileTypes, PlatformTypes, ProjectTypes, \
    source_file_detect
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

    # Easy test, use relative indexing
    if pathname.startswith("."):
        return VSStringProperty("RelativePath", pathname)

    # VS 2003 doesn't support FileName, so force relative
    # Also 2005/2008 only supports RelativePath if it's a source
    # code filename
    if ide is IDETypes.vs2003:

        # Check if it's a full path
        if len(pathname) < 2 or pathname[1] != ":":

            # Prepend dot slash
            pathname = ".\\" + pathname
        return VSStringProperty("RelativePath", pathname)

    # VS 2005/2008
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

########################################


def create_copy_file_script(source_file, dest_file, perforce):
    """
    Create a batch file to copy a single file.

    Create a list of command lines to copy a file from source_file to
    dest_file with perforce support.

    This is an example of the Windows batch file. The lines for the
    tool ``p4`` are added if perforce=True.

    ```bash
    p4 edit dest_file
    copy /Y source_file dest_file
    p4 revert -a dest_file
    ```

    Args:
        source_file: Pathname to the source file
        dest_file: Pathname to where to copy source file
        perforce: True if perforce commands should be generated.

    Returns:
        List of command strings for Windows Command shell.

    See Also:
        create_deploy_script
    """

    command_list = []

    # Check out the file
    if perforce:
        # Note, use ``cmd /c``` so if the call fails, the batch file will
        # continue
        command_list.append("cmd /c p4 edit \"{}\"".format(dest_file))

    # Perform the copy
    command_list.append(
        "copy /Y \"{}\" \"{}\"".format(source_file, dest_file))

    # Revert the file if it hasn't changed
    if perforce:
        command_list.append(
            "cmd /c p4 revert -a \"{}\"".format(dest_file))

    return command_list

########################################


def create_deploy_script(configuration):
    """
    Create a deployment batch file if needed.

    If an attribute of ``deploy_folder`` exists, a batch file
    will be returned that has the commands to copy the output file
    to the folder named in ``deploy_folder``.

    Two values are returned, the first is the command description
    suitable for Visual Studio Post Build and the second is the batch
    file string to perform the file copy. Both values are set to None
    if ``deploy_folder`` is empty.

    Note:
        If the output is ``project_type`` of Tool, the folder will have
        cpu name appended to it and any suffix stripped.

    ```bash
    mkdir final_folder
    p4 edit dest_file
    copy /Y source_file dest_file
    p4 revert -a dest_file
    ```

    Args:
        configuration: Configuration record.
    Returns:
        None, None or description and batch file string.

    See Also:
        create_copy_file_script
    """

    # Is there an override?
    post_build = configuration.get_chained_value("post_build")
    if post_build:
        # Return the tuple, message, then command
        return post_build

    deploy_folder = configuration.deploy_folder

    # Don't deploy if no folder is requested.
    if not deploy_folder:
        return None, None

    # Ensure it's the correct slashes and end with a slash
    deploy_folder = convert_to_windows_slashes(deploy_folder, True)

    # Get the project and platform
    project_type = configuration.project_type
    platform = configuration.platform
    perforce = configuration.get_chained_value("perforce")

    # Determine where to copy and if pdb files are involved
    if project_type.is_library():
        deploy_name = "$(TargetName)"
    else:
        # For executables, use ProjectName to strip the suffix
        deploy_name = "$(ProjectName)"

        # Windows doesn't support fat files, so deploy to different
        # folders for tools
        if project_type is ProjectTypes.tool:
            item = get_cpu_folder(platform)
            if item:
                deploy_folder = deploy_folder + item + "\\"

    # Create the batch file
    # Make sure the destination directory is present
    command_list = ["mkdir \"{}\" 2>nul".format(deploy_folder)]

    # Copy the executable
    command_list.extend(
        create_copy_file_script(
            "$(TargetPath)",
            "{}{}$(TargetExt)".format(deploy_folder, deploy_name),
            perforce))

    # Copy the symbols on Microsoft platforms
    # if platform.is_windows() or platform.is_xbox():
    #    if project_type.is_library() or configuration.debug:
    #       command_list.extend(
    #           create_copy_file_script(
    #              "$(TargetDir)$(TargetName).pdb",
    #               "{}{}.pdb".format(deploy_folder, deploy_name),
    #               perforce))

    return "Copying $(TargetFileName) to {}".format(
        deploy_folder), "\n".join(command_list) + "\n"
