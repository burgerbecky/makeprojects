#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sub file for makeprojects.
Handler for Codeblocks projects

This module contains classes needed to generate
project files intended for use by Codeblocks

@package makeprojects.codeblocks
"""

# Copyright 1995-2022 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

import os
from burger import save_text_file_if_newer, convert_to_linux_slashes
from .enums import FileTypes, ProjectTypes, PlatformTypes, IDETypes

SUPPORTED_IDES = (IDETypes.codeblocks,)

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


class Project(object):
    """
    Root object for a Codeblocks IDE project file
    Created with the name of the project, the IDE code
    the platform code (4gw, x32, win)

    Attributes:
        solution: Parent solution
        platforms: List of all platform types
        configuration_list: List of all configurations
        configuration_names: List of configuration names

    """

    def __init__(self, solution):
        """
        Initialize the exporter.
        """

        self.solution = solution
        self.platforms = []
        self.configuration_list = []
        self.configuration_names = []

        # Process all the projects and configurations
        for project in solution.project_list:

            # Process the filenames
            project.get_file_list([FileTypes.h,
                                   FileTypes.cpp,
                                   FileTypes.c,
                                   FileTypes.x86,
                                   ])

            # Add to the master list
            self.configuration_list.extend(project.configuration_list)

            # Create sets of configuration names and projects
            for configuration in project.configuration_list:

                # Add only if not already present
                for item in self.configuration_names:
                    if configuration.name == item.name:
                        break
                else:
                    self.configuration_names.append(configuration)

                # Add platform if not already found
                if configuration.platform not in self.platforms:
                    self.platforms.append(configuration.platform)

    ########################################

    def generate(self, line_list=None):
        """
        Write out the Watcom project.

        Args:
            line_list: string list to save the XML text
        """

        if line_list is None:
            line_list = []

        # Save the standard XML header for CodeBlocks
        line_list.append(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>')
        line_list.append('<CodeBlocks_project_file>')
        line_list.append('\t<FileVersion major="1" minor="6" />')
        line_list.append('\t<Project>')

        # Output the project settings

        line_list.append('\t\t<Option title="' + self.solution.name + '" />')
        line_list.append('\t\t<Option makefile="makefile" />')
        line_list.append('\t\t<Option pch_mode="2" />')
        line_list.append('\t\t<Option compiler="ow" />')

        # Output the per target build settings
        line_list.append('\t\t<Build>')
        for configuration in self.configuration_list:
            target_name = configuration.name + '_' + \
                configuration.platform.get_short_code()

            line_list.append('\t\t\t<Target title="' + target_name + '">')

            binary_name = 'bin/{}{}'.format(
                configuration.project.name,
                configuration.get_suffix())
            if configuration.project_type.is_library():
                binary_name = binary_name + '.lib'
            else:
                binary_name = binary_name + '.exe'

            line_list.append(
                '\t\t\t\t<Option output="' +
                binary_name +
                '" prefix_auto="0" extension_auto="0" />')
            line_list.append('\t\t\t\t<Option working_dir="" />')

            intdirectory = 'temp/{}{}/'.format(
                configuration.project.name,
                configuration.get_suffix())
            line_list.append(
                '\t\t\t\t<Option object_output="' + intdirectory + '" />')

            if configuration.project_type is ProjectTypes.tool:
                line_list.append('\t\t\t\t<Option type="1" />')
            else:
                line_list.append('\t\t\t\t<Option type="2" />')

            line_list.append('\t\t\t\t<Option compiler="ow" />')
            line_list.append('\t\t\t\t<Option createDefFile="1" />')
            line_list.append('\t\t\t\t<Compiler>')

            if configuration.platform.is_msdos():
                line_list.append('\t\t\t\t\t<Add option="-bt=dos" />')
            else:
                line_list.append('\t\t\t\t\t<Add option="-bt=nt" />')

            # Include symbols
            if configuration.debug:
                line_list.append('\t\t\t\t\t<Add option="-d2" />')

            # Enable optimizations
            if configuration.optimization:
                line_list.append('\t\t\t\t\t<Add option="-ox" />')
                line_list.append('\t\t\t\t\t<Add option="-ot" />')

            # Maximum warnings
            line_list.append('\t\t\t\t\t<Add option="-wx" />')

            # Pentium Pro floating point
            line_list.append('\t\t\t\t\t<Add option="-fp6" />')

            # Pentium Pro optimizations
            line_list.append('\t\t\t\t\t<Add option="-6r" />')

            # Error file name
            line_list.append('\t\t\t\t\t<Add option="-fr=$(ERROR_FILE)" />')

            # Defines
            for item in configuration.get_chained_list('define_list'):
                line_list.append('\t\t\t\t\t<Add option="-d' + item + '" />')
            line_list.append('\t\t\t\t</Compiler>')
            line_list.append('\t\t\t</Target>')

        line_list.append('\t\t\t<Environment>')
        line_list.append((
            '\t\t\t\t<Variable name="ERROR_FILE" '
            'value="$(TARGET_OBJECT_DIR)foo.err" />'))
        line_list.append('\t\t\t</Environment>')
        line_list.append('\t\t</Build>')

        # Output the virtual target
        line_list.append('\t\t<VirtualTargets>')
        target_list = []
        for configuration in self.configuration_list:
            target_name = configuration.name + '_' + \
                configuration.platform.get_short_code()
            target_list.append(target_name)
        line_list.append(
            '\t\t\t<Add alias="Everything" targets="' +
            ';'.join(target_list) +
            '" />')
        line_list.append('\t\t</VirtualTargets>')

        # Output the global compiler settings
        line_list.append('\t\t<Compiler>')

        # Extract the directories from the files
        # Sort them for consistent diffs for source control
        include_folders = []
        for configuration in self.configuration_list:
            for item in configuration.get_unique_chained_list(
                    '_source_include_list'):
                if item not in include_folders:
                    include_folders.append(item)

            for item in configuration.get_unique_chained_list(
                    'include_folders_list'):
                if item not in include_folders:
                    include_folders.append(item)

        for item in sorted(include_folders):
            line_list.append('\t\t\t<Add directory=\'&quot;' +
                             convert_to_linux_slashes(item) +
                             '&quot;\' />')

        if not self.solution.project_list[0].project_type.is_library() or \
                self.solution.name != 'burger':
            line_list.append((
                '\t\t\t<Add directory=\'&quot;'
                '$(BURGER_SDKS)/windows/burgerlib&quot;\' />'))
        line_list.append('\t\t</Compiler>')

        # Output the list of source files
        if self.solution.project_list:
            codefiles = self.solution.project_list[0].codefiles
        else:
            codefiles = []

        for item in codefiles:
            line_list.append(
                '\t\t<Unit filename="' +
                convert_to_linux_slashes(
                    item.relative_pathname) +
                '" />')

        # Add the extensions (If any)
        line_list.append('\t\t<Extensions>')
        line_list.append('\t\t\t<code_completion />')
        line_list.append('\t\t\t<envvars />')
        line_list.append('\t\t\t<debugger />')
        line_list.append('\t\t</Extensions>')

        # Close the file

        line_list.append('\t</Project>')
        line_list.append('</CodeBlocks_project_file>')
        return 0

########################################


def generate(solution):
    """
    Create a project file for Codeblocks.

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

    # Create the output filename and pass it to the generator
    # so it can reference itself in make targets
    solution.codeblocks_filename = '{}{}{}.cbp'.format(
        solution.name, solution.ide_code, solution.platform_code)

    exporter = Project(solution)

    # Output the actual project file
    codeblocks_lines = []
    error = exporter.generate(codeblocks_lines)
    if error:
        return error

    # Save the file if it changed
    save_text_file_if_newer(
        os.path.join(solution.working_directory, solution.codeblocks_filename),
        codeblocks_lines,
        bom=False,
        perforce=solution.perforce,
        verbose=solution.verbose)
    return 0
