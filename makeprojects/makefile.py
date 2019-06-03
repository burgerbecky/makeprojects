#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sub file for makeprojects.
Handler for Linux make projects
"""

# Copyright 1995-2019 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

#
## \package makeprojects.makefile
# This module contains classes needed to generate
# project files intended for use by make
#

from __future__ import absolute_import, print_function, unicode_literals
import os
from io import StringIO
import burger
from makeprojects import FileTypes, ProjectTypes, PlatformTypes

# pylint: disable=C0302

#
## \package makeprojects.makefile
# This module contains classes needed to generate
# project files intended for use by GNU make
#

## Array of targets that Watcom can build
VALID_TARGETS = [
    PlatformTypes.linux
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
        self.configuration_list = []

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
        filep.write(
            '#\n'
            '# Build ' + self.project_name + ' with make\n'
            '#\n')

        config = None
        for item in self.configuration_list:
            if item == 'Release':
                config = 'Release'
            elif config is None:
                config = str(item)
        if config is None:
            config = 'Release'

        target = None
        for item in self.platforms:
            if item == PlatformTypes.msdos4gw:
                target = item.get_short_code()
            elif target is None:
                target = item.get_short_code()

        filep.write(
            '\n'
            '#\n'
            '# Default configuration\n'
            '#\n\n'
            'ifndef $(CONFIG)\n'
            'CONFIG = {0}\n'
            'endif\n\n'
            '#\n'
            '# Default target\n'
            '#\n\n'
            'ifndef $(TARGET)\n'
            'TARGET = {1}\n'
            'endif\n'.format(config, target))

        filep.write(
            '\n'
            '#\n'
            '# Directory name fragments\n'
            '#\n\n')

        for item in self.platforms:
            filep.write(
                'TARGET_SUFFIX_{0} = {1}\n'.format(
                    item.get_short_code(),
                    item.get_short_code()[-3:]))
        filep.write('\n')

        for item in self.configuration_list:
            filep.write('CONFIG_SUFFIX_{0} = {1}\n'.format(
                str(item), item.get_attribute('short_code')))

        filep.write('\n'
                    '#\n'
                    '# Set the set of known files supported\n'
                    '# Note: They are in the reverse order of building. .c is '
                    'built first, then .x86\n'
                    '# until the .exe or .lib files are built\n'
                    '#\n\n'
                    '.SUFFIXES:\n'
                    '.SUFFIXES: .cpp .x86 .c .i86 .a .o .h\n')

    def write_source_dir(self, filep):
        """
        Write out the list of directories for the source
        """

        # Set the folders for the source code to search
        filep.write(
            '\n#\n'
            '# SOURCE_DIRS = Work directories for the source code\n'
            '#\n\n')

        # Extract the directories from the files
        source_dir = []
        for item in self.code_files:
            file_name = burger.convert_to_windows_slashes(
                item.relative_pathname)

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
                filep.write('SOURCE_DIRS ' + colon +
                            burger.encapsulate_path_linux(item) + '\n')
                colon = '+='
        else:
            filep.write("SOURCE_DIRS =\n")

        # Save the project name
        filep.write('\n'
                    '#\n'
                    '# Name of the output library\n'
                    '#\n\n'
                    'PROJECT_NAME = ' + self.project_name + '\n')

        # Save the base name of the temp directory
        filep.write(
            '\n'
            '#\n'
            '# Base name of the temp directory\n'
            '#\n\n'
            'BASE_TEMP_DIR = temp/$(PROJECT_NAME)\n'
            'BASE_SUFFIX = mak$(TARGET_SUFFIX_$(TARGET))$(CONFIG_SUFFIX_$(CONFIG))\n'
            'TEMP_DIR = $(BASE_TEMP_DIR)$(BASE_SUFFIX)\n')

        # Save the final binary output directory
        filep.write('\n'
                    '#\n'
                    '# Binary directory\n'
                    '#\n\n'
                    'DESTINATION_DIR = bin\n')

        # Extra include folders
        filep.write(
            '\n'
            '#\n'
            '# INCLUDE_DIRS = Header includes\n'
            '#\n\n'
            'INCLUDE_DIRS = $(SOURCE_DIRS) $(BURGER_SDKS)/linux/burgerlib')

        for item in self.include_folders:
            filep.write(' ' + burger.convert_to_linux_slashes(item))
        filep.write('\n')

        # Final folder if needed
        if self.final_folder:
            filep.write(
                '\n'
                '#\n'
                '# Final location folder\n'
                '#\n\n'
                'FINAL_FOLDER = ' +
                burger.convert_to_linux_slashes(
                    self.final_folder, force_ending_slash=True)[:-1] +
                '\n')

    def write_rules(self, filep):
        """
        Output the default rules for building object code
        """

        # Set the search directories for source files
        filep.write('\n'
                    '#\n'
                    '# Tell WMAKE where to find the files to work with\n'
                    '#\n'
                    '\n'
                    'vpath %.c $(SOURCE_DIRS)\n'
                    'vpath %.cpp $(SOURCE_DIRS)\n'
                    'vpath %.x86 $(SOURCE_DIRS)\n'
                    'vpath %.i86 $(SOURCE_DIRS)\n'
                    'vpath %.o $(TEMP_DIR)\n')

        # Global compiler flags
        filep.write(
            '\n'
            '#\n'
            '# Set the compiler flags for each of the build types\n'
            '#\n'
            '\n'
            'CFlagsDebug=-D_DEBUG -g -Og\n'
            'CFlagsInternal=-D_DEBUG -g -O3\n'
            'CFlagsRelease=-DNDEBUG -O3\n'
            '\n'
            '#\n'
            '# Set the flags for each target operating system\n'
            '#\n'
            '\n'
            'CFlagslnx= -D__LINUX__\n'
            '\n'
            '#\n'
            '# Set the WASM flags for each of the build types\n'
            '#\n'
            '\n'
            'AFlagsDebug=-D_DEBUG -g\n'
            'AFlagsInternal=-D_DEBUG -g\n'
            'AFlagsRelease=-DNDEBUG\n'
            '\n'
            '#\n'
            '# Set the as flags for each operating system\n'
            '#\n'
            '\n'
            'AFlagslnx=-D__LINUX__=1\n'
            '\n'
            'LFlagsDebug=-g -lburgerlibmaklnxdbg\n'
            'LFlagsInternal=-g -lburgerlibmaklnxint\n'
            'LFlagsRelease=-lburgerlibmaklnxrel\n'
            '\n'
            'LFlagslnx=-lGL -L$(BURGER_SDKS)/linux/burgerlib\n'
            '\n'
            '# Now, set the compiler flags\n'
            '\n'
            'C_INCLUDES=$(addprefix -I,$(INCLUDE_DIRS))\n'
            'CL=$(CXX) -c -Wall -x c++ $(C_INCLUDES)\n'
            'CP=$(CXX) -c -Wall -x c++ $(C_INCLUDES)\n'
            'ASM=$(AS)\n'
            'LINK=$(CXX)\n'
            '\n'
            '# Set the default build rules\n'
            '# Requires ASM, CP to be set\n'
            '\n'
            '# Macro expansion is GNU make User\'s Guide\n'
            '# https://www.gnu.org/software/make/manual/html_node/Automatic-Variables.html\n'
            '\n'
            '%.o: %.i86\n'
            '\t@echo $(*F).i86 / $(CONFIG) / $(TARGET)\n'
            '\t@$(ASM) $(AFlags$(CONFIG)) $(AFlags$(TARGET)) '
            '$< -o $(TEMP_DIR)/$@ -MMD -MF $(TEMP_DIR)/$(*F).d\n'
            '\n'
            '%.o: %.x86\n'
            '\t@echo $(*F).x86 / $(CONFIG) / $(TARGET)\n'
            '\t@$(ASM) $(AFlags$(CONFIG)) $(AFlags$(TARGET)) '
            '$< -o $(TEMP_DIR)/$@ -MMD -MF $(TEMP_DIR)/$(*F).d\n'
            '\n'
            '%.o: %.c\n'
            '\t@echo $(*F).c / $(CONFIG) / $(TARGET)\n'
            '\t@$(CP) $(CFlags$(CONFIG)) $(CFlags$(TARGET)) $< '
            '-o $(TEMP_DIR)/$@ -MMD -MF $(TEMP_DIR)/$(*F).d\n'
            '\t@sed -i "s:$(TEMP_DIR)/$@:$@:g" $(TEMP_DIR)/$(*F).d\n'
            '\n'
            '%.o: %.cpp\n'
            '\t@echo $(*F).cpp / $(CONFIG) / $(TARGET)\n'
            '\t@$(CP) $(CFlags$(CONFIG)) $(CFlags$(TARGET)) $< '
            '-o $(TEMP_DIR)/$@ -MMD -MF $(TEMP_DIR)/$(*F).d\n'
            '\t@sed -i "s:$(TEMP_DIR)/$@:$@:g" $(TEMP_DIR)/$(*F).d\n')

    def write_files(self, filep):
        """
        Output the list of object files to create
        """
        filep.write(
            '\n'
            '#\n'
            '# Object files to work with for the library\n'
            '#\n\n')

        obj_list = []
        for item in self.code_files:
            if item.type == FileTypes.c or \
                    item.type == FileTypes.cpp or \
                    item.type == FileTypes.x86:

                tempfile = burger.convert_to_linux_slashes(
                    item.relative_pathname)
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
                filep.write(colon + item + '.o')
                colon = ' \\\n\t'
            filep.write('\n')

        else:
            filep.write('OBJS=\n')

        filep.write('\nTRUE_OBJS = $(addprefix $(TEMP_DIR)/,$(OBJS))\n')
        filep.write('DEPS = $(addprefix $(TEMP_DIR)/,$(OBJS:.o=.d))\n')

    def write_all_target(self, filep):
        """
        Output the "all" rule
        """

        filep.write('\n'
                    '#\n'
                    '# List the names of all of the final binaries to build\n'
                    '#\n\n'
                    '.PHONY: all\n'
                    'all:')
        for item in self.configuration_list:
            filep.write(' ' + str(item))
        filep.write('\n'
                    '\t@\n')

        filep.write('\n'
                    '#\n'
                    '# Configurations\n'
                    '#\n\n')

        for configuration in self.configuration_list:
            filep.write('.PHONY: {0}\n'.format(str(configuration)))
            filep.write('{0}:'.format(str(configuration)))
            for platform in self.platforms:
                filep.write(
                    ' ' +
                    str(configuration) +
                    platform.get_short_code())
            filep.write('\n'
                        '\t@\n\n')

        for platform in self.platforms:
            filep.write('.PHONY: {0}\n'.format(platform.get_short_code()))
            filep.write('{0}:'.format(platform.get_short_code()))
            for configuration in self.configuration_list:
                filep.write(
                    ' ' +
                    str(configuration) +
                    platform.get_short_code())
            filep.write('\n'
                        '\t@\n\n')

        filep.write(
            '#\n'
            '# List the names of all of the final binaries to build\n'
            '#\n\n')

        if self.projecttype == ProjectTypes.library:
            suffix = '.a'
            prefix = 'lib'
        else:
            suffix = ''
            prefix = ''

        for configuration in self.configuration_list:
            for platform in self.platforms:
                filep.write(
                    '.PHONY: {0}{1}\n'.format(
                        str(configuration),
                        platform.get_short_code()))
                filep.write(
                    '{0}{1}:\n'.format(
                        str(configuration),
                        platform.get_short_code()))
                filep.write('\t@-mkdir -p "$(DESTINATION_DIR)"\n')
                name = 'mak' + platform.get_short_code(
                )[-3:] + configuration.get_attribute('short_code')
                filep.write('\t@-mkdir -p "$(BASE_TEMP_DIR){0}"\n'.format(name))
                filep.write(
                    '\t@$(MAKE) -e CONFIG=' + str(configuration) + ' TARGET=' +
                    platform.get_short_code() + ' -f ' + self.projectname_code +
                    '.mak'
                    ' $(DESTINATION_DIR)/' + prefix + '$(PROJECT_NAME)mak' +
                    platform.get_short_code()[-3:] +
                    configuration.get_attribute('short_code') + suffix + '\n')
                filep.write('\n')

        filep.write(
            '#\n'
            '# Disable building this make file\n'
            '#\n'
            '\n' +
            self.projectname_code + '.mak:\n'
            '\t@\n')

    def write_builds(self, filep):
        """
        Output the rule to build the exes/libs
        """

        filep.write('\n'
                    '#\n'
                    '# A = The object file temp folder\n'
                    '#\n'
                    '\n')

        if self.projecttype == ProjectTypes.library:
            suffix = '.a'
            prefix = 'lib'
        else:
            suffix = ''
            prefix = ''

        for theplatform in self.platforms:
            for target in self.configuration_list:
                filep.write('$(DESTINATION_DIR)/' + prefix + '$(PROJECT_NAME)mak' +
                            theplatform.get_short_code()[-3:] +
                            target.get_attribute('short_code') +
                            suffix + ': $(OBJS) ' + self.projectname_code + '.mak\n')
                if self.projecttype == ProjectTypes.library:
                    filep.write('\t@ar -rcs $@ $(TRUE_OBJS)\n')
                    if self.final_folder:
                        filep.write(
                            '\t@-p4 edit "$(FINAL_FOLDER)/$(@F)"\n'
                            '\t@-cp -T "$@" "$(FINAL_FOLDER)/$(@F)"\n'
                            '\t@-p4 revert -a "$(FINAL_FOLDER)/$(@F)"\n')
                else:
                    filep.write(
                        '\t@$(LINK) -o $@ $(TRUE_OBJS) $(LFlags$(TARGET)) $(LFlags$(CONFIG))\n')
                    if self.final_folder:
                        if target == 'Release':
                            filep.write(
                                '\t@-p4 edit "$(FINAL_FOLDER)/$(PROJECT_NAME)"\n'
                                '\t@-cp -T "$@" "$(FINAL_FOLDER)/$(PROJECT_NAME)"\n'
                                '\t@-p4 revert -a "$(FINAL_FOLDER)/$(PROJECT_NAME)"\n')
                filep.write('\n')

        filep.write(
            '%.d:\n'
            '\t@\n\n'
            '%: %,v\n\n'
            '%: RCS/%,v\n\n'
            '%: RCS/%\n\n'
            '%: s.%\n\n'
            '%: SCCS/s.%\n\n'
            '%.h:\n'
            '\t@\n\n'
            '# Include the generated dependencies\n'
            '-include $(DEPS)\n')

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


def generate(solution):
    """
    Create an OpenWatcom makefile
    """

    # Validate the requests target(s)
    platforms = solution.project_list[0].get_attribute('platform').get_expanded()

    # Special case, discard any attempt to build 64 bit windows
    try:
        platforms.remove(PlatformTypes.win64)
    except ValueError:
        pass

    for item in platforms:
        if item not in VALID_TARGETS:
            print('Error: Platform {} not supported by Makefile'.format(str(item)))
            return 10

    #
    # Find the files to put into the project
    #

    codefiles, _ = solution.getfilelist(
        [FileTypes.h, FileTypes.cpp, FileTypes.x86])

    #
    # Determine the ide and target type for the final file name
    #

    idecode = solution.ide.get_short_code()
    platformcode = solution.project_list[0].get_attribute(
        'platform').get_short_code()
    make_projectfile = Project(
        solution.get_attribute('name'),
        idecode, platformcode)
    project_filename = solution.attributes['name'] + \
        idecode + platformcode + '.mak'
    project_pathname = os.path.join(
        solution.attributes['working_directory'], project_filename)

    # Send the file list to the project
    for item in codefiles:
        make_projectfile.add_source_file(item)

    # Sent the include folder list to the project
    for item in solution.project_list[0].get_attribute('include_folders_list'):
        make_projectfile.add_include_folder(item)

    make_projectfile.platforms = platforms
    make_projectfile.configurations = []
    for configuration in solution.project_list[0].configurations:
        if configuration.attributes.get('deploy_folder'):
            make_projectfile.final_folder = configuration.attributes.get(
                'deploy_folder')
        make_projectfile.configurations.append(configuration.attributes['name'])
    make_projectfile.projecttype = solution.project_list[0].get_attribute(
        'project_type')

    #
    # Serialize the Watcom file
    #

    filep = StringIO()
    make_projectfile.write(filep)

    #
    # Did it change?
    #

    if burger.compare_file_to_string(project_pathname, filep):
        if solution.get_attribute('verbose'):
            print(project_pathname + ' was not changed')
    else:
        if solution.get_attribute('perforce'):
            burger.perforce_edit(project_pathname)
        filep2 = open(project_pathname, 'w')
        filep2.write(filep.getvalue())
        filep2.close()
    filep.close()
    return 0
