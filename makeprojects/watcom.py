#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 1995-2024 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

"""
This module contains classes needed to generate
project files intended for use by Open Watcom
WMAKE 1.9 or higher

@package makeprojects.watcom

@var makeprojects.watcom.SUPPORTED_IDES
List of IDETypes the watcom module supports.

@var makeprojects.watcom._WATCOMFILE_MATCH
Regex for matching files with *.wmk

@var makeprojects.watcom._WMAKE_DO_NOTHING
String to do nothing in WMAKE
"""

# pylint: disable=consider-using-f-string
# pylint: disable=super-with-arguments
# pylint: disable=useless-object-inheritance
# pylint: disable=too-many-lines

from __future__ import absolute_import, print_function, unicode_literals

import os
from re import compile as re_compile
from burger import save_text_file_if_newer, encapsulate_path_linux, \
    convert_to_linux_slashes, convert_to_windows_slashes, where_is_watcom, \
    get_windows_host_type

try:
    from wslwinreg import convert_to_windows_path
except ImportError:
    pass

from .enums import FileTypes, ProjectTypes, PlatformTypes, IDETypes, \
    get_output_template
from .build_objects import BuildObject, BuildError
from .watcom_util import fixup_env, get_custom_list, get_output_list, \
    add_post_build, watcom_linker_system, get_obj_list, add_obj_list, \
    warn_if_invalid

# IDEs supported by this generator
SUPPORTED_IDES = (IDETypes.watcom,)

# Regex for matching *.wmk files
_WATCOMFILE_MATCH = re_compile("(?is).*\\.wmk\\Z")

# WMake command to never build a file
_WMAKE_DO_NOTHING = "\t@%null"

########################################


class BuildWatcomFile(BuildObject):
    """
    Class to build watcom make files

    Attribute:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority, configuration, verbose=False):
        r"""
        Class to handle watcom make files

        Args:
            file_name: Pathname to the \*.wmk to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
        """

        super(
            BuildWatcomFile,
            self).__init__(
            file_name,
            priority,
            configuration=configuration)
        self.verbose = verbose

    def build(self):
        """
        Build Watcom MakeFile.
        @details
        On Linux and Windows hosts, this function will invoke the ``wmake``
        tool to build the watcom make file.

        The PATH will be temporarily adjusted to include the watcom tools so
        wmake can find its shared libraries.

        The default target built is ``all``.

        Returns:
            List of BuildError objects
        """

        # Is Watcom installed?
        watcom_path = where_is_watcom(verbose=self.verbose)
        if watcom_path is None:
            file_name = self.file_name
            return BuildError(0, file_name,
                msg="{} requires Watcom to be installed to build!".format(
                    file_name))

        # Watcom requires the path set up so it can access link files
        exe_name = where_is_watcom("wmake", verbose=self.verbose)

        saved_path = os.environ["PATH"]
        if get_windows_host_type() or exe_name.endswith(".exe"):

            # Building for DOS/Windows needs the binnt and binw folders
            # in the path
            new_path = os.pathsep.join(
                (os.path.join(
                    watcom_path, "binnt"), os.path.join(
                        watcom_path, "binw")))
            file_name = convert_to_windows_path(self.file_name)

        else:
            # Linux uses the binl folder
            new_path = os.path.join(watcom_path, "binl")
            file_name = self.file_name

        # Make sure they are in the path
        os.environ["PATH"] = new_path + os.pathsep + saved_path

        # Set the configuration target
        cmd = [exe_name, "-e", "-h", "-f", file_name, self.configuration]

        # Iterate over the commands
        if self.verbose:
            print(" ".join(cmd))

        result = self.run_command(cmd, self.verbose)

        # Restore the path variable
        os.environ["PATH"] = saved_path

        # Return the error code
        return result

    ########################################

    def clean(self):
        """
        Delete temporary files.

        This function is called by ``cleanme`` to remove temporary files.

        On exit, return 0 for no error, or a non zero error code if there was an
        error to report. None if not implemented or not applicable.

        Returns:
            None if not implemented, otherwise an integer error code.
        """

        return self.build()

########################################


def match(filename):
    """
    Check if the filename is a type that this module supports

    Args:
        filename: Filename to match
    Returns:
        False if not a match, True if supported
    """

    return _WATCOMFILE_MATCH.match(filename)

########################################


def create_build_object(file_name, priority=50,
                 configurations=None, verbose=False):
    """
    Create BuildWatcomFile build records for every desired configuration

    Args:
        file_name: Pathname to the *.wmk to build
        priority: Priority to build this object
        configurations: Configuration list to build
        verbose: True if verbose output
    Returns:
        list of BuildWatcomFile classes
    """

    if not configurations:
        return [BuildWatcomFile(file_name, priority, "all", verbose)]

    results = []
    for configuration in configurations:
        results.append(
            BuildWatcomFile(
                file_name,
                priority,
                configuration,
                verbose))
    return results

########################################


def create_clean_object(file_name, priority=50,
                 configurations=None, verbose=False):
    """
    Create BuildWatcomFile build records for every desired configuration

    Args:
        file_name: Pathname to the *.wmk to build
        priority: Priority to build this object
        configurations: Configuration list to build
        verbose: True if verbose output
    Returns:
        list of BuildWatcomFile classes
    """

    if not configurations:
        return [BuildWatcomFile(file_name, priority, "clean", verbose)]

    results = []
    for configuration in configurations:

        # If clean is invoked, pass it through
        if configuration != "clean" and not configuration.startswith("clean_"):

            # Convert Release to clean_Release
            configuration = "clean_" + configuration

        results.append(
            BuildWatcomFile(file_name, priority, configuration, verbose))
    return results

########################################


def test(ide, platform_type):
    """ Filter for supported platforms

    Args:
        ide: IDETypes
        platform_type: PlatformTypes
    Returns:
        True if supported, False if not
    """

    # pylint: disable=unused-argument

    return platform_type in (
        PlatformTypes.win32, PlatformTypes.msdos4gw, PlatformTypes.msdosx32)

########################################


def generate(solution):
    """
    Create a project file for Watcom.

    Given a Solution object, create an appropriate Watcom WMAKE
    file to allow this project to build.

    Args:
        solution: Solution instance.

    Returns:
        Zero if no error, non-zero on error.
    """

    # Failsafe
    if solution.ide not in SUPPORTED_IDES:
        return 10

    # Perform sanity checks
    error = warn_if_invalid(solution)
    if error:
        return error

    # Create the output filename and pass it to the generator
    # so it can reference itself in make targets
    solution.watcom_filename = "{}{}{}.wmk".format(
        solution.name, solution.ide_code, solution.platform_code)

    # Create an instance of the generator
    exporter = WatcomProject(solution)

    # Output the actual project file
    watcom_lines = []
    error = exporter.generate(watcom_lines)
    if error:
        return error

    # Handle any post processing
    watcom_lines = solution.post_process(watcom_lines)

    # Save the file if it changed
    save_text_file_if_newer(
        os.path.join(solution.working_directory, solution.watcom_filename),
        watcom_lines,
        bom=False,
        perforce=solution.perforce,
        verbose=solution.verbose)
    return 0


########################################


class WatcomProject(object):
    """
    Root object for a Watcom IDE project file.

    Created with the name of the project, the IDE code
    the platform code (4gw, x32, win)

    Attributes:
        solution: Parent solution
        platforms: List of all platform types
        configuration_list: List of all configurations
        configuration_names: List of configuration names
        custom_list: List of custom built files
        output_list: List of custom output files
    """

    def __init__(self, solution):
        """
        Initialize the exporter.

        Args:
            solution: Parent solution.
        """

        # Init the platform list
        platforms = []

        # Init the list of custom rules
        custom_list = []

        self.solution = solution
        self.platforms = platforms
        self.configuration_list = []
        self.configuration_names = []

        # Process all the projects and configurations
        for project in solution.project_list:

            # Process the filename types supported by Open Watcom
            project.get_file_list(
                [FileTypes.h, FileTypes.cpp, FileTypes.c, FileTypes.x86,
                 FileTypes.hlsl, FileTypes.glsl, FileTypes.rc])

            # Keep a copy of the filenames for now
            codefiles = project.codefiles

            # Add to the master list
            self.configuration_list.extend(project.configuration_list)

            # Create sets of configuration names and projects
            for configuration in project.configuration_list:

                configuration.watcommake_name = configuration.name + \
                    configuration.platform.get_short_code()

                # Add only if not already present
                for item in self.configuration_names:
                    if configuration.name == item.name:
                        break
                else:
                    self.configuration_names.append(configuration)

                # Add platform if not already found
                if configuration.platform not in platforms:
                    platforms.append(configuration.platform)

                # Get the rule list
                rule_list = (configuration.custom_rules,
                    configuration.parent.custom_rules,
                    configuration.parent.parent.custom_rules)
                get_custom_list(custom_list, rule_list, codefiles)

        self.custom_list = custom_list
        self.output_list = get_output_list(custom_list)

    ########################################

    def write_header(self, line_list):
        """
        Write the header for a Watcom wmake file

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        line_list.extend([
            "#",
            "# Build " + self.solution.name + " with WMAKE",
            "# Generated with makeprojects.watcom",
            "#",
            "# This file requires the environment variable WATCOM set to the "
            "OpenWatcom",
            "# folder",
            "# Example: WATCOM=C:\\WATCOM",
            "#"]
        )
        return 0

    ########################################

    def write_test_variables(self, line_list):
        """
        Create tests for environment variables

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        # Scan all entries and make sure all duplicates are purged
        variable_list = set()

        for project in self.solution.project_list:

            # Create sets of configuration names and projects
            for configuration in project.configuration_list:
                variable_list.update(
                    configuration.get_unique_chained_list("env_variable_list"))

        # Anything found?
        if variable_list:
            line_list.extend((
                "",
                "#",
                "# Test for required environment variables",
                "#"
            ))
            for variable in sorted(variable_list):
                line_list.extend((
                    "",
                    "!ifndef %" + variable,
                    ("!error The environment variable {} "
                     "was not declared").format(variable),
                    "!endif"
                ))
        return 0

    ########################################

    def write_extensions(self, line_list):
        """
        Write the list of acceptable file extensions

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        line_list.extend([
            "",
            "#",
            "# Set the set of known files supported",
            "# Note: They are in the reverse order of building. .x86 is "
            "built first, then .c",
            "# until the .exe or .lib files are built",
            "#",
            "",
            ".extensions:",
            ".extensions: .exe .exp .lib .obj .cpp .c .x86 .i86 .h .res .rc",
        ])
        return 0

    ########################################

    def write_include_dlls(self, line_list):
        """
        Write the commands to include the DLLs for wmake

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        line_list.extend([
            "",
            "#",
            "# This speeds up the building process for Watcom because it keeps "
            "the apps in",
            "# memory and doesn't have to reload for every source file",
            "# Note: There is a bug that if the wlib app is loaded, "
            "it will not",
            "# get the proper WOW file if a full build is performed",
            "#",
            "# The bug is gone from Watcom 1.2",
            "#",
            "",
            "!ifdef %WATCOM",
            "!ifdef __LOADDLL__",
            "!loaddll wcc $(%WATCOM)/binnt/wccd",
            "!loaddll wccaxp $(%WATCOM)/binnt/wccdaxp",
            "!loaddll wcc386 $(%WATCOM)/binnt/wccd386",
            "!loaddll wpp $(%WATCOM)/binnt/wppdi86",
            "!loaddll wppaxp $(%WATCOM)/binnt/wppdaxp",
            "!loaddll wpp386 $(%WATCOM)/binnt/wppd386",
            "!loaddll wlink $(%WATCOM)/binnt/wlinkd",
            "!loaddll wlib $(%WATCOM)/binnt/wlibd",
            "!endif",
            "!endif"])
        return 0

    ########################################

    def write_output_list(self, line_list):
        """
        Output the list of object files to create.

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        line_list.extend([
            "",
            "#",
            "# Custom output files",
            "#",
            ""
        ])

        # Get a list of custom files
        output_list = self.output_list
        if not output_list:
            line_list.append("EXTRA_OBJS=")
            return 0

        colon = "EXTRA_OBJS= "
        for item in output_list:
            line_list.append(
                colon +
                convert_to_linux_slashes(
                    item) + " &")
            colon = "\t"

        # Remove the " &" from the last line
        line_list[-1] = line_list[-1][:-2]
        return 0

    ########################################

    def _write_phony_all(self, line_list):
        """
        Generate ``all`` symbolic target

        Args:
            line_list: List of lines of text generated.
        """

        target_list = []
        configuration_names = self.configuration_names
        for item in configuration_names:
            target_list.append(item.name)

        line_all = "all: " + " ".join(target_list) + " .SYMBOLIC"
        line_clean = "clean: " + \
            " ".join(["clean_" + x for x in target_list]) + " .SYMBOLIC"

        line_list.extend((
            "",
            "#",
            "# List the names of all of the final binaries to build and clean",
            "#",
            "",
            line_all,
            _WMAKE_DO_NOTHING,
            "",
            line_clean,
            _WMAKE_DO_NOTHING
        ))

    ########################################

    def _write_phony_configurations(self, line_list):
        """
        Generate symbolic configuration targets

        Args:
            line_list: List of lines of text generated.
        """

        # Only generate if there are configurations
        if self.configuration_names:
            line_list.extend((
                "",
                "#",
                "# Configurations",
                "#"
            ))

            platforms = self.platforms
            for configuration in self.configuration_names:
                target_list = []
                for platform in platforms:
                    target_list.append(
                        configuration.name +
                        platform.get_short_code())

                line_configuration = configuration.name + \
                    ": " + " ".join(target_list) + " .SYMBOLIC"
                line_clean = "clean_" + configuration.name + ": " + \
                    " ".join(["clean_" + x for x in target_list]) + \
                    " .SYMBOLIC"

                line_list.extend(("",
                                  line_configuration,
                                  _WMAKE_DO_NOTHING,
                                  "",
                                  line_clean,
                                  _WMAKE_DO_NOTHING
                                  ))

    ########################################

    def _write_phony_platforms(self, line_list):
        """
        Generate a list of platforms

        Args:
            line_list: List of lines of text generated.
        """

        # Only generate if there are platforms
        platforms = self.platforms
        if platforms:
            line_list.extend((
                "",
                "#",
                "# Platforms",
                "#"
            ))

            configuration_list = self.configuration_list
            for platform in platforms:

                short_code = platform.get_short_code()

                target_list = []
                for configuration in configuration_list:
                    target_list.append(
                        configuration.name +
                        short_code)

                line_platform = short_code + \
                    ": " + " ".join(target_list) + " .SYMBOLIC"
                line_clean = "clean_" + short_code + ": " + \
                    " ".join(["clean_" + x for x in target_list]) + \
                    " .SYMBOLIC"

                line_list.extend(("",
                                  line_platform,
                                  _WMAKE_DO_NOTHING,
                                  "",
                                  line_clean,
                                  _WMAKE_DO_NOTHING))

    ########################################

    def _write_phony_binaries(self, line_list):
        """
        Generate phony targets for binaries.

        Args:
            line_list: List of lines of text generated.
        """

        configuration_list = self.configuration_list
        if configuration_list:

            line_list.extend((
                "",
                "#",
                "# List of binaries to build or clean",
                "#"
            ))

            for configuration in configuration_list:
                template = get_output_template(
                    configuration.project_type, configuration.platform)

                platform_short_code = configuration.platform.get_short_code()
                target_name = configuration.name + platform_short_code
                bin_folder = self.solution.name + "wat" + \
                    platform_short_code[-3:] + configuration.short_code
                bin_name = template.format(bin_folder)

                # Instructions to build
                line_list.extend((
                    "",
                    target_name + ": .SYMBOLIC",
                    "\t@if not exist bin @mkdir bin",
   	                "\t@if not exist \"temp\\{0}\" @mkdir \"temp\\{0}\"".format(
   	                    bin_folder),
                    "\t@set CONFIG=" + configuration.name,
                    "\t@set TARGET=" + platform_short_code,
                    "\t@%make bin\\" + bin_name
                ))

                # Instructions to clean
                line_list.extend((
                    "",
                    "clean_" + target_name + ": .SYMBOLIC"
                ))

                # Optional custom outputs
                if self.output_list:
                    line_list.append("\t@rm -f $(EXTRA_OBJS)")

                line_list.extend((
                    "\t@if exist temp\\{0} @rmdir /s /q temp\\{0}".format(
                        bin_folder),
                    "\t@if exist bin\\{0} @del /q bin\\{0}".format(
                        bin_name),
                    # Test if the directory is empty, if so, delete the
                    # directory
                    "\t@-if exist bin @rmdir bin 2>NUL",
                    "\t@-if exist temp @rmdir temp 2>NUL"
                ))

    ########################################

    def write_all_targets(self, line_list):
        """
        Output all of the .SYMBOLIC targets.

        Create all of the targets, starting with all, and then all the
        configurations, followed by the clean targets.

        Args:
            line_list: List of lines of text generated.

        Returns:
            Zero.
        """

        # Save the "All" targets
        self._write_phony_all(line_list)

        # Save the configuration targets.
        self._write_phony_configurations(line_list)

        # Save the platform targets.
        self._write_phony_platforms(line_list)

        # Generate the list of final binaries
        self._write_phony_binaries(line_list)

        return 0

    ########################################

    def write_directory_targets(self, line_list):
        """
        Create directory and make file targets

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        line_list.extend((
            "",
            "#",
            "# Create the folder for the binary output",
            "#",
            "",
            "bin:",
            "\t@if not exist bin @mkdir bin",
            "",
            "temp:",
            "\t@if not exist temp @mkdir temp"
        ))

        line_list.extend((
            "",
            "#",
            "# Disable building this make file",
            "#",
            "",
            self.solution.watcom_filename + ":",
            _WMAKE_DO_NOTHING))
        return 0

    ########################################

    def write_configurations(self, line_list):
        """
        Write configuration list.

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        # Default configuration, assume Release or use
        # the one found first.
        config = None
        configuration_list = self.configuration_list
        for item in configuration_list:
            if item.name == "Release":
                config = "Release"
                break
            if config is None:
                config = item.name

        # Nothing in self.configuration_list?
        if config is None:
            config = "Release"

        line_list.extend([
            "",
            "#",
            "# Default configuration",
            "#",
            "",
            "!ifndef CONFIG",
            "CONFIG = " + config,
            "!endif"
        ])

        # Default platform is Dos4GW unless it's not in the list
        target = PlatformTypes.msdos4gw.get_short_code()
        platforms = self.platforms
        if platforms and PlatformTypes.msdos4gw not in platforms:
            target = platforms[0].get_short_code()

        line_list.extend([
            "",
            "#",
            "# Default target",
            "#",
            "",
            "!ifndef TARGET",
            "TARGET = " + target,
            "!endif"
        ])

        line_list.extend([
            "",
            "#",
            "# Directory name fragments",
            "#"
        ])

        # List all platforms
        line_list.append("")
        for platform in platforms:
            line_list.append(
                "TARGET_SUFFIX_{0} = {1}".format(
                    platform.get_short_code(),
                    platform.get_short_code()[-3:]))

        line_list.append("")
        for item in self.configuration_names:
            line_list.append("CONFIG_SUFFIX_{0} = {1}".format(item.name,
                                                              item.short_code))

        # Save the base name of the temp directory
        line_list.extend([
            "",
            "#",
            "# Base name of the temp directory",
            "#",
            "",
            "BASE_TEMP_DIR = temp\\" + self.solution.name,
            "BASE_SUFFIX = wat$(TARGET_SUFFIX_$(%TARGET))"
            "$(CONFIG_SUFFIX_$(%CONFIG))",
            "TEMP_DIR = temp\\{0}$(BASE_SUFFIX)".format(self.solution.name)
        ])

        return 0

    ########################################

    def write_source_dir(self, line_list):
        """
        Write out the list of directories for the source

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        # Set the folders for the source code to search
        line_list.extend([
            "",
            "#",
            "# SOURCE_DIRS = Work directories for the source code",
            "#",
            ""
        ])

        # Extract the directories from the files
        # Sort them for consistent diffs for source control
        include_folders = []
        source_folders = []
        configuration_list = self.configuration_list
        for configuration in configuration_list:
            for item in configuration.get_unique_chained_list(
                    "_source_include_list"):
                if item not in source_folders:
                    source_folders.append(item)

            for item in configuration.get_unique_chained_list(
                    "include_folders_list"):
                if item not in include_folders:
                    include_folders.append(item)

        if source_folders:
            colon = "="
            for item in sorted(source_folders):
                line_list.append(
                    "SOURCE_DIRS " +
                    colon +
                    encapsulate_path_linux(item))
                colon = "+=;"
        else:
            line_list.append("SOURCE_DIRS =")

        # Extra include folders
        line_list.extend([
            "",
            "#",
            "# INCLUDE_DIRS = Header includes",
            "#",
            "",
            "INCLUDE_DIRS = $(SOURCE_DIRS)"
        ])

        for item in include_folders:
            item = fixup_env(item)
            line_list.append(
                "INCLUDE_DIRS +=;" +
                convert_to_linux_slashes(item))

        return 0

    ########################################

    @staticmethod
    def _setwatcomdirs(line_list):
        """
        Output the default rules for building object code
        """

        # Set the search directories for source files
        line_list.extend([
            "",
            "#",
            "# Tell WMAKE where to find the files to work with",
            "#",
            "",
            ".c: $(SOURCE_DIRS)",
            ".cpp: $(SOURCE_DIRS)",
            ".x86: $(SOURCE_DIRS)",
            ".i86: $(SOURCE_DIRS)",
            ".rc: $(SOURCE_DIRS)"
        ])

    ########################################

    def _setcppflags(self, line_list):
        """
        Output the default rules for C and C++

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        # C and C++ flags
        line_list.extend((
            "",
            "#",
            "# Set the compiler flags for each of the build types",
            "#",
            ""))

        configuration_list = self.configuration_list
        for configuration in configuration_list:
            entries = ["CFlags" + configuration.watcommake_name + "="]

            if configuration.platform is PlatformTypes.msdos4gw:
                entries.append("-bt=DOS")
                entries.append("-i=\"$(%WATCOM)/h;$(%WATCOM)/h/nt\"")

            elif configuration.platform is PlatformTypes.msdosx32:
                entries.append("-bt=DOS")
                entries.append("-i=\"$(%WATCOM)/h\"")

            else:
                entries.append("-bm")
                entries.append("-bt=NT")
                entries.append("-dTYPE_BOOL=1")
                entries.append("-dTARGET_CPU_X86=1")
                entries.append("-dTARGET_OS_WIN32=1")
                entries.append(
                    "-i=\"$(%WATCOM)/h;"
                    "$(%WATCOM)/h/nt;"
                    "$(%WATCOM)/h/nt/directx\"")

            # Enable debug information
            if configuration.debug:
                entries.append("-d2")
            else:
                entries.append("-d0")

            # Enable optimization
            if configuration.optimization:
                entries.append("-oaxsh")
            else:
                entries.append("-od")

            # Enable C++ exceptions
            if configuration.exceptions:
                entries.append("-xs")

            # Add defines
            define_list = configuration.get_chained_list("define_list")
            for item in define_list:
                entries.append("-D" + item)

            line_list.append(" ".join(entries))
        return 0

    ########################################

    def _setasmflags(self, line_list):
        """
        Output the default rules for assembler

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        # Global assembler flags
        line_list.extend((
            "",
            "#",
            "# Set the assembler flags for each of the build types",
            "#",
            ""))

        configuration_list = self.configuration_list
        for configuration in configuration_list:
            entries = ["AFlags" + configuration.watcommake_name + "="]

            if configuration.platform.is_windows():
                entries.append("-d__WIN32__=1")

            # Add defines
            define_list = configuration.get_chained_list("define_list")
            for item in define_list:
                entries.append("-D" + item)

            line_list.append(" ".join(entries))
        return 0

    ########################################

    def _setlinkerflags(self, line_list):
        """
        Output the default rules for linker

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        line_list.extend((
            "",
            "#",
            "# Set the Linker flags for each of the build types",
            "#",
            ""))

        configuration_list = self.configuration_list
        for configuration in configuration_list:
            entries = ["LFlags" + configuration.watcommake_name + "="]

            # Add linker "system nt"
            item = watcom_linker_system(configuration)
            if item:
                entries.append(item)

            # Add libraries for non static library
            if configuration.project_type is not ProjectTypes.library:

                # Is there a list of folders to locate libraries?
                lib_list = configuration.get_unique_chained_list(
                    "library_folders_list")

                # Use the watcom libp command if needed
                if lib_list:
                    entries.append("libp")
                    entries.append(
                        ";".join(
                            [convert_to_linux_slashes(fixup_env(x))
                             for x in lib_list]))

                # Is there a list of libraries to link in?
                lib_list = configuration.get_unique_chained_list(
                    "libraries_list")

                # Use the watcom LIBRARY command if needed
                if lib_list:
                    entries.append("LIBRARY")
                    entries.append(",".join(lib_list))

            # Set the wmake file line
            line_list.append(" ".join(entries))

        return 0

    ########################################

    def _setresourceflags(self, line_list):
        """
        Output the default rules for resource compiler

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        line_list.extend((
            "",
            "#",
            "# Set the Resource flags for each of the build types",
            "#",
            ""))

        configuration_list = self.configuration_list
        for configuration in configuration_list:
            entries = ["RFlags" + configuration.watcommake_name + "="]

            # Use Windows format
            if configuration.platform.is_windows():
                entries.append("-bt=nt")

                # Also add in the windows headers
                entries.append("-i=\"$(%WATCOM)/h/nt\"")

            # Add defines
            define_list = configuration.get_chained_list("define_list")
            for item in define_list:
                entries.append("-D" + item)

            # Set the wmake file line
            line_list.append(" ".join(entries))

        return 0

    ########################################

    def write_rules(self, line_list):
        """
        Output the default rules for building object code

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        self._setwatcomdirs(line_list)
        self._setcppflags(line_list)
        self._setasmflags(line_list)
        self._setlinkerflags(line_list)
        self._setresourceflags(line_list)

        # Global compiler flags
        line_list.extend([
            "",
            "# Now, set the compiler flags",
            "",
            "CL=WCC386 -6r -fp6 -w4 -ei -j -mf -zq -zp=8 "
            "-wcd=7 -i=\"$(INCLUDE_DIRS)\"",
            "CP=WPP386 -6r -fp6 -w4 -ei -j -mf -zq -zp=8 "
            "-wcd=7 -i=\"$(INCLUDE_DIRS)\"",
            "ASM=WASM -5r -fp6 -w4 -zq -d__WATCOM__=1",
            "LINK=*WLINK option caseexact option quiet PATH $(%WATCOM)/binnt;"
            "$(%WATCOM)/binw;.",
            "RC=WRC -ad -r -q -d__WATCOM__=1 -i=\"$(INCLUDE_DIRS)\"",
            "",
            "# Set the default build rules",
            "# Requires ASM, CP to be set",
            "",
            "# Macro expansion is on page 93 of the C/C++ Tools User's Guide",
            "# $^* = C:\\dir\\target (No extension)",
            "# $[* = C:\\dir\\dep (No extension)",
            "# $^@ = C:\\dir\\target.ext",
            "# $^: = C:\\dir\\",
            "",
            ".rc.res : .AUTODEPEND",
            "\t@echo $[&.rc / $(%CONFIG) / $(%TARGET)",
            "\t@$(RC) $(RFlags$(%CONFIG)$(%TARGET)) $[*.rc -fo=$^@",
            "",
            ".i86.obj : .AUTODEPEND",
            "\t@echo $[&.i86 / $(%CONFIG) / $(%TARGET)",
            "\t@$(ASM) -0 -w4 -zq -d__WATCOM__=1 $(AFlags$(%CONFIG)"
            "$(%TARGET)) $[*.i86 -fo=$^@ -fr=$^*.err",
            "",
            ".x86.obj : .AUTODEPEND",
            "\t@echo $[&.x86 / $(%CONFIG) / $(%TARGET)",
            "\t@$(ASM) $(AFlags$(%CONFIG)$(%TARGET)) "
            "$[*.x86 -fo=$^@ -fr=$^*.err",
            "",
            ".c.obj : .AUTODEPEND",
            "\t@echo $[&.c / $(%CONFIG) / $(%TARGET)",
            "\t@$(CL) $(CFlags$(%CONFIG)$(%TARGET)) $[*.c "
            "-fo=$^@ -fr=$^*.err",
            "",
            ".cpp.obj : .AUTODEPEND",
            "\t@echo $[&.cpp / $(%CONFIG) / $(%TARGET)",
            "\t@$(CP) $(CFlags$(%CONFIG)$(%TARGET)) $[*.cpp "
            "-fo=$^@ -fr=$^*.err"
        ])
        return 0

    ########################################

    def write_files(self, line_list):
        """
        Output the list of object files to create.

        Args:
            line_list: List of lines of text generated.
        Returns:
            True if compilable files were found
        """

        line_list.extend([
            "",
            "#",
            "# Object files to work with for the project",
            "#",
            ""
        ])

        if self.solution.project_list:

            # Get the list of acceptable object files
            obj_list = get_obj_list(
                self.solution.project_list[0].codefiles,
                (FileTypes.c, FileTypes.cpp, FileTypes.x86))

            if obj_list:
                # Create the OBJS= list
                add_obj_list(
                    line_list, obj_list, "OBJS= ", ".obj")
                return True

        line_list.append("OBJS=")
        return False

    ########################################

    def write_res_files(self, line_list):
        """
        Output the list of resource files to create.

        Args:
            line_list: List of lines of text generated.
        Returns:
            True if .rc files were found
        """

        line_list.extend([
            "",
            "#",
            "# Resource files to work with for the project",
            "#",
            ""
        ])

        if self.solution.project_list:

            # Get the list of acceptable object files
            obj_list = get_obj_list(
                self.solution.project_list[0].codefiles,
                (FileTypes.rc,))

            if obj_list:
                # Create the OBJS= list
                add_obj_list(
                    line_list, obj_list, "RC_OBJS= ", ".res")
                return True

        line_list.append("RC_OBJS=")
        return False

########################################

    def write_custom_files(self, line_list):
        """
        Output the list of object files to create.

        Args:
            line_list: List of lines of text generated.
        Returns:
            Zero
        """

        # Get a list of custom files
        output_list = self.output_list
        if not output_list:
            return 0

        line_list.extend([
            "",
            "#",
            "# Build custom files",
            "#"
        ])

        output_list = list(self.output_list)
        # Output the execution lines
        while output_list:

            output = output_list[0]

            entry = None
            for item in self.custom_list:
                for output_test in item[2]:
                    if output_test == output:
                        entry = item
                        break
                if entry:
                    break

            else:
                output_list.remove(output)
                continue

            line_list.append("")
            line_list.append(
                " ".join(entry[2]) + " : " +
                convert_to_linux_slashes(
                    entry[3].relative_pathname))
            line_list.append("\t@echo " + entry[1])
            line_list.append("\t@cmd /c & " + fixup_env(entry[0]))

            for output_test in entry[2]:
                output_list.remove(output_test)

        return 0

    ########################################

    def write_builds(self, line_list, has_rez):
        """
        Output the rule to build the exes/libs

        Args:
            line_list: List of lines of text generated.
            has_rez: Is there a Windows Resource file to link in
        Returns:
            Zero
        """

        line_list.extend([
            "",
            "#",
            "# A = The object file temp folder",
            "#"
        ])

        configuration_list = self.configuration_list
        for configuration in configuration_list:
            if configuration.project_type is ProjectTypes.library:
                suffix = ".lib"
            else:
                suffix = ".exe"
            line_list.append("")
            line_list.append(
                "A = $(BASE_TEMP_DIR)wat" +
                configuration.platform.get_short_code()[-3:] +
                configuration.short_code)

            if has_rez and configuration.platform.is_windows():
                rc_objs = "$+$(RC_OBJS)$- "
            else:
                rc_objs = ""

            line_list.append(
                "bin\\" + self.solution.name + "wat" +
                configuration.platform.get_short_code()[-3:] +
                configuration.short_code + suffix +
                ": $(EXTRA_OBJS) $+$(OBJS)$- " + rc_objs +
                self.solution.watcom_filename)

            if configuration.project_type is ProjectTypes.library:

                line_list.extend([
                    "\t@SET WOW=$+$(OBJS)$-",
                    "\t@echo Creating library...",
                    "\t@WLIB -q -b -c -n $^@ @WOW"
                ])

                add_post_build(line_list, configuration)

                if configuration.deploy_folder:
                    deploy_folder = convert_to_windows_slashes(
                        configuration.deploy_folder,
                        force_ending_slash=True)[:-1]
                    deploy_folder = fixup_env(deploy_folder)
                    line_list.extend([
                        "\t@p4 edit \"{}\\$^.\"".format(deploy_folder),
                        "\t@copy /y \"$^@\" \"{}\\$^.\"".format(deploy_folder),
                        "\t@p4 revert -a \"{}\\$^.\"".format(deploy_folder)
                    ])
            else:
                line_list.extend([
                    "\t@SET WOW={$+$(OBJS)$-}",
                    "\t@echo Performing link...",
                    "\t@$(LINK) $(LFlags" + configuration.name + \
                    configuration.platform.get_short_code() + ") "
                    "NAME $^@ FILE @wow"
                ])

                # If there's a resource file, add it to the exe
                if rc_objs:
                    line_list.append(
                        "\t@echo Performing resource linking...")
                    line_list.append(
                        "\t@WRC -q -bt=nt $+$(RC_OBJS)$- $^@")

                add_post_build(line_list, configuration)

        return 0

    ########################################

    def generate(self, line_list=None):
        """
        Write out the watcom make project.

        Args:
            line_list: string list to save the XML text
        Returns:
            Zero on no error, non-zero on error.
        """

        if line_list is None:
            line_list = []

        self.write_header(line_list)
        self.write_test_variables(line_list)
        self.write_extensions(line_list)
        self.write_include_dlls(line_list)
        self.write_output_list(line_list)
        self.write_all_targets(line_list)
        self.write_directory_targets(line_list)
        self.write_configurations(line_list)
        self.write_source_dir(line_list)
        self.write_rules(line_list)
        self.write_files(line_list)
        has_rez = self.write_res_files(line_list)
        self.write_custom_files(line_list)
        self.write_builds(line_list, has_rez)
        return 0
