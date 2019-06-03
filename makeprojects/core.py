#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module contains the core classes for makeproject.
"""

## \package makeprojects.core

from __future__ import absolute_import, print_function, unicode_literals

import os
from operator import attrgetter
from copy import deepcopy
from burger import get_windows_host_type, convert_to_windows_slashes, \
    convert_to_linux_slashes, is_string, translate_to_regex_match

from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes
from .build_rules import rules as default_rules

## List of attributes that consist of lists

_DEFAULT_ATTRIBUTE_LISTS = (
    'define_list',
    'exclude_from_build_list',
    '_source_include_list',
    'include_folders_list',
    'library_folders_list',
    'libraries_list',
    'frameworks_list'
)

########################################


def validate_type(self, attribute_name, data_type):
    """
    Verify an attribute is a specific data type.

    Check if the attribute exists and if so, verify it's an instance of a
    specfic data type. If so, exit immediately. If the record doesn't exist,
    create it with the default of None. If the record contains a string,
    call the lookup() function of the data type for conversion.

    Args:
        self: Class the contains a member called ``attributes``.
        attribute_name: Name of the attribute to check.
        data_type: Type instance of the class type to match.

    Returns:
        Value found in the attribute.

    Exception:
        TypeError if lookup() failed.
    """

    # Ensure the entry exists
    data = self.attributes.setdefault(attribute_name)
    if data is not None:
        if not isinstance(data, data_type):
            # Perform the lookup
            new_data = data_type.lookup(data)
            if new_data is None:
                msg = '["{}"]={} must be of type "{}".'.format(
                    attribute_name, data, data_type.__name__)
                raise TypeError(msg)
            # Save the converted type
            self.attributes[attribute_name] = new_data
            return new_data
    return data

########################################


def source_file_filter(file_list, file_type_list):
    """
    Prune the file list for a specific type.

    Args:
        file_list: list of SourceFile entries.
        file_type_list: FileTypes to match.
    Returns:
        list of matching SourceFile entries.
    """

    result_list = []

    # Convert to an iterable if a single item was passed
    if isinstance(file_type_list, FileTypes):
        for item in file_list:
            if item.type is file_type_list:
                result_list.append(item)
    else:
        for item in file_list:
            if item.type in file_type_list:
                result_list.append(item)
    return result_list


########################################


class SourceFile():
    """
    Object for each input file to insert to a solution.

    For every file that could be included into a project file
    one of these objects is created and attached to a Project object
    for processing.
    """

    def __init__(self, relative_pathname, working_directory, filetype):
        """
        Default constructor.

        Args:
            relative_pathname: Filename of the input file (relative to the root)
            working_directory: Pathname of the root directory
            filetype: Compiler to apply
        See Also:
            enums.FileTypes
        """

        # Sanity check
        if not isinstance(filetype, FileTypes):
            raise TypeError("parameter 'filetype' must be of type FileTypes")

        ## File base name with extension using windows style slashes
        self.relative_pathname = convert_to_windows_slashes(relative_pathname)

        ## Directory the file is relative to.
        self.working_directory = working_directory

        ## File type enumeration, see: \ref enums.FileTypes
        self.type = filetype

    ########################################

    def get_group_name(self):
        r"""
        Get the group location for this source file.
        @details
        To determine if the file should be in a sub group in the project, scan
        the filename to find if it's a base filename or part of a directory.
        If it's a basename, return an empty string.
        If it's in a folder, remove any ``..\`` prefixes and ``.\`` prefixes
        and return the filename with the basename removed.

        Returns:
            The group name string with ``\`` delimiters.
        """

        # Check if there's a group
        slash = '\\'
        index = self.relative_pathname.rfind(slash)
        if index == -1:
            slash = '/'
            index = self.relative_pathname.rfind(slash)
            if index == -1:
                return ''

        # Remove the basename
        group_name = self.relative_pathname[:index]

        # If there are ..\\ at the beginning, remove them

        while group_name.startswith('..' + slash):
            group_name = group_name[3:]

        # If there is a .\\, remove the single prefix
        while group_name.startswith('.' + slash):
            group_name = group_name[2:]

        return group_name

    def get_abspath(self):
        """
        Return the full pathname of the file entry.

        Returns:
            Absolute pathname for the file.
        """

        if get_windows_host_type():
            file_name = self.relative_pathname
        else:
            file_name = convert_to_linux_slashes(self.relative_pathname)
        return os.path.abspath(os.path.join(self.working_directory, file_name))

    def __repr__(self):
        """
        Convert the file record into a human readable file description.

        Returns:
            Human readable string.
        """

        return 'FileType: {} Pathname: "{}"'.format(str(self.type),
                                                    self.get_abspath())

    ## Allow str() to work.
    __str__ = __repr__


########################################


class Configuration:
    """
    Object for containing attributes specific to a build configuration.

    This object contains all of the items needed to create a specific
    configuration of a project.

    Valid attributes:

    - ``name`` name of the configuration
    - ``short_code`` Short code suffix for configuration name
    - ``platform`` Platform to build for
    - ``project_type`` Type of binary to generate
    - ``exclude_from_build_list`` List of files to exclude from this
        configuration
    - ``include_folders_list`` List of directories for headers
    - ``library_folders_list`` List of directories for libraries
    - ``libraries_list`` List of libraries to include
    - ``frameworks_list`` List of frameworks to include (macOS/iOS)
    - ``define_list`` List of defines for compilation
    - ``debug`` True if debugging defaults are enabled
    - ``optimization`` 0-4 level of optimization
    - ``link_time_code_generation`` Enable link time code genration

    See Also:
        Project, Solution
    """

    def __init__(self, **kargs):
        """
        Init defaults.

        Args:
            kargs: List of defaults.
        """

        ## Dictionary of attributes describing how to build this configuration.
        self.attributes = deepcopy(kargs)

        ## Project this Configuration is attached to.
        self.project = None

        # Set the default name
        name = self.attributes.get('name')
        if not is_string(name):
            raise TypeError(
                "string parameter 'name' is required")

        # Set the optional short code for file names
        self.attributes.setdefault('short_code', name)

        # Verify the platform parameter
        validate_type(self, 'platform', PlatformTypes)

        # Verify the project type
        validate_type(self, 'project_type', ProjectTypes)

        # Initialize the attributes that are lists
        for item in _DEFAULT_ATTRIBUTE_LISTS:
            self.attributes.setdefault(item, [])

    ########################################

    def get_attribute(self, name):
        """
        Return an attribute by key.
        @details
        If the attribute does not exist, it will check
        the parent project and then the parent solution for the key.

        Args:
            name: Name of the attribute key
        Return:
            None if the attribute is not in use, or a value.
        """

        value = self.attributes.get(name)
        if value is None:
            if self.project:
                return self.project.get_attribute(name)
        return value

    ########################################

    def get_attribute_list(self, name):
        """
        Return an chained attribute list.
        @details
        Obtain the list from the named attribute and append
        it with the same attribute in project and solution
        and return the entire list. This function does not
        modify the original lists.

        Args:
            name: Name of the attribute key
        Return:
            A list of all items found. The list can be empty.
        """

        value_list = list(self.attributes.get(name, []))

        # Is there a reverse link?
        if self.project:
            value_list.extend(self.project.attributes.get(name, []))

            # Is there a solution?
            if self.project.solution:
                value_list.extend(
                    self.project.solution.attributes.get(name, []))
        return value_list

    ########################################

    def parse_attributes(self, build_rules_list, working_directory):
        """
        Initialize the default attributes.

        Args:
            build_rules_list: List to append a valid build_rules file instance.
            working_directory: Full path name of the build_rules.py to load.
        """

        default_rules('configuration_settings',
                      working_directory=working_directory,
                      configuration=self)
        for rules in build_rules_list:
            default = rules(
                'configuration_settings',
                working_directory=working_directory,
                configuration=self)

            # Must test for zero, since None is a break.
            if default != 0:
                break

    ########################################

    def __repr__(self):
        """
        Convert the configuration record into a human readable description.

        Returns:
            Human readable string.
        """

        return 'Configuration: {}, Attributes: {}'.format(
            self.attributes['name'], str(self.attributes))

    ## Allow str() to work.
    __str__ = __repr__


########################################


class Project:
    """
    Object for processing a project file.

    This object contains all of the items needed to generate a project.

    @note On most IDEs, this is merged into one file, but Visual Studio
    generates a project file for each project.
    """

    # Too many instance attributes
    # pylint: disable=too-many-instance-attributes

    def __init__(self, **kargs):
        """
        Set defaults.

        Args:
            kargs: dict of arguments.
        """

        ## Dictionary of attributes describing how to build this configuration.
        self.attributes = deepcopy(kargs)

        ## No parent solution yet
        self.solution = None

        ## Generate the three default configurations
        self.configuration_list = []

        ## Initial array of Project records that need to be built first
        self.project_list = []

        ## Initial array of SourceFile in the solution
        self.codefiles = []

        ## Used by scan_directory
        self.file_list = None

        ## Used by scan_directory
        self.include_list = None

        ## Used by scan_directory
        self.exclude_list = None

        # Set a default project name
        self.attributes.setdefault('name', 'project')

        # Set a default working directory
        self.attributes.setdefault('working_directory', os.getcwd())

        # Verify the platform parameter
        validate_type(self, 'platform', PlatformTypes)

        # Verify the project type
        validate_type(self, 'project_type', ProjectTypes)

        # Initialize the attributes that are lists
        for item in _DEFAULT_ATTRIBUTE_LISTS:
            self.attributes.setdefault(item, [])

        self.attributes.setdefault('exclude_list', [])
        self.attributes.setdefault(
            'source_folders_list', ['.', 'source', 'src'])

    ########################################

    def add_configuration(self, configuration):
        """
        Add a configuration to the list of configurations found in this project.
        @details
        Given a new Configuration class instance, append it to the list of
        configurations that this project is managing.

        Args:
            self: The 'this' reference.
            configuration: Reference to an instance of a Configuration.
        Exception:
            TypeError if ``configuration`` is not a Configuration
        """

        if configuration:

            # Singular
            if isinstance(configuration, Configuration):

                # Set the configuration's parent
                configuration.project = self
                self.configuration_list.append(configuration)
            else:

                # Assume iterable
                for item in configuration:
                    # Sanity check
                    if not isinstance(item, Configuration):
                        raise TypeError(("parameter 'configuration' must "
                                         "be of type Configuration"))
                    item.project = self
                    self.configuration_list.append(item)

    ########################################

    def add_project(self, project):
        """
        Add a dependent project.

        Args:
            project: Project to depend on.
        Exception:
            TypeError if project is not a Project
        """

        # Sanity check
        if not isinstance(project, Project):
            raise TypeError("parameter 'project' must be of type Project")
        self.project_list.append(project)

    ########################################

    def get_attribute(self, name):
        """
        Return an attribute by key.
        @details
        If the attribute does not exist, it will check
        the solution for the key.

        Args:
            name: Name of the attribute key
        Return:
            None if the attribute is not in use, or a value.
        """

        value = self.attributes.get(name)
        if value is None:
            if self.solution:
                value = self.solution.attributes.get(name)
        return value

    ########################################

    def get_attribute_list(self, name):
        """
        Return an chained attribute list.
        @details
        Obtain the list from the named attribute and append
        it with the same attribute in the solution
        and return the entire list. This function does not
        modify the original lists.

        Args:
            name: Name of the attribute key
        Return:
            A list of all items found. The list can be empty.
        """

        value_list = list(self.attributes.get(name, []))

        # Is there a solution?
        if self.solution:
            value_list.extend(self.solution.attributes.get(name, []))
        return value_list

    ########################################

    def parse_attributes(self, build_rules_list, working_directory):
        """
        Initialize the default attributes.

        Args:
            build_rules_list: List to append a valid build_rules file instance.
            working_directory: Full path name of the build_rules.py to load.
        """

        default_rules('project_settings',
                      working_directory=working_directory,
                      project=self)
        for rules in build_rules_list:
            default = rules('project_settings',
                            working_directory=working_directory,
                            project=self)
            # Must test for zero, since None is a break.
            if default != 0:
                break

    ########################################

    def _scan_directory(self, working_directory, recurse, acceptable_list):
        """
        Given a base directory and a relative directory
        scan for all the files that are to be included in the project

        Args:
            working_directory: Directory to scan
            file_list: list to store SourceFile records
        """

        # Absolute or relative?
        if not os.path.isabs(working_directory):
            working_directory = os.path.abspath(
                os.path.join(self.get_attribute('working_directory'),
                             working_directory))

        # Is this a valid directory?
        if not os.path.isdir(working_directory):
            return

        # Scan the directory
        for base_name in os.listdir(working_directory):

            # Is this file in the exclusion list?
            for item in self.exclude_list:
                if item(base_name):
                    break
            else:

                # Is it a file? (Skip links and folders)
                file_name = os.path.join(working_directory, base_name)
                if os.path.isfile(file_name):

                    # Check against the extension list (Skip if not
                    # supported)
                    file_type = FileTypes.lookup(base_name)
                    if file_type is None:
                        continue

                    # Found a match, test if the type is in
                    # the acceptable list

                    if file_type in acceptable_list:
                        # Create a new entry (Using windows style slashes
                        # for consistency)
                        self.file_list.append(SourceFile(
                            os.path.relpath(
                                file_name,
                                self.get_attribute('working_directory')),
                            working_directory,
                            file_type))

                        # Add the directory the file was found for header search
                        self.include_list.add(
                            os.path.relpath(
                                working_directory, self.get_attribute(
                                    'working_directory')))

                # Process folders only if in recursion mode
                elif recurse and os.path.isdir(file_name):
                    self._scan_directory(
                        file_name, recurse, acceptable_list)

    ########################################

    def get_file_list(self, acceptable_list):
        """
        Obtain the list of source files.

        Set up the variables ``codefiles`` with the list of source files found
        and ``_source_include_list`` with a list of relative to the
        working directory folders where the source code was found.

        - ``exclude_list`` for wildcard matching for files to exclude
        - ``source_folders_list`` for list of folders to search for source code
        Args:
            acceptable_list: List of acceptable FileTypes
        """

        # Get the files to exclude in this
        self.exclude_list = translate_to_regex_match(
            self.get_attribute_list('exclude_list'))

        self.file_list = []
        self.include_list = set()

        # Pull in all the source folders and scan them
        for item in self.get_attribute_list('source_folders_list'):

            # Is it a recursive test?
            recurse = False
            if item.endswith('/*.*'):
                # Remove the trailing /*.*
                item = item[:-4]
                recurse = True

            # Scan the folder for files
            self._scan_directory(item, recurse, acceptable_list)

        # Since the slashes are all windows (No matter what
        # host this script is running on, the sort will yield consistent
        # results so it doesn't matter what platform generated the
        # file list, it's the same output.
        self.codefiles = sorted(
            self.file_list, key=attrgetter('relative_pathname'))
        self.attributes['_source_include_list'] = sorted(self.include_list)

        # Cleanup
        self.file_list = None
        self.include_list = None
        self.exclude_list = None

    ########################################

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return ('Project: {}, CodeFiles: {}, Attributes: {}, Configurations: '
                '{}').format(self.attributes['name'], str(self.codefiles),
                             str(self.attributes),
                             str(self.configuration_list))

    ## Allow str() to work.
    __str__ = __repr__


class Solution:
    """
    Object for processing a solution file.

    This object contains all of the items needed to create a solution.
    """

    def __init__(self, **kargs):
        """
        Init defaults.

        Args:
            kargs: dict of arguments.
        """

        ## Dictionary of attributes describing how to build this configuration.
        self.attributes = deepcopy(kargs)

        ## Type of ide
        self.ide = validate_type(self, 'ide', IDETypes)
        if self.ide is None:
            self.ide = IDETypes.default()
            self.attributes['ide'] = self.ide

        ## Initial array of Project records for projects
        self.project_list = []

        # Set a default project name
        self.attributes.setdefault('name', 'project')

        # Set a default working directory
        self.attributes.setdefault('working_directory', os.getcwd())

        # Set a default working directory
        self.attributes.setdefault('verbose', False)

        # Set a default working directory
        self.attributes.setdefault('perforce', True)

        # Set a default working directory
        self.attributes.setdefault('suffix_enable', True)

        # Initialize the attributes that are lists
        for item in _DEFAULT_ATTRIBUTE_LISTS:
            self.attributes.setdefault(item, [])

        self.attributes.setdefault('exclude_list', [])
        self.attributes.setdefault(
            'source_folders_list', ['.', 'source', 'src'])

    ########################################

    def add_project(self, project):
        """
        Add a project to the list of projects found in this solution.
        @details
        Given a new Project class instance, append it to the list of
        projects that this solution is managing.

        Args:
            self: The 'this' reference.
            project: Reference to an instance of a Project.
        """

        # Sanity check
        if not isinstance(project, Project):
            raise TypeError("parameter 'project' must be of type Project")

        project.solution = self
        self.project_list.append(project)

    ########################################

    def get_attribute(self, name):
        """
        Return an attribute by key.

        Args:
            name: Name of the attribute key
        """
        return self.attributes.get(name)

    ########################################

    def get_attribute_list(self, name):
        """
        Return an chained attribute list.
        @details
        Obtain the list from the named attribute.

        Args:
            name: Name of the attribute key
        Return:
            A list of all items found. The list can be empty.
        """

        return list(self.attributes.get(name, []))

    ########################################

    def generate(self, ide=None):
        """
        Generate a project file and write it out to disk.
        """

        # Work from a copy to ensure the original is not touched.
        solution = deepcopy(self)

        # Sort the configuration/platforms to ensure diffs are minimized
        for project in solution.project_list:
            project.configuration_list = sorted(
                project.configuration_list, key=lambda x: (
                    x.get_attribute('name'), x.get_attribute('platform')))

        # If ide was passed, check it, otherwise assume
        # solution.ide is valid
        if ide is not None:
            if not isinstance(ide, IDETypes):
                raise TypeError("parameter 'ide' must be of type IDETypes")
            solution.ide = ide

        # Create Visual Studio files
        if ide.is_visual_studio():
            from .visualstudio import generate as vs_generate
            return vs_generate(solution)

        # Create Codewarrior files
        if ide.is_codewarrior():
            from .codewarrior import generate as cw_generate
            return cw_generate(solution)
        return 10

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return 'Solution: {}, IDE: {}, Attributes: {}, ' \
            'Projects: [{}]'.format(
                self.attributes['name'],
                str(self.ide),
                str(self.attributes),
                '],['.join([str(i) for i in self.project_list]))

    ## Allow str() to work.
    __str__ = __repr__
