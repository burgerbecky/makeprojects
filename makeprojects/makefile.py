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
from burger import save_text_file_if_newer, encapsulate_path_linux, \
    convert_to_linux_slashes, convert_to_windows_slashes

from makeprojects import FileTypes, ProjectTypes, PlatformTypes, IDETypes

# pylint: disable=C0302

SUPPORTED_IDES = (IDETypes.make,)

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

    return platform_type is PlatformTypes.linux


########################################

class Project(object):
    """
    Root object for a Watcom IDE project file
    Created with the name of the project, the IDE code
    the platform code (4gw, x32, win)
    """

    def __init__(self, solution):
        """
        Initialize the exporter.
        """

        ## Parent solution
        self.solution = solution

        ## List of all platform types
        self.platforms = []

        ## List of all configurations
        self.configuration_list = []

        ## List of configuration names
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
        Write the header for a gnu makefile
        """

        line_list.extend([
            '#',
            '# Build ' + self.solution.name + ' with make',
            '#'])

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
            'ifndef $(CONFIG)',
            'CONFIG = ' + config,
            'endif'
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
            'ifndef $(TARGET)',
            'TARGET = ' + target,
            'endif'
        ])

        line_list.extend([
            '',
            '#',
            '# Directory name fragments',
            '#',
        ])

        line_list.append('')
        for platform in self.platforms:
            line_list.append(
                'TARGET_SUFFIX_{0} = {1}'.format(
                    platform.get_short_code(),
                    platform.get_short_code()[-3:]))

        line_list.append('')
        for item in self.configuration_list:
            line_list.append(
                'CONFIG_SUFFIX_{0} = {1}'.format(
                    item.name, item.short_code))

        line_list.extend([
            '',
            '#',
            '# Set the set of known files supported',
            '# Note: They are in the reverse order of building. .c is '
            'built first, then .x86',
            '# until the .exe or .lib files are built',
            '#',
            '',
            '.SUFFIXES:',
            '.SUFFIXES: .cpp .x86 .c .i86 .a .o .h'
        ])
        return 0

    def write_source_dir(self, line_list):
        """
        Write out the list of directories for the source
        """

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
                colon = '+='
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
            'BASE_SUFFIX = mak$(TARGET_SUFFIX_$'
            '(TARGET))$(CONFIG_SUFFIX_$(CONFIG))',
            'TEMP_DIR = $(BASE_TEMP_DIR)$(BASE_SUFFIX)',
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
            'INCLUDE_DIRS = $(SOURCE_DIRS) $(BURGER_SDKS)/linux/burgerlib'
        ])

        for item in include_folders:
            line_list.append(
                'INCLUDE_DIRS +=' +
                convert_to_linux_slashes(item))
        return 0

    def write_rules(self, line_list):
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
            'vpath %.c $(SOURCE_DIRS)',
            'vpath %.cpp $(SOURCE_DIRS)',
            'vpath %.x86 $(SOURCE_DIRS)',
            'vpath %.i86 $(SOURCE_DIRS)',
            'vpath %.o $(TEMP_DIR)'
        ])

        # Global compiler flags
        line_list.extend([
            '',
            '#',
            '# Set the compiler flags for each of the build types',
            '#',
            '',
            'CFlagsDebug=-D_DEBUG -g -Og',
            'CFlagsInternal=-D_DEBUG -g -O3',
            'CFlagsRelease=-DNDEBUG -O3',
            '',
            '#',
            '# Set the flags for each target operating system',
            '#',
            '',
            'CFlagslnx= -D__LINUX__',
            '',
            '#',
            '# Set the WASM flags for each of the build types',
            '#',
            '',
            'AFlagsDebug=-D_DEBUG -g',
            'AFlagsInternal=-D_DEBUG -g',
            'AFlagsRelease=-DNDEBUG',
            '',
            '#',
            '# Set the as flags for each operating system',
            '#',
            '',
            'AFlagslnx=-D__LINUX__=1',
            '',
            'LFlagsDebug=-g -lburgerlibmaklnxdbg',
            'LFlagsInternal=-g -lburgerlibmaklnxint',
            'LFlagsRelease=-lburgerlibmaklnxrel',
            '',
            'LFlagslnx=-lGL -L$(BURGER_SDKS)/linux/burgerlib',
            '',
            '# Now, set the compiler flags',
            '',
            'C_INCLUDES=$(addprefix -I,$(INCLUDE_DIRS))',
            'CL=$(CXX) -c -Wall -x c++ $(C_INCLUDES)',
            'CP=$(CXX) -c -Wall -x c++ $(C_INCLUDES)',
            'ASM=$(AS)',
            'LINK=$(CXX)',
            '',
            '# Set the default build rules',
            '# Requires ASM, CP to be set',
            '',
            '# Macro expansion is GNU make User\'s Guide',
            '# https://www.gnu.org/software/make/'
            'manual/html_node/Automatic-Variables.html',
            '',
            '%.o: %.i86',
            '\t@echo $(*F).i86 / $(CONFIG) / $(TARGET)',
            '\t@$(ASM) $(AFlags$(CONFIG)) $(AFlags$(TARGET)) '
            '$< -o $(TEMP_DIR)/$@ -MMD -MF $(TEMP_DIR)/$(*F).d',
            '',
            '%.o: %.x86',
            '\t@echo $(*F).x86 / $(CONFIG) / $(TARGET)',
            '\t@$(ASM) $(AFlags$(CONFIG)) $(AFlags$(TARGET)) '
            '$< -o $(TEMP_DIR)/$@ -MMD -MF $(TEMP_DIR)/$(*F).d',
            '',
            '%.o: %.c',
            '\t@echo $(*F).c / $(CONFIG) / $(TARGET)',
            '\t@$(CP) $(CFlags$(CONFIG)) $(CFlags$(TARGET)) $< '
            '-o $(TEMP_DIR)/$@ -MMD -MF $(TEMP_DIR)/$(*F).d',
            '\t@sed -i "s:$(TEMP_DIR)/$@:$@:g" $(TEMP_DIR)/$(*F).d',
            '',
            '%.o: %.cpp',
            '\t@echo $(*F).cpp / $(CONFIG) / $(TARGET)',
            '\t@$(CP) $(CFlags$(CONFIG)) $(CFlags$(TARGET)) $< '
            '-o $(TEMP_DIR)/$@ -MMD -MF $(TEMP_DIR)/$(*F).d',
            '\t@sed -i "s:$(TEMP_DIR)/$@:$@:g" $(TEMP_DIR)/$(*F).d'
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
                line_list.append(colon + item + '.o \\')
                colon = '\t'
            # Remove the ' &' from the last line
            line_list[-1] = line_list[-1][:-2]

        else:
            line_list.append('OBJS=')

        line_list.append('')
        line_list.append('TRUE_OBJS = $(addprefix $(TEMP_DIR)/,$(OBJS))')
        line_list.append('DEPS = $(addprefix $(TEMP_DIR)/,$(OBJS:.o=.d))')
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
            '',
            '.PHONY: all'
        ])

        target_list = ['all:']
        for item in self.configuration_names:
            target_list.append(item.name)
        line_list.append(' '.join(target_list))
        line_list.append('\t@')

        line_list.extend([
            '',
            '#',
            '# Configurations',
            '#'
        ])

        # Build targets for configuations
        for configuration in self.configuration_names:
            line_list.append('')
            line_list.append('.PHONY: ' + configuration.name)
            target_list = [configuration.name + ':']
            for platform in self.platforms:
                target_list.append(
                    configuration.name +
                    platform.get_short_code())
            line_list.append(' '.join(target_list))
            line_list.append('\t@')

        for platform in self.platforms:
            line_list.append('')
            line_list.append('.PHONY: ' + platform.get_short_code())
            target_list = [platform.get_short_code() + ':']
            for configuration in self.configuration_list:
                target_list.append(
                    configuration.name +
                    platform.get_short_code())
            line_list.append(' '.join(target_list))
            line_list.append('\t@')

        line_list.extend([
            '',
            '#',
            '# List the names of all of the final binaries to build',
            '#'
        ])

        for configuration in self.configuration_list:
            if configuration.project_type is ProjectTypes.library:
                suffix = '.a'
                prefix = 'lib'
            else:
                suffix = ''
                prefix = ''
            platform = configuration.platform
            line_list.append('')
            line_list.append(
                '.PHONY: ' + configuration.name + platform.get_short_code())
            line_list.append(
                '{0}{1}:'.format(
                    configuration.name,
                    platform.get_short_code()))
            line_list.append('\t@-mkdir -p "$(DESTINATION_DIR)"')
            name = 'mak' + platform.get_short_code(
            )[-3:] + configuration.short_code
            line_list.append(
                '\t@-mkdir -p "$(BASE_TEMP_DIR){0}"'.format(name))
            line_list.append(
                '\t@$(MAKE) -e CONFIG=' + configuration.name + ' TARGET=' +
                platform.get_short_code() + ' -f ' +
                self.solution.makefile_filename +
                ' $(DESTINATION_DIR)/' + prefix + '$(PROJECT_NAME)mak' +
                platform.get_short_code()[-3:] +
                configuration.short_code + suffix)

        line_list.extend([
            '',
            '#',
            '# Disable building this make file',
            '#',
            '',
            self.solution.makefile_filename + ':',
            '\t@'])
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
            if configuration.project_type == ProjectTypes.library:
                suffix = '.a'
                prefix = 'lib'
            else:
                suffix = ''
                prefix = ''

            line_list.append('')
            line_list.append(
                '$(DESTINATION_DIR)/' + prefix + '$(PROJECT_NAME)mak' +
                configuration.platform.get_short_code()[-3:] +
                configuration.short_code +
                suffix + ': $(OBJS) ' + self.solution.makefile_filename)
            if configuration.project_type is ProjectTypes.library:
                line_list.append('\t@ar -rcs $@ $(TRUE_OBJS)')
                if configuration.deploy_folder:
                    deploy_folder = convert_to_windows_slashes(
                        configuration.deploy_folder,
                        force_ending_slash=True)[:-1]
                    line_list.extend([
                        '\t@-p4 edit "{}/$(@F)"'.format(
                            deploy_folder),
                        '\t@-cp -T "$@" "{}/$(@F)"'.format(
                            deploy_folder),
                        '\t@-p4 revert -a "{}/$(@F)"'.format(
                            deploy_folder)
                        ])
            else:
                line_list.append(
                    '\t@$(LINK) -o $@ $(TRUE_OBJS) '
                    '$(LFlags$(TARGET)) $(LFlags$(CONFIG))')
                if configuration.deploy_folder:
                    deploy_folder = convert_to_windows_slashes(
                        configuration.deploy_folder,
                        force_ending_slash=True)[:-1]
                    line_list.extend([
                        '\t@-p4 edit "{}/$(PROJECT_NAME)'.format(
                            deploy_folder),
                        '\t@-cp -T "$^@" "{}/$(PROJECT_NAME)'.format(
                            deploy_folder),
                        '\t@-p4 revert -a "{}/$(PROJECT_NAME)'.format(
                            deploy_folder)
                    ])

        line_list.append('')
        line_list.extend([
            '%.d:',
            '\t@',
            '',
            '%: %,v',
            '',
            '%: RCS/%,v',
            '',
            '%: RCS/%',
            '',
            '%: s.%',
            '',
            '%: SCCS/s.%',
            '',
            '%.h:',
            '\t@',
            '',
            '# Include the generated dependencies',
            '-include $(DEPS)',
            ])
        return 0

    ########################################

    def generate(self, line_list=None):
        """
        Write out the makefile project.

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


def generate(solution):
    """
    Create a gnu makefile
    """

    # Failsafe
    if solution.ide not in SUPPORTED_IDES:
        return 10

    # Create the output filename and pass it to the generator
    # so it can reference itself in make targets
    solution.makefile_filename = '{}{}{}.mak'.format(
        solution.name, solution.ide_code, solution.platform_code)

    exporter = Project(solution)

    # Output the actual project file
    makefile_lines = []
    error = exporter.generate(makefile_lines)
    if error:
        return error

    # Save the file if it changed
    save_text_file_if_newer(
        os.path.join(solution.working_directory, solution.makefile_filename),
        makefile_lines,
        bom=False,
        perforce=solution.perforce,
        verbose=solution.verbose)
    return 0
