#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 1995-2022 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

"""
This module contains classes needed to generate
project files intended for use by Open Watcom
WMAKE 1.9 or higher

@package makeprojects.watcom

@var makeprojects.watcom._WATCOMFILE_MATCH
Regex for matching files with *.wmk

@var makeprojects.watcom.SUPPORTED_IDES
List of IDETypes the watcom module supports.
"""

# pylint: disable=consider-using-f-string
# pylint: disable=super-with-arguments
# pylint: disable=useless-object-inheritance

from __future__ import absolute_import, print_function, unicode_literals

import os
from re import compile as re_compile
from burger import save_text_file_if_newer, encapsulate_path_linux, \
    convert_to_linux_slashes, convert_to_windows_slashes, where_is_watcom, \
    get_windows_host_type

from .enums import FileTypes, ProjectTypes, PlatformTypes, IDETypes
from .build_objects import BuildObject, BuildError

_WATCOMFILE_MATCH = re_compile('(?is).*\\.wmk\\Z')

SUPPORTED_IDES = (IDETypes.watcom,)

########################################


class BuildWatcomFile(BuildObject):
    """
    Class to build watcom make files

    Attribute:
        verbose: Save the verbose flag
    """

    def __init__(self, file_name, priority, configuration, verbose=False):
        """
        Class to handle watcom make files

        Args:
            file_name: Pathname to the *.wmk to build
            priority: Priority to build this object
            configuration: Build configuration
            verbose: True if verbose output
        """

        super(BuildWatcomFile, self).__init__(
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
            return BuildError(
                0, self.file_name,
                msg='{} requires Watcom to be installed to build!'.format(
                    self.file_name))

        # Watcom requires the path set up so it can access link files
        saved_path = os.environ['PATH']
        if get_windows_host_type():
            new_path = os.pathsep.join(
                (os.path.join(
                    watcom_path, 'binnt'), os.path.join(
                        watcom_path, 'binw')))
        else:
            new_path = os.path.join(watcom_path, 'binl')

        exe_name = where_is_watcom('wmake', verbose=self.verbose)
        os.environ['PATH'] = new_path + os.pathsep + saved_path

        # Set the configuration target
        cmd = [exe_name, '-e', '-h', '-f', self.file_name, self.configuration]

        # Iterate over the commands
        if self.verbose:
            print(' '.join(cmd))

        result = self.run_command(cmd, self.verbose)

        # Restore the path variable
        os.environ['PATH'] = saved_path

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
        return BuildError(0, self.file_name,
                          msg="Watcom doesn't support cleaning")

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
        return [BuildWatcomFile(file_name, priority, 'all', verbose)]

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
        return [BuildWatcomFile(file_name, priority, 'clean', verbose)]

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


class Project(object):
    """
    Root object for a Watcom IDE project file
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

    def write_header(self, line_list):
        """
        Write the header for a Watcom wmake file
        """

        line_list.extend([
            '#',
            '# Build ' + self.solution.name + ' with WMAKE',
            '# Generated with makeprojects',
            '#',
            '# Require the environment variable WATCOM set to the OpenWatcom '
            'folder',
            '# Example: WATCOM=C:\\WATCOM',
            '#',
            '',
            '# This speeds up the building process for Watcom because it',
            '# keeps the apps in memory and doesn\'t have '
            'to reload for every source file',
            '# Note: There is a bug that if the wlib app is loaded, '
            'it will not',
            '# get the proper WOW file if a full build is performed',
            '',
            '# The bug is gone from Watcom 1.2',
            '',
            '!ifdef %WATCOM',
            '!ifdef __LOADDLL__',
            '!loaddll wcc $(%WATCOM)/binnt/wccd',
            '!loaddll wccaxp $(%WATCOM)/binnt/wccdaxp',
            '!loaddll wcc386 $(%WATCOM)/binnt/wccd386',
            '!loaddll wpp $(%WATCOM)/binnt/wppdi86',
            '!loaddll wppaxp $(%WATCOM)/binnt/wppdaxp',
            '!loaddll wpp386 $(%WATCOM)/binnt/wppd386',
            '!loaddll wlink $(%WATCOM)/binnt/wlinkd',
            '!loaddll wlib $(%WATCOM)/binnt/wlibd',
            '!endif',
            '!endif'])

        # Default configuration
        config = None
        for item in self.configuration_list:
            if item.name == 'Release':
                config = 'Release'
            elif config is None:
                config = item.name
        if config is None:
            config = 'Release'

        line_list.extend([
            '',
            '#',
            '# Default configuration',
            '#',
            '',
            '!ifndef CONFIG',
            'CONFIG = ' + config,
            '!endif'
        ])

        # Default platform
        target = None
        # Get all the configuration names
        for platform in self.platforms:
            if platform is PlatformTypes.msdos4gw:
                target = platform.get_short_code()
            elif target is None:
                target = platform.get_short_code()
        if target is None:
            target = 'Release'

        line_list.extend([
            '',
            '#',
            '# Default target',
            '#',
            '',
            '!ifndef TARGET',
            'TARGET = ' + target,
            '!endif'
        ])

        line_list.extend([
            '',
            '#',
            '# Directory name fragments',
            '#',
            ''
        ])

        for platform in self.platforms:
            line_list.append(
                'TARGET_SUFFIX_{0} = {1}'.format(
                    platform.get_short_code(),
                    platform.get_short_code()[-3:]))

        line_list.append('')
        for item in self.configuration_names:
            line_list.append('CONFIG_SUFFIX_{0} = {1}'.format(item.name,
                                                              item.short_code))

        line_list.extend([
            '',
            '#',
            '# Set the set of known files supported',
            '# Note: They are in the reverse order of building. .c is '
            'built first, then .x86',
            '# until the .exe or .lib files are built',
            '#',
            '',
            '.extensions:',
            '.extensions: .exe .exp .lib .obj .h .cpp .x86 .c .i86',
        ])
        return 0

    def write_source_dir(self, line_list):
        """
        Write out the list of directories for the source
        """

        # Save the refernence BURGER_SDKS
        line_list.extend([
            '',
            '#',
            '# Ensure sdks are pulled from the environment',
            '#',
            '',
            'BURGER_SDKS = $(%BURGER_SDKS)'
        ])

        # Set the folders for the source code to search
        line_list.extend([
            '',
            '#',
            '# SOURCE_DIRS = Work directories for the source code',
            '#',
            ''
        ])

        # Extract the directories from the files
        # Sort them for consistent diffs for source control
        include_folders = []
        source_folders = []
        for configuration in self.configuration_list:
            for item in configuration.get_unique_chained_list(
                    '_source_include_list'):
                if item not in source_folders:
                    source_folders.append(item)

            for item in configuration.get_unique_chained_list(
                    'include_folders_list'):
                if item not in include_folders:
                    include_folders.append(item)

        if source_folders:
            colon = '='
            for item in sorted(source_folders):
                line_list.append(
                    'SOURCE_DIRS ' +
                    colon +
                    encapsulate_path_linux(item))
                colon = '+=;'
        else:
            line_list.append('SOURCE_DIRS =')

        # Save the project name
        line_list.extend([
            '',
            '#',
            '# Name of the output library',
            '#',
            '',
            'PROJECT_NAME = ' + self.solution.name])

        # Save the base name of the temp directory
        line_list.extend([
            '',
            '#',
            '# Base name of the temp directory',
            '#',
            '',
            'BASE_TEMP_DIR = temp/$(PROJECT_NAME)',
            'BASE_SUFFIX = wat$(TARGET_SUFFIX_$(%TARGET))'
            '$(CONFIG_SUFFIX_$(%CONFIG))',
            'TEMP_DIR = $(BASE_TEMP_DIR)$(BASE_SUFFIX)'
        ])

        # Save the final binary output directory
        line_list.extend([
            '',
            '#',
            '# Binary directory',
            '#',
            '',
            'DESTINATION_DIR = bin'
        ])

        # Extra include folders
        line_list.extend([
            '',
            '#',
            '# INCLUDE_DIRS = Header includes',
            '#',
            '',
            'INCLUDE_DIRS = $(SOURCE_DIRS)'
        ])

        for item in include_folders:
            line_list.append(
                'INCLUDE_DIRS +=;' +
                convert_to_linux_slashes(item))

        return 0

    @staticmethod
    def write_rules(line_list):
        """
        Output the default rules for building object code
        """

        # Set the search directories for source files
        line_list.extend([
            '',
            '#',
            '# Tell WMAKE where to find the files to work with',
            '#',
            '',
            '.c: $(SOURCE_DIRS)',
            '.cpp: $(SOURCE_DIRS)',
            '.x86: $(SOURCE_DIRS)',
            '.i86: $(SOURCE_DIRS)'
        ])

        # Global compiler flags
        line_list.extend([
            '',
            '#',
            '# Set the compiler flags for each of the build types',
            '#',
            '',
            'CFlagsDebug=-d_DEBUG -d2 -od',
            'CFlagsInternal=-d_DEBUG -d2 -oaxsh',
            'CFlagsRelease=-dNDEBUG -d0 -oaxsh',
            '',
            '#',
            '# Set the flags for each target operating system',
            '#',
            '',
            'CFlagscom=-bt=com -d__COM__=1 -i="$(%BURGER_SDKS)/dos/burgerlib;'
            '$(%BURGER_SDKS)/dos/x32;$(%WATCOM)/h"',
            'CFlagsdosx32=-bt=DOS -d__X32__=1 '
            '-i="$(%BURGER_SDKS)/dos/burgerlib;'
            '$(%BURGER_SDKS)/dos/x32;$(%WATCOM)/h"',
            'CFlagsdos4gw=-bt=DOS -d__DOS4G__=1 '
            '-i="$(%BURGER_SDKS)/dos/burgerlib;'
            '$(%BURGER_SDKS)/dos/sosaudio;$(%WATCOM)/h;$(%WATCOM)/h/nt"',
            'CFlagsw32=-bt=NT -dGLUT_DISABLE_ATEXIT_HACK -dGLUT_NO_LIB_PRAGMA '
            '-dTARGET_CPU_X86=1 -dTARGET_OS_WIN32=1 -dTYPE_BOOL=1 -dUNICODE '
            '-d_UNICODE -dWIN32_LEAN_AND_MEAN '
            '-i="$(%BURGER_SDKS)/windows/burgerlib;'
            '$(%BURGER_SDKS)/windows/opengl;$(%BURGER_SDKS)/windows/directx9;'
            '$(%BURGER_SDKS)/windows/windows5;'
            '$(%BURGER_SDKS)/windows/quicktime7;'
            '$(%WATCOM)/h;$(%WATCOM)/h/nt"',
            '',
            '#',
            '# Set the WASM flags for each of the build types',
            '#',
            '',
            'AFlagsDebug=-d_DEBUG',
            'AFlagsInternal=-d_DEBUG',
            'AFlagsRelease=-dNDEBUG',
            '',
            '#',
            '# Set the WASM flags for each operating system',
            '#',
            '',
            'AFlagscom=-d__COM__=1',
            'AFlagsdosx32=-d__X32__=1',
            'AFlagsdos4gw=-d__DOS4G__=1',
            'AFlagsw32=-d__WIN32__=1',
            '',
            'LFlagsDebug=',
            'LFlagsInternal=',
            'LFlagsRelease=',
            '',
            'LFlagscom=format dos com libp $(%BURGER_SDKS)/dos/burgerlib',
            'LFlagsx32=system x32r libp $(%BURGER_SDKS)/dos/burgerlib;'
            '$(%BURGER_SDKS)/dos/x32',
            'LFlagsdos4gw=system dos4g libp $(%BURGER_SDKS)/dos/burgerlib;'
            '$(%BURGER_SDKS)/dos/sosaudio',
            'LFlagsw32=system nt libp $(%BURGER_SDKS)/windows/burgerlib;'
            '$(%BURGER_SDKS)/windows/directx9 LIBRARY VERSION.lib,opengl32.lib,'
            'winmm.lib,shell32.lib,shfolder.lib',
            '',
            '# Now, set the compiler flags',
            '',
            'CL=WCC386 -6r -fp6 -w4 -ei -j -mf -zq -zp=8 '
            '-wcd=7 -i="$(INCLUDE_DIRS)"',
            'CP=WPP386 -6r -fp6 -w4 -ei -j -mf -zq -zp=8 '
            '-wcd=7 -i="$(INCLUDE_DIRS)"',
            'ASM=WASM -5r -fp6 -w4 -zq -d__WATCOM__=1',
            'LINK=*WLINK option caseexact option quiet PATH $(%WATCOM)/binnt;'
            '$(%WATCOM)/binw;.',
            '',
            '# Set the default build rules',
            '# Requires ASM, CP to be set',
            '',
            '# Macro expansion is on page 93 of the C//C++ Tools User\'s Guide',
            '# $^* = C:\\dir\\target (No extension)',
            '# $[* = C:\\dir\\dep (No extension)',
            '# $^@ = C:\\dir\\target.ext',
            '# $^: = C:\\dir\\',
            '',
            '.i86.obj : .AUTODEPEND',
            '\t@echo $[&.i86 / $(%CONFIG) / $(%TARGET)',
            '\t@$(ASM) -0 -w4 -zq -d__WATCOM__=1 $(AFlags$(%CONFIG)) '
            '$(AFlags$(%TARGET)) $[*.i86 -fo=$^@ -fr=$^*.err',
            '',
            '.x86.obj : .AUTODEPEND',
            '\t@echo $[&.x86 / $(%CONFIG) / $(%TARGET)',
            '\t@$(ASM) $(AFlags$(%CONFIG)) $(AFlags$(%TARGET)) '
            '$[*.x86 -fo=$^@ -fr=$^*.err',
            '',
            '.c.obj : .AUTODEPEND',
            '\t@echo $[&.c / $(%CONFIG) / $(%TARGET)',
            '\t@$(CL) $(CFlags$(%CONFIG)) $(CFlags$(%TARGET)) $[*.c '
            '-fo=$^@ -fr=$^*.err',
            '',
            '.cpp.obj : .AUTODEPEND',
            '\t@echo $[&.cpp / $(%CONFIG) / $(%TARGET)',
            '\t@$(CP) $(CFlags$(%CONFIG)) $(CFlags$(%TARGET)) $[*.cpp '
            '-fo=$^@ -fr=$^*.err'
        ])
        return 0

    def write_files(self, line_list):
        """
        Output the list of object files to create
        """
        line_list.extend([
            '',
            '#',
            '# Object files to work with for the library',
            '#',
            ''
        ])

        obj_list = []
        if self.solution.project_list:
            codefiles = self.solution.project_list[0].codefiles
        else:
            codefiles = []

        for item in codefiles:
            if item.type is FileTypes.c or \
                    item.type is FileTypes.cpp or \
                    item.type is FileTypes.x86:

                tempfile = convert_to_linux_slashes(
                    item.relative_pathname)
                index = tempfile.rfind('.')
                if index == -1:
                    entry = tempfile
                else:
                    entry = tempfile[:index]

                index = entry.rfind('/')
                if index != -1:
                    entry = entry[index + 1:]

                obj_list.append(entry)

        if obj_list:
            colon = 'OBJS= '
            for item in sorted(obj_list):
                line_list.append(colon + '$(A)/' + item + '.obj &')
                colon = '\t'
            # Remove the ' &' from the last line
            line_list[-1] = line_list[-1][:-2]

        else:
            line_list.append('OBJS=')
        return 0

    def write_all_target(self, line_list):
        """
        Output the "all" rule
        """

        line_list.extend([
            '',
            '#',
            '# List the names of all of the final binaries to build',
            '#',
            ''
        ])

        target_list = ['all:']
        for item in self.configuration_names:
            target_list.append(item.name)
        target_list.append('.SYMBOLIC')
        line_list.append(' '.join(target_list))
        line_list.append('\t@%null')

        line_list.extend([
            '',
            '#',
            '# Configurations',
            '#'
        ])

        # Build targets for configuations
        for configuration in self.configuration_names:
            line_list.append('')
            target_list = [configuration.name + ':']
            for platform in self.platforms:
                target_list.append(
                    configuration.name +
                    platform.get_short_code())
            target_list.append('.SYMBOLIC')
            line_list.append(' '.join(target_list))
            line_list.append('\t@%null')

        # Build targets for platforms
        for platform in self.platforms:
            line_list.append('')
            target_list = [platform.get_short_code() + ':']
            for configuration in self.configuration_list:
                target_list.append(
                    configuration.name +
                    platform.get_short_code())
            target_list.append('.SYMBOLIC')
            line_list.append(' '.join(target_list))
            line_list.append('\t@%null')

        for configuration in self.configuration_list:
            if configuration.project_type is ProjectTypes.library:
                suffix = 'lib'
            else:
                suffix = 'exe'
            platform = configuration.platform
            line_list.append('')
            line_list.append(
                '{0}{1}: .SYMBOLIC'.format(
                    configuration.name,
                    platform.get_short_code()))
            line_list.append('\t@if not exist "$(DESTINATION_DIR)" '
                             '@mkdir "$(DESTINATION_DIR)"')
            name = 'wat' + platform.get_short_code(
            )[-3:] + configuration.short_code
            line_list.append('\t@if not exist "$(BASE_TEMP_DIR){0}" '
                             '@mkdir "$(BASE_TEMP_DIR){0}"'.format(name))
            line_list.append('\t@set CONFIG=' + configuration.name)
            line_list.append('\t@set TARGET=' + platform.get_short_code())
            line_list.append(
                '\t@%make $(DESTINATION_DIR)\\$(PROJECT_NAME)wat' +
                platform.get_short_code()[-3:] +
                configuration.short_code + '.' + suffix)

        line_list.extend([
            '',
            '#',
            '# Disable building this make file',
            '#',
            '',
            self.solution.watcom_filename + ':',
            '\t@%null'
        ])
        return 0

    def write_builds(self, line_list):
        """
        Output the rule to build the exes/libs
        """

        line_list.extend([
            '',
            '#',
            '# A = The object file temp folder',
            '#'
        ])

        for configuration in self.configuration_list:
            if configuration.project_type is ProjectTypes.library:
                suffix = '.lib'
            else:
                suffix = '.exe'
            line_list.append('')
            line_list.append(
                'A = $(BASE_TEMP_DIR)wat' +
                configuration.platform.get_short_code()[-3:] +
                configuration.short_code)

            line_list.append(
                '$(DESTINATION_DIR)\\$(PROJECT_NAME)wat' +
                configuration.platform.get_short_code()[-3:] +
                configuration.short_code + suffix +
                ': $+$(OBJS)$- ' + self.solution.watcom_filename)

            if configuration.project_type is ProjectTypes.library:

                line_list.extend([
                    '\t@SET WOW=$+$(OBJS)$-',
                    '\t@WLIB -q -b -c -n $^@ @WOW'
                ])

                if configuration.deploy_folder:
                    deploy_folder = convert_to_windows_slashes(
                        configuration.deploy_folder,
                        force_ending_slash=True)[:-1]
                    line_list.extend([
                        '\t@p4 edit "{}\\$^."'.format(deploy_folder),
                        '\t@copy /y "$^@" "{}\\$^."'.format(deploy_folder),
                        '\t@p4 revert -a "{}\\$^."'.format(deploy_folder)
                    ])
            else:
                line_list.extend([
                    '\t@SET WOW={$+$(OBJS)$-}',
                    '\t@$(LINK) $(LFlags$(%TARGET)) $(LFlags$(%CONFIG)) '
                    'LIBRARY burger$(BASE_SUFFIX).lib NAME $^@ FILE @wow'
                ])

        return 0

    ########################################

    def generate(self, line_list=None):
        """
        Write out the Watcom project.

        Args:
            line_list: string list to save the XML text
        """

        if line_list is None:
            line_list = []

        self.write_header(line_list)
        self.write_source_dir(line_list)
        self.write_rules(line_list)
        self.write_files(line_list)
        self.write_all_target(line_list)
        self.write_builds(line_list)
        return 0

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

    # Create the output filename and pass it to the generator
    # so it can reference itself in make targets
    solution.watcom_filename = '{}{}{}.wmk'.format(
        solution.name, solution.ide_code, solution.platform_code)

    exporter = Project(solution)

    # Output the actual project file
    watcom_lines = []
    error = exporter.generate(watcom_lines)
    if error:
        return error

    # Save the file if it changed
    save_text_file_if_newer(
        os.path.join(solution.working_directory, solution.watcom_filename),
        watcom_lines,
        bom=False,
        perforce=solution.perforce,
        verbose=solution.verbose)
    return 0
