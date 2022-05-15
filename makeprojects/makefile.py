#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sub file for makeprojects.
Handler for Linux make projects

@package makeprojects.makefile
This module contains classes needed to generate
project files intended for use by make
"""

# Copyright 1995-2022 by Rebecca Ann Heineman becky@burgerbecky.com

# It is released under an MIT Open Source license. Please see LICENSE
# for license details. Yes, you can use it in a
# commercial title without paying anything, just give me a credit.
# Please? It's not like I'm asking you for money!

from __future__ import absolute_import, print_function, unicode_literals

import os
from burger import save_text_file_if_newer, encapsulate_path_linux, \
    convert_to_linux_slashes

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

                configuration.make_name = configuration.name + \
                    configuration.platform.get_short_code()

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
            '#',
            '# Generated with makeprojects',
            '#'])
        return 0

    ########################################

    def write_default_goal(self, line_list):
        """
        Write the default goal for the makefile
        """

        default_goal = 'all'

        line_list.extend([
            '',
            '#',
            '# Project to build without a goal',
            '#',
            '',
            '.DEFAULT_GOAL := ' + default_goal])
        return 0

    ########################################

    def write_phony_targets(self, line_list):
        """
        Output all of the .PHONY targets
        """

        # Generate list of build targets
        target_list = ['all:']
        for item in self.configuration_names:
            target_list.append(item.name)

        line_list.extend([
            '',
            '#',
            '# List the names of all of the final binaries to build',
            '#',
            '',
            '.PHONY: all',
            ' '.join(target_list) + ' ;'
        ])

        # Generate the list of configurations
        if self.configuration_names:
            line_list.extend([
                '',
                '#',
                '# Configurations',
                '#'
            ])

            for configuration in self.configuration_names:
                target_list = [configuration.name + ':']
                for platform in self.platforms:
                    target_list.append(
                        configuration.name +
                        platform.get_short_code())
                line_list.extend(['',
                                  '.PHONY: ' + configuration.name,
                                  ' '.join(target_list) + ' ;'
                                  ])

        # Generate a list of platforms
        if self.platforms:
            line_list.extend([
                '',
                '#',
                '# Platforms',
                '#'
            ])

            for platform in self.platforms:
                target_list = [platform.get_short_code() + ':']
                for configuration in self.configuration_list:
                    target_list.append(
                        configuration.name +
                        platform.get_short_code())
                line_list.extend(['',
                                  '.PHONY: ' + platform.get_short_code(),
                                  ' '.join(target_list) + ' ;'])

        # Generate the list of final binaries
        if self.configuration_list:

            line_list.extend([
                '',
                '#',
                '# List the names of all of the final binaries to build',
                '#'
            ])

            for configuration in self.configuration_list:
                if configuration.project_type is ProjectTypes.library:
                    template = 'lib{}.a'
                else:
                    template = '{}'

                platform_short_code = configuration.platform.get_short_code()
                target_name = configuration.name + platform_short_code
                line_list.extend([
                    '',
                    '.PHONY: ' + target_name,
                    target_name + ':',
                    '\t@$(MAKE) -e --no-print-directory CONFIG=' +
                    configuration.name +
                    ' TARGET=' + platform_short_code +
                    ' -f ' + self.solution.makefile_filename +
                    ' bin/' + template.format(self.solution.name + 'mak' +
                                              platform_short_code[-3:] +
                                              configuration.short_code)
                ])

        # Generate the "clean" target
        if self.configuration_list:
            line_list.extend([
                '',
                '#',
                '# Clean all binaries',
                '#',
                '',
                '.PHONY: clean',
                'clean:'
            ])
            remove_list = ['\t@-rm -rf']
            for configuration in self.configuration_list:
                remove_list.append(
                    'temp/' + self.solution.name + 'mak' +
                    configuration.platform.get_short_code()[-3:] +
                    configuration.short_code)
            line_list.append(' '.join(remove_list))

            remove_list = ['\t@-rm -f']
            for configuration in self.configuration_list:
                if configuration.project_type is ProjectTypes.library:
                    template = 'lib{}.a'
                else:
                    template = '{}'

                remove_list.append(
                    'bin/' +
                    template.format(
                        self.solution.name + 'mak' +
                        configuration.platform.get_short_code()[-3:] +
                        configuration.short_code))
            line_list.append(' '.join(remove_list))

            # Test if the directory is empty, if so, delete the directory
            line_list.append('\t@if [ -d bin ] && files=$$(ls -qAL -- bin) '
                             '&& [ -z "$$files" ]; then rm -fd bin; fi')
        return 0

    ########################################

    def write_directory_targets(self, line_list):
        """
        Create directory and make file targets
        """

        line_list.extend([
            '',
            '#',
            '# Create the folder for the binary output',
            '#',
            '',
            'bin:',
            '\t@-mkdir -p bin'
        ])

        line_list.extend([
            '',
            '#',
            '# Disable building this make file',
            '#',
            '',
            self.solution.makefile_filename + ': ;'])
        return 0

    ########################################

    def write_test_variables(self, line_list):
        """
        Create tests for environment variables
        """

        variable_list = ['BURGER_SDKS']

        if variable_list:
            line_list.extend([
                '',
                '#',
                '# Required environment variables',
                '#'
            ])
            for variable in variable_list:
                line_list.extend([
                    '',
                    'ifndef ' + variable,
                    ('$(error the environment variable {} '
                     'was not declared)').format(variable),
                    'endif'
                ])
        return 0

    ########################################

    def write_configurations(self, line_list):
        """
        Write configuration list
        """

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
            'CONFIG ?= ' + config
        ])

        # Default platform
        target = None
        # Get all the configuration names
        for platform in self.platforms:
            if platform is PlatformTypes.linux:
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
            'TARGET ?= ' + target
        ])

        line_list.extend([
            '',
            '#',
            '# Directory name fragments',
            '#',
        ])

        # List all platforms
        line_list.append('')
        for platform in self.platforms:
            line_list.append(
                'TARGET_SUFFIX_{0} := {1}'.format(
                    platform.get_short_code(),
                    platform.get_short_code()[-3:]))

        # List all configurations
        line_list.append('')
        for item in self.configuration_list:
            line_list.append(
                'CONFIG_SUFFIX_{0} := {1}'.format(
                    item.name, item.short_code))

        # Save the base name of the temp directory
        line_list.extend([
            '',
            '#',
            '# Base name of the temp directory',
            '#',
            '',
            'BASE_SUFFIX := mak$(TARGET_SUFFIX_$'
            '(TARGET))$(CONFIG_SUFFIX_$(CONFIG))',
            'TEMP_DIR := temp/{0}$(BASE_SUFFIX)'.format(self.solution.name)
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
            colon = ':='
            for item in sorted(source_folders):
                line_list.append(
                    'SOURCE_DIRS ' +
                    colon +
                    encapsulate_path_linux(item))
                colon = '+='
        else:
            line_list.append('SOURCE_DIRS :=')

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

        # Global compiler flags
        line_list.extend([
            '',
            '#',
            '# Set the compiler flags for each of the build types',
            '#',
            ''])

        for configuration in self.configuration_list:
            entries = ['CFlags' + configuration.make_name + ':=']

            # Enable debug information
            if configuration.debug:
                entries.append('-g')

            # Enable optimization
            if configuration.optimization:
                entries.append('-O3')
            else:
                entries.append('-Og')

            # Add defines
            define_list = configuration.get_chained_list('define_list')
            for item in define_list:
                entries.append('-D' + item)

            line_list.append(' '.join(entries))

        # Global assembler flags
        line_list.extend([
            '',
            '#',
            '# Set the WASM flags for each of the build types',
            '#',
            ''])

        for configuration in self.configuration_list:
            entries = ['AFlags' + configuration.make_name + ':=']

            # Enable debug information
            if configuration.debug:
                entries.append('-g')

            # Add defines
            define_list = configuration.get_chained_list('define_list')
            for item in define_list:
                entries.append('-D' + item)

            line_list.append(' '.join(entries))

        # Global linker flags
        line_list.extend([
            '',
            '#',
            '# Set the Linker flags for each of the build types',
            '#',
            ''])

        for configuration in self.configuration_list:
            entries = ['LFlags' + configuration.make_name + ':=']

            # Enable debug information
            if configuration.debug:
                entries.append('-g')

            # Add libraries

            if not configuration.project_type.is_library():
                lib_list = configuration.get_unique_chained_list(
                    'libraries_list')

                for item in lib_list:
                    entries.append('-l' + item)

                lib_list = configuration.get_unique_chained_list(
                    'library_folders_list')
                for item in lib_list:
                    entries.append('-L' + item)

            line_list.append(' '.join(entries))

        # Build rules
        line_list.extend([
            '',
            '# Now, set the compiler flags',
            '',
            'C_INCLUDES:=$(addprefix -I,$(INCLUDE_DIRS))',
            'CL:=$(CXX) -c -Wall -x c++ $(C_INCLUDES)',
            'CP:=$(CXX) -c -Wall -x c++ $(C_INCLUDES)',
            'ASM:=$(AS)',
            'LINK:=$(CXX)',
            '',
            '#',
            '# Default build recipes',
            '#',
            '',
            'define BUILD_CPP=',
            '@echo $(<F) / $(CONFIG) / $(TARGET); \\',
            '$(CP) $(CFlags$(CONFIG)$(TARGET)) $< -o $@ '
            '-MT \'$@\' -MMD -MF \'$*.d\'',
            'endef'
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
            colon = 'OBJS:= '
            for item in sorted(obj_list):
                line_list.append(colon + '$(TEMP_DIR)/' + item + '.o \\')
                colon = '\t'
            # Remove the ' &' from the last line
            line_list[-1] = line_list[-1][:-2]

            line_list.append('')
            colon = 'DEPS:= '
            for item in sorted(obj_list):
                line_list.append(colon + '$(TEMP_DIR)/' + item + '.d \\')
                colon = '\t'
            # Remove the ' &' from the last line
            line_list[-1] = line_list[-1][:-2]

        else:
            line_list.append('OBJS:=')
            line_list.append('DEPS:=')

        return 0

    def write_all_target(self, line_list):
        """
        Output the "all" rule
        """

        source_list = []
        if self.solution.project_list:
            codefiles = self.solution.project_list[0].codefiles
        else:
            codefiles = []

        for item in codefiles:
            if item.type is FileTypes.c or \
                    item.type is FileTypes.cpp or \
                    item.type is FileTypes.x86:

                entry = convert_to_linux_slashes(
                    item.relative_pathname)
                source_list.append(entry)

        if source_list:
            line_list.extend([
                '',
                '#',
                '# Disable building the source files',
                '#',
                ''
            ])
            items = ' '.join(source_list)
            line_list.append(items + ': ;')

            line_list.extend([
                '',
                '#',
                '# Build the object file folder',
                '#',
                '',
                '$(OBJS): | $(TEMP_DIR)',
                '',
                '$(TEMP_DIR):',
                '\t@-mkdir -p $(TEMP_DIR)'
            ])

            line_list.extend([
                '',
                '#',
                '# Build the object files',
                '#',
            ])
            for item in source_list:

                # Hack off the .cpp extension
                index = item.rfind('.')
                if index == -1:
                    entry = item
                else:
                    entry = item[:index]

                # Hack off the directory prefix
                index = entry.rfind('/')
                if index != -1:
                    entry = entry[index + 1:]

                line_list.extend(
                    ['',
                     '$(TEMP_DIR)/{0}.o: {1} ; $(BUILD_CPP)'.format(entry, item)
                     ])
        return 0

    def write_builds(self, line_list):
        """
        Output the rule to build the exes/libs
        """

        line_list.extend([
            '',
            '#',
            '# Create final binaries',
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
                'bin/' + prefix + self.solution.name + 'mak' +
                configuration.platform.get_short_code()[-3:] +
                configuration.short_code +
                suffix + ': $(OBJS) ' +
                self.solution.makefile_filename + ' | bin')
            if configuration.project_type is ProjectTypes.library:
                line_list.append('\t@ar -rcs $@ $(OBJS)')
                if configuration.deploy_folder:
                    deploy_folder = convert_to_linux_slashes(
                        configuration.deploy_folder,
                        force_ending_slash=True)[:-1]
                    line_list.extend(
                        [
                            '\t@if [ -f /bin/wslpath ]; then \\',
                            '\tp4.exe edit $$(wslpath -a -w \'{}/$(@F)\'); \\'.format(deploy_folder),
                            '\tcp -T "$@" "{}/$(@F)"; \\'.format(deploy_folder),
                            '\tp4.exe revert -a $$(wslpath -a -w \'{}/$(@F)\'); \\'.format(deploy_folder),
                            '\telse \\',
                            '\tp4 edit "{}/$(@F)"; \\'.format(deploy_folder),
                            '\tcp -T "$@" "{}/$(@F)"; \\'.format(deploy_folder),
                            '\tp4 revert -a "{}/$(@F)"; \\'.format(deploy_folder),
                            '\tfi'])
            else:
                line_list.append(
                    '\t@$(LINK) -o $@ $(OBJS) '
                    '$(LFlags$(CONFIG)$(TARGET))')
                if configuration.deploy_folder:
                    deploy_folder = convert_to_linux_slashes(
                        configuration.deploy_folder,
                        force_ending_slash=True)[:-1]
                    line_list.extend([
                        '\t@-p4 edit "{}/{}"'.format(
                            deploy_folder, self.solution.name),
                        '\t@-cp -T "$^@" "{}/{}"'.format(
                            deploy_folder, self.solution.name),
                        '\t@-p4 revert -a "{}/{}"'.format(
                            deploy_folder, self.solution.name)
                    ])

        line_list.append('')
        line_list.extend([
            '%.d: ;',
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
            '%.h: ;',
            '',
            '#',
            '# Include the generated dependencies',
            '#',
            '',
            '-include $(DEPS)'
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
        self.write_default_goal(line_list)
        self.write_phony_targets(line_list)
        self.write_directory_targets(line_list)

        line_list.extend(['',
                          '#',
                          '# Code below can only be invoked indirectly',
                          '#',
                          '',
                          'ifneq (0,$(MAKELEVEL))'])

        # Write out the records that are only value if
        # TARGET and CONFIG are set
        self.write_test_variables(line_list)
        self.write_configurations(line_list)
        self.write_source_dir(line_list)
        self.write_rules(line_list)
        self.write_files(line_list)
        self.write_all_target(line_list)
        self.write_builds(line_list)

        # Release the endif
        line_list.extend(['', 'endif'])
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
