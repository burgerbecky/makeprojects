#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sub file for makeprojects.
Handler for Watcom WMAKE projects
"""

# Copyright 1995-2018 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

#
## \package makeprojects.watcom
# This module contains classes needed to generate
# project files intended for use by Open Watcom
# WMAKE 1.9 or higher
#

from __future__ import absolute_import, print_function, unicode_literals
import os
from io import StringIO
import burger
from makeprojects import FileTypes, ProjectTypes, PlatformTypes, \
    ConfigurationTypes

# pylint: disable=C0302

#
## \package makeprojects.watcom
# This module contains classes needed to generate
# project files intended for use by OpenWatcom WMAKE
#

#
# Default folder for DOS tools when invoking 'FINAL_FOLDER'
# from the command line
#

DEFAULT_FINAL_FOLDER = '$(BURGER_SDKS)/dos/burgerlib'

## Array of targets that Watcom can build
VALID_TARGETS = [
    PlatformTypes.msdos4gw,
    PlatformTypes.msdosx32,
    PlatformTypes.win32
]


class Project(object):
    """
    Root object for a Watcom IDE project file
    Created with the name of the project, the IDE code
    the platform code (4gw, x32, win)
    """

    def __init__(self, project_name, ide_code, platform_code):
        self.project_name = project_name
        self.ide_code = ide_code
        self.platform_code = platform_code
        self.projectname_code = project_name + ide_code + platform_code
        self.projecttype = None
        self.code_files = []
        self.include_folders = []
        self.final_folder = None
        self.platforms = []
        self.configurations = []

    def add_source_file(self, source_file):
        """
        Add a SourceFile() to the project
        """
        self.code_files.append(source_file)

    def add_include_folder(self, include_folder):
        """
        Add a path to the include directory list to the project
        """
        self.include_folders.append(include_folder)

    def write_header(self, filep):
        """
        Write the header for a Watcom wmake file
        """
        filep.write( \
            '#\n' \
            '# Build ' + self.project_name + ' with WMAKE\n' \
            '# Set the environment variable WATCOM to the OpenWatcom folder\n'
            '#\n' \
            '\n' \
            '# This speeds up the building process for Watcom because it\n' \
            '# keeps the apps in memory and doesn\'t have ' \
            'to reload for every source file\n' \
            '# Note: There is a bug that if the wlib app is loaded, it will not\n' \
            '# get the proper WOW file if a full build is performed\n' \
            '\n' \
            '# The bug is gone from Watcom 1.2\n' \
            '\n' \
            '!ifdef %WATCOM\n' \
            '!ifdef __LOADDLL__\n' \
            '!loaddll wcc $(%WATCOM)/binnt/wccd\n' \
            '!loaddll wccaxp $(%WATCOM)/binnt/wccdaxp\n' \
            '!loaddll wcc386 $(%WATCOM)/binnt/wccd386\n' \
            '!loaddll wpp $(%WATCOM)/binnt/wppdi86\n' \
            '!loaddll wppaxp $(%WATCOM)/binnt/wppdaxp\n' \
            '!loaddll wpp386 $(%WATCOM)/binnt/wppd386\n' \
            '!loaddll wlink $(%WATCOM)/binnt/wlinkd\n' \
            '!loaddll wlib $(%WATCOM)/binnt/wlibd\n' \
            '!endif\n' \
            '!endif\n')

        config = None
        for item in self.configurations:
            if item == ConfigurationTypes.release:
                config = 'Release'
            elif config is None:
                config = str(item)
        if config is None:
            config = 'Release'

        target = None
        for item in self.platforms:
            if item == PlatformTypes.msdos4gw:
                target = item.getshortcode()
            elif target is None:
                target = item.getshortcode()

        filep.write( \
            '\n' \
            '#\n' \
            '# Default configuration\n' \
            '#\n\n' \
            '!ifndef CONFIG\n' \
            'CONFIG = {0}\n' \
            '!endif\n\n'
            '#\n' \
            '# Default target\n' \
            '#\n\n' \
            '!ifndef TARGET\n' \
            'TARGET = {1}\n' \
            '!endif\n'.format(config, target))

        filep.write( \
            '\n' \
            '#\n' \
            '# Directory name fragments\n' \
            '#\n\n')

        for item in self.platforms:
            filep.write('TARGET_SUFFIX_{0} = {1}\n'.format(item.getshortcode(), \
                item.getshortcode()[-3:]))
        filep.write('\n')

        for item in self.configurations:
            filep.write('CONFIG_SUFFIX_{0} = {1}\n'.format(str(item), \
                item.getshortcode()))

        filep.write( \
            '\n' \
            '#\n' \
            '# Set the set of known files supported\n' \
            '# Note: They are in the reverse order of building. .c is ' \
            'built first, then .x86\n' \
            '# until the .exe or .lib files are built\n' \
            '#\n\n' \
            '.extensions:\n' \
            '.extensions: .exe .exp .lib .obj .h .cpp .x86 .c .i86\n')

    def write_source_dir(self, filep):
        """
        Write out the list of directories for the source
        """

        # Save the refernence BURGER_SDKS
        filep.write('\n' \
            '#\n' \
            '# Ensure sdks are pulled from the environment\n' \
            '#\n\n' \
            'BURGER_SDKS = $(%BURGER_SDKS)\n')

        # Set the folders for the source code to search
        filep.write( \
            '\n#\n' \
            '# SOURCE_DIRS = Work directories for the source code\n' \
            '#\n\n')

        # Extract the directories from the files
        source_dir = []
        for item in self.code_files:
            file_name = burger.convert_to_windows_slashes(item.filename)

            # Remove the filename to get the directory
            index = file_name.rfind('\\')
            if index == -1:
                entry = file_name
            else:
                entry = file_name[0:index]
            if entry not in source_dir:
                source_dir.append(entry)

        # Sort them for consistent diffs for source control

        if source_dir:
            source_dir = sorted(source_dir)
            colon = '='
            for item in source_dir:
                filep.write('SOURCE_DIRS ' + colon + \
                    burger.encapsulate_path_linux(item) + '\n')
                colon = '+=;'
        else:
            filep.write("SOURCE_DIRS =\n")

        # Save the project name
        filep.write('\n' \
            '#\n' \
            '# Name of the output library\n' \
            '#\n\n' \
            'PROJECT_NAME = ' + self.project_name + '\n')

        # Save the base name of the temp directory
        filep.write('\n' \
            '#\n' \
            '# Base name of the temp directory\n' \
            '#\n\n' \
            'BASE_TEMP_DIR = temp/$(PROJECT_NAME)\n' \
            'BASE_SUFFIX = wat$(TARGET_SUFFIX_$(%TARGET))' \
            '$(CONFIG_SUFFIX_$(%CONFIG))\n' \
            'TEMP_DIR = $(BASE_TEMP_DIR)$(BASE_SUFFIX)\n')

        # Save the final binary output directory
        filep.write('\n' \
            '#\n' \
            '# Binary directory\n' \
            '#\n\n' \
            'DESTINATION_DIR = bin\n')

        # Extra include folders
        filep.write( \
            '\n' \
            '#\n' \
            '# INCLUDE_DIRS = Header includes\n' \
            '#\n\n' \
            'INCLUDE_DIRS = $(SOURCE_DIRS)') \

        for item in self.include_folders:
            filep.write(';' + burger.convert_to_linux_slashes(item))
        filep.write('\n')

        # Final folder if needed
        if self.final_folder:
            filep.write( \
                '\n' \
                '#\n' \
                '# Final location folder\n' \
                '#\n\n' \
                'FINAL_FOLDER = ' + \
                burger.convert_to_windows_slashes( \
                    self.final_folder, force_ending_slash=True)[:-1] + \
                '\n')

    def write_rules(self, filep):
        """
        Output the default rules for building object code
        """

        # Set the search directories for source files
        filep.write('\n' \
            '#\n' \
            '# Tell WMAKE where to find the files to work with\n' \
            '#\n' \
            '\n' \
            '.c: $(SOURCE_DIRS)\n' \
            '.cpp: $(SOURCE_DIRS)\n' \
            '.x86: $(SOURCE_DIRS)\n' \
            '.i86: $(SOURCE_DIRS)\n')

        # Global compiler flags
        filep.write('\n' \
            '#\n' \
            '# Set the compiler flags for each of the build types\n' \
            '#\n' \
            '\n' \
            'CFlagsDebug=-d_DEBUG -d2 -od\n' \
            'CFlagsInternal=-d_DEBUG -d2 -oaxsh\n' \
            'CFlagsRelease=-dNDEBUG -d0 -oaxsh\n' \
            '\n' \
            '#\n' \
            '# Set the flags for each target operating system\n' \
            '#\n' \
            '\n' \
            'CFlagscom=-bt=com -d__COM__=1 -i="$(%BURGER_SDKS)/dos/burgerlib;' \
            '$(%BURGER_SDKS)/dos/x32;$(%WATCOM)/h"\n' \
            'CFlagsdosx32=-bt=DOS -d__X32__=1 -i="$(%BURGER_SDKS)/dos/burgerlib;' \
            '$(%BURGER_SDKS)/dos/x32;$(%WATCOM)/h"\n' \
            'CFlagsdos4gw=-bt=DOS -d__DOS4G__=1 -i="$(%BURGER_SDKS)/dos/burgerlib;' \
            '$(%BURGER_SDKS)/dos/sosaudio;$(%WATCOM)/h;$(%WATCOM)/h/nt"\n' \
            'CFlagsw32=-bt=NT -dGLUT_DISABLE_ATEXIT_HACK -dGLUT_NO_LIB_PRAGMA ' \
            '-dTARGET_CPU_X86=1 -dTARGET_OS_WIN32=1 -dTYPE_BOOL=1 -dUNICODE ' \
            '-d_UNICODE -dWIN32_LEAN_AND_MEAN -i="$(%BURGER_SDKS)/windows/burgerlib;' \
            '$(%BURGER_SDKS)/windows/opengl;$(%BURGER_SDKS)/windows/directx9;' \
            '$(%BURGER_SDKS)/windows/windows5;$(%BURGER_SDKS)/windows/quicktime7;' \
            '$(%WATCOM)/h;$(%WATCOM)/h/nt"\n' \
            '\n' \
            '#\n' \
            '# Set the WASM flags for each of the build types\n' \
            '#\n' \
            '\n' \
            'AFlagsDebug=-d_DEBUG\n' \
            'AFlagsInternal=-d_DEBUG\n' \
            'AFlagsRelease=-dNDEBUG\n' \
            '\n' \
            '#\n' \
            '# Set the WASM flags for each operating system\n' \
            '#\n' \
            '\n' \
            'AFlagscom=-d__COM__=1\n' \
            'AFlagsdosx32=-d__X32__=1\n' \
            'AFlagsdos4gw=-d__DOS4G__=1\n' \
            'AFlagsw32=-d__WIN32__=1\n' \
            '\n' \
            'LFlagsDebug=\n' \
            'LFlagsInternal=\n' \
            'LFlagsRelease=\n' \
            '\n' \
            'LFlagscom=format dos com libp $(%BURGER_SDKS)/dos/burgerlib\n' \
            'LFlagsx32=system x32r libp $(%BURGER_SDKS)/dos/burgerlib;' \
            '$(%BURGER_SDKS)/dos/x32\n' \
            'LFlagsdos4gw=system dos4g libp $(%BURGER_SDKS)/dos/burgerlib;' \
            '$(%BURGER_SDKS)/dos/sosaudio\n' \
            'LFlagsw32=system nt libp $(%BURGER_SDKS)/windows/burgerlib;' \
            '$(%BURGER_SDKS)/windows/directx9 LIBRARY VERSION.lib,opengl32.lib,' \
            'winmm.lib,shell32.lib,shfolder.lib\n' \
            '\n' \
            '# Now, set the compiler flags\n' \
            '\n' \
            'CL=WCC386 -6r -fp6 -w4 -ei -j -mf -zq -zp=8 -wcd=7 -i=$(INCLUDE_DIRS)\n' \
            'CP=WPP386 -6r -fp6 -w4 -ei -j -mf -zq -zp=8 -wcd=7 -i=$(INCLUDE_DIRS)\n' \
            'ASM=WASM -5r -fp6 -w4 -zq -d__WATCOM__=1\n' \
            'LINK=*WLINK option caseexact option quiet PATH $(%WATCOM)/binnt;' \
            '$(%WATCOM)/binw;.\n' \
            '\n' \
            '# Set the default build rules\n' \
            '# Requires ASM, CP to be set\n' \
            '\n' \
            '# Macro expansion is on page 93 of the C//C++ Tools User\'s Guide\n' \
            '# $^* = C:\\dir\\target (No extension)\n' \
            '# $[* = C:\\dir\\dep (No extension)\n' \
            '# $^@ = C:\\dir\\target.ext\n' \
            '# $^: = C:\\dir\\\n' \
            '\n' \
            '.i86.obj : .AUTODEPEND\n' \
            '\t@echo $[&.i86 / $(%CONFIG) / $(%TARGET)\n' \
            '\t@$(ASM) -0 -w4 -zq -d__WATCOM__=1 $(AFlags$(%CONFIG)) ' \
            '$(AFlags$(%TARGET)) $[*.i86 -fo=$^@ -fr=$^*.err\n' \
            '\n' \
            '.x86.obj : .AUTODEPEND\n' \
            '\t@echo $[&.x86 / $(%CONFIG) / $(%TARGET)\n' \
            '\t@$(ASM) $(AFlags$(%CONFIG)) $(AFlags$(%TARGET)) ' \
            '$[*.x86 -fo=$^@ -fr=$^*.err\n' \
            '\n' \
            '.c.obj : .AUTODEPEND\n' \
            '\t@echo $[&.c / $(%CONFIG) / $(%TARGET)\n' \
            '\t@$(CP) $(CFlags$(%CONFIG)) $(CFlags$(%TARGET)) $[*.c ' \
            '-fo=$^@ -fr=$^*.err\n' \
            '\n' \
            '.cpp.obj : .AUTODEPEND\n' \
            '\t@echo $[&.cpp / $(%CONFIG) / $(%TARGET)\n' \
            '\t@$(CP) $(CFlags$(%CONFIG)) $(CFlags$(%TARGET)) $[*.cpp ' \
            '-fo=$^@ -fr=$^*.err\n')

    def write_files(self, filep):
        """
        Output the list of object files to create
        """
        filep.write( \
            '\n' \
            '#\n' \
            '# Object files to work with for the library\n' \
            '#\n\n')

        obj_list = []
        for item in self.code_files:
            if item.type == FileTypes.c or \
                item.type == FileTypes.cpp or \
                item.type == FileTypes.x86:

                tempfile = burger.convert_to_linux_slashes(item.filename)
                index = tempfile.rfind('.')
                if index == -1:
                    entry = tempfile
                else:
                    entry = tempfile[:index]

                index = entry.rfind('/')
                if index == -1:
                    entry = entry
                else:
                    entry = entry[index + 1:]

                obj_list.append(entry)

        if obj_list:
            obj_list = sorted(obj_list)
            colon = 'OBJS= '
            for item in obj_list:
                filep.write(colon + '$(A)/' + item + '.obj')
                colon = ' &\n\t'
            filep.write('\n')

        else:
            filep.write('OBJS=\n')

    def write_all_target(self, filep):
        """
        Output the "all" rule
        """

        filep.write('\n' \
            '#\n' \
            '# List the names of all of the final binaries to build\n' \
            '#\n\n' \
            'all: ')
        for item in self.configurations:
            filep.write(str(item) + ' ')
        filep.write('.SYMBOLIC\n' \
            '\t@%null\n')

        filep.write('\n' \
            '#\n' \
            '# Configurations\n' \
            '#\n\n')

        for configuration in self.configurations:
            filep.write('{0}: '.format(str(configuration)))
            for platform in self.platforms:
                filep.write(str(configuration) + platform.getshortcode() + ' ')
            filep.write('.SYMBOLIC\n' \
                '\t@%null\n\n')

        for platform in self.platforms:
            filep.write('{0}: '.format(platform.getshortcode()))
            for configuration in self.configurations:
                filep.write(str(configuration) + platform.getshortcode() + ' ')
            filep.write('.SYMBOLIC\n' \
                '\t@%null\n\n')

        if self.projecttype == ProjectTypes.library:
            suffix = 'lib'
        else:
            suffix = 'exe'

        for configuration in self.configurations:
            for platform in self.platforms:
                filep.write('{0}{1}: .SYMBOLIC\n'.format(str(configuration), \
                    platform.getshortcode()))
                filep.write('\t@if not exist "$(DESTINATION_DIR)" ' \
                    '@mkdir "$(DESTINATION_DIR)"\n')
                name = 'wat' + platform.getshortcode()[-3:] + \
                    configuration.getshortcode()
                filep.write('\t@if not exist "$(BASE_TEMP_DIR){0}" ' \
                    '@mkdir "$(BASE_TEMP_DIR){0}"\n'.format(name))
                filep.write('\t@set CONFIG=' + str(configuration) + '\n')
                filep.write('\t@set TARGET=' + platform.getshortcode() + '\n')
                filep.write('\t@%make $(DESTINATION_DIR)\\$(PROJECT_NAME)wat' + \
                    platform.getshortcode()[-3:] + \
                    configuration.getshortcode() + '.' + suffix + '\n')
                filep.write('\n')

        filep.write( \
            '#\n' \
            '# Disable building this make file\n' \
            '#\n\n' + \
            self.projectname_code + '.wmk:\n' \
            '\t@%null\n')

    def write_builds(self, filep):
        """
        Output the rule to build the exes/libs
        """

        filep.write('\n' \
            '#\n' \
            '# A = The object file temp folder\n' \
            '#\n' \
            '\n')

        if self.projecttype == ProjectTypes.library:
            suffix = '.lib'
        else:
            suffix = '.exe'

        for target in self.platforms:
            for config in self.configurations:
                filep.write('A = $(BASE_TEMP_DIR)wat' + target.getshortcode()[-3:] + \
                    config.getshortcode() + '\n' \
                    '$(DESTINATION_DIR)\\$(PROJECT_NAME)wat' + target.getshortcode()[-3:] + \
                    config.getshortcode() + \
                    suffix + ': $+$(OBJS)$- ' + self.projectname_code + '.wmk\n')
                if self.projecttype == ProjectTypes.library:

                    filep.write('\t@SET WOW=$+$(OBJS)$-\n' \
                        '\t@WLIB -q -b -c -n $^@ @WOW\n')

                    if self.final_folder:
                        filep.write('\t@"$(%perforce)\\p4" edit "$(FINAL_FOLDER)\\$^."\n' \
                            '\t@copy /y "$^@" "$(FINAL_FOLDER)\\$^."\n' \
                            '\t@"$(%perforce)\\p4" revert -a "$(FINAL_FOLDER)\\$^."\n\n')
                else:
                    filep.write('\t@SET WOW={$+$(OBJS)$-}\n' \
                        '\t@$(LINK) $(LFlags$(%TARGET)) $(LFlags$(%CONFIG)) ' \
                        'LIBRARY burgerlib$(BASE_SUFFIX).lib NAME $^@ FILE @wow\n\n')

    def write(self, filep):
        """
        Dump out the entire file
        """

        self.write_header(filep)
        self.write_source_dir(filep)
        self.write_rules(filep)
        self.write_files(filep)
        self.write_all_target(filep)
        self.write_builds(filep)


def generate(solution, perforce=False, verbose=False):
    """
    Create an OpenWatcom makefile
    """

    # Validate the requests target(s)
    platforms = solution.platform.getexpanded()

    # Special case, discard any attempt to build 64 bit windows
    try:
        platforms.remove(PlatformTypes.win64)
    except ValueError:
        pass

    for item in platforms:
        if item not in VALID_TARGETS:
            print('Error: Platform {} not supported by OpenWatcom'.format(str(item)))
            return 10

    #
    # Find the files to put into the project
    #

    codefiles, _ = solution.getfilelist( \
        [FileTypes.h, FileTypes.cpp, FileTypes.x86])

    #
    # Determine the ide and target type for the final file name
    #

    idecode = solution.ide.getshortcode()
    platformcode = solution.platform.getshortcode()
    watcom_projectfile = Project(solution.projectname, idecode, platformcode)
    project_filename = solution.projectname + idecode + platformcode + '.wmk'
    project_pathname = os.path.join( \
        solution.workingDir, project_filename)

    # Send the file list to the project
    for item in codefiles:
        watcom_projectfile.add_source_file(item)

    # Sent the include folder list to the project
    for item in solution.includefolders:
        watcom_projectfile.add_include_folder(item)

    watcom_projectfile.final_folder = solution.finalfolder
    watcom_projectfile.platforms = platforms
    watcom_projectfile.configurations = solution.configurations
    watcom_projectfile.projecttype = solution.projecttype

    #
    # Serialize the Watcom file
    #

    filep = StringIO()
    watcom_projectfile.write(filep)

    #
    # Did it change?
    #

    if burger.compare_file_to_string(project_pathname, filep):
        if solution.verbose is True:
            print(project_pathname + ' was not changed')
    else:
        if perforce:
            burger.perforce_edit(project_pathname)
        filep2 = open(project_pathname, 'w')
        filep2.write(filep.getvalue())
        filep2.close()
    filep.close()
    return 0
