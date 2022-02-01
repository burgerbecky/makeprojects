#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module contains the core classes for makeproject.
"""

## \package makeprojects.core

from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import fnmatch
from operator import attrgetter
from copy import deepcopy
from burger import get_windows_host_type, convert_to_windows_slashes, \
    convert_to_linux_slashes, is_string, translate_to_regex_match, \
    string_to_bool, StringListProperty, BooleanProperty, NoneProperty

from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes
from .enums import platformtype_short_code
from .defaults import get_configuration_settings
from .build_rules import rules as default_rules

# pylint: disable=consider-using-f-string

########################################


def validate_enum_type(value, data_type):
    """
    Verify a value is a specific data type.

    Check if the value is either None or an instance of a
    specfic data type. If so, return immediately. If the value is a string,
    call the lookup() function of the data type for conversion.

    Args:
        value: Value to check.
        data_type: Type instance of the class type to match.

    Returns:
        Value converted to data_type or None.

    Exception:
        TypeError if lookup() failed.
    """

    if value is not None:
        # Perform the lookup
        new_value = data_type.lookup(value)
        if new_value is None:
            msg = '"{}" must be of type "{}".'.format(
                value, data_type.__name__)
            raise TypeError(msg)
        # Save the converted type
        value = new_value
    return value

########################################


def regex_dict(item):
    """ Convert *.cpp keys to regex keys

    Args:
        item: dict to convert
    Returns:
        dict with keys converted to regexes
    """

    output = {}
    for key in item:
        output[re.compile(fnmatch.translate(key)).match] = item[key]
    return output

########################################


def validate_boolean(value):
    """
    Verify a value is a boolean.

    Check if the value can be converted to a bool, if so,
    return the value as bool. None is converted to False.

    Args:
        value: Value to check.

    Returns:
        Value converted to data_type or None.

    Exception:
        ValueError if conversion failed.
    """

    if value is not None:
        # Convert to bool
        value = string_to_bool(value)
    return value

########################################


def validate_string(value):
    """
    Verify a value is a string.

    Check if the value is a string, if so,
    return the value as is or None.

    Args:
        value: Value to check.

    Returns:
        Value is string or None.

    Exception:
        ValueError if conversion failed.
    """

    if value is not None:
        # Convert to bool
        if not is_string(value):
            raise ValueError('"{}" must be a string.'.format(value))
    return value

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


class Attributes:
    """
    Base class for Solution parts to unify common code
    """

    # Too many instance attributes
    # pylint: disable=R0902

    ## List of defines for the compiler
    define_list = StringListProperty('_define_list')

    ## List of folders to add to compiler include list
    include_folders_list = StringListProperty('_include_folders_list')

    ## List of folders to add to linker include list
    library_folders_list = StringListProperty('_library_folders_list')

    ## List of libraries to link
    libraries_list = StringListProperty('_libraries_list')

    ## Darwin frameworks list
    frameworks_list = StringListProperty('_frameworks_list')

    ## List of file patterns to exclude from this configuration
    exclude_from_build_list = StringListProperty('_exclude_from_build_list')

    ## List of files to exclude from directory scanning
    exclude_list = StringListProperty('_exclude_list')

    ## List of CodeWarrior environment variables
    cw_environment_variables = StringListProperty('_cw_environment_variables')

    def __init__(self, **kargs):
        """
        Perform initialization that's common to all parts.

        Args:
            kargs: List of defaults.
        """

        ## Reference to parent object for chained attribute lookups
        self.parent = None

        ## List of defines for the compiler
        self.define_list = []

        ## List of folders to add to compiler include list
        self.include_folders_list = []

        ## List of folders to add to linker include list
        self.library_folders_list = []

        ## List of libraries to link
        self.libraries_list = []

        ## List of file patterns to exclude from this configuration
        self.exclude_from_build_list = []

        ## List of files to exclude from directory scanning
        self.exclude_list = []

        ## Generated file folder list
        self._source_include_list = []

        ## List of CodeWarrior environment variables
        self.cw_environment_variables = []

        ## Custom build rules
        self.custom_rules = {}

        # Set all the variables
        for key in kargs:
            setattr(self, key, kargs[key])

    ########################################

    def get_chained_value(self, name):
        """
        Follow the chain to find a value.

        Args:
            self: The 'this' reference.
            name: Name of the attribute
        Return:
            None or the value.
        """
        value = getattr(self, name, None)
        if value is None and self.parent is not None:
            value = self.parent.get_chained_value(name)
        return value

    ########################################

    def get_chained_list(self, name):
        """
        Return an chained attribute list.
        @details
        Obtain the list from the named attribute and append
        it with the same attribute in parent
        and return the entire list. This function does not
        modify the original lists.

        Args:
            name: Name of the attribute key
        Return:
            A list of all items found. The list can be empty.
        """

        value_list = list(getattr(self, name, []))

        # Is there a reverse link?
        if self.parent is not None:
            value_list.extend(getattr(self.parent, name, []))
        return value_list

    ########################################

    def get_unique_chained_list(self, name):
        """
        Return an chained attribute list with duplicates removed.
        @details
        Obtain the list from the named attribute and append
        it with the same attribute in parent
        and return the entire list. This function does not
        modify the original lists. All duplicates are removed.

        Args:
            name: Name of the attribute key
        Return:
            A list of all items found. The list can be empty.
        See Also:
            get_chained_list
        """

        return list(dict.fromkeys(self.get_chained_list(name)))

    ########################################

    # Attribute defined outside __init__
    # pylint: disable=W0201

    @property
    def platform(self):
        """ Get the enums.PlatformTypes """
        return self.get_chained_value('_platform')

    @platform.setter
    def platform(self, value):
        """
        Set the enums.PlatformTypes with validation
        Args:
            self: The 'this' reference.
            value: None or enums.PlatformTypes
        """

        ## Private enums.PlatformTypes value
        self._platform = validate_enum_type(value, PlatformTypes)

    ########################################

    @property
    def project_type(self):
        """ Get the enums.ProjectTypes """
        return self.get_chained_value('_project_type')

    @project_type.setter
    def project_type(self, value):
        """
        Set the enums.ProjectTypes with validation
        Args:
            self: The 'this' reference.
            value: None or enums.ProjectTypes
        """

        ## Private enums.ProjectTypes value
        self._project_type = validate_enum_type(value, ProjectTypes)

    ########################################

    @property
    def debug(self):
        """ Get debug boolean """
        return self.get_chained_value('_debug')

    @debug.setter
    def debug(self, value):
        """
        Set the boolean with validation
        Args:
            self: The 'this' reference.
            value: None, True or False
        """

        ## Private boolean for debug
        self._debug = validate_boolean(value)

    ########################################

    @property
    def link_time_code_generation(self):
        """ Get link time code generation boolean """
        return self.get_chained_value('_link_time_code_generation')

    @link_time_code_generation.setter
    def link_time_code_generation(self, value):
        """
        Set the boolean with validation
        Args:
            self: The 'this' reference.
            value: None, True or False
        """

        ## Private boolean for link_time_code_generation
        self._link_time_code_generation = validate_boolean(value)

    ########################################

    @property
    def optimization(self):
        """ Get optimization boolean """
        return self.get_chained_value('_optimization')

    @optimization.setter
    def optimization(self, value):
        """
        Set the boolean with validation
        Args:
            self: The 'this' reference.
            value: None, True or False
        """

        ## Private boolean for optimization
        self._optimization = validate_boolean(value)

    ########################################

    @property
    def analyze(self):
        """ Get code analysis boolean """
        return self.get_chained_value('_analyze')

    @analyze.setter
    def analyze(self, value):
        """
        Set the boolean with validation
        Args:
            self: The 'this' reference.
            value: None, True or False
        """

        ## Private boolean for analyze
        self._analyze = validate_boolean(value)

    ########################################

    @property
    def use_mfc(self):
        """ Get use of Microsoft Foundation class boolean """
        return self.get_chained_value('_use_mfc')

    @use_mfc.setter
    def use_mfc(self, value):
        """
        Set the boolean with validation
        Args:
            self: The 'this' reference.
            value: None, True or False
        """

        ## Private boolean for use_mfc
        self._use_mfc = validate_boolean(value)

    ########################################

    @property
    def use_atl(self):
        """ Get Microsoft Active Template Library boolean """
        return self.get_chained_value('_use_atl')

    @use_atl.setter
    def use_atl(self, value):
        """
        Set the boolean with validation
        Args:
            self: The 'this' reference.
            value: None, True or False
        """

        ## Private boolean for use_atl
        self._use_atl = validate_boolean(value)

    @property
    def clr_support(self):
        """ Get Common Language Runtime boolean """
        return self.get_chained_value('_clr_support')

    @clr_support.setter
    def clr_support(self, value):
        """
        Set the boolean with validation
        Args:
            self: The 'this' reference.
            value: None, True or False
        """

        ## Private boolean for clr_support
        self._clr_support = validate_boolean(value)

    ########################################

    @property
    def name(self):
        """ Get name string """
        return self.get_chained_value('_name')

    @name.setter
    def name(self, value):
        """
        Set the string with validation
        Args:
            self: The 'this' reference.
            value: None, string
        """

        ## Private string for name
        self._name = validate_string(value)

    @property
    def working_directory(self):
        """ Get working directory string """
        return self.get_chained_value('_working_directory')

    @working_directory.setter
    def working_directory(self, value):
        """
        Set the string with validation
        Args:
            self: The 'this' reference.
            value: None, string
        """

        ## Private string for working_directory
        self._working_directory = validate_string(value)

    @property
    def deploy_folder(self):
        """ Get deployment folder string """
        return self.get_chained_value('_deploy_folder')

    @deploy_folder.setter
    def deploy_folder(self, value):
        """
        Set the string with validation
        Args:
            self: The 'this' reference.
            value: None, string
        """

        ## Private string for deploy_folder
        self._deploy_folder = validate_string(value)

########################################


class SourceFile:
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


class Configuration(Attributes):
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

    ## Don't allow source folders in configuration
    source_folders_list = NoneProperty('_source_folders_list')

    ## Don't allow source files to be added in a configuration
    source_files_list = StringListProperty('_source_files_list')

    ## Don't allow Visual Studio props files
    vs_props = NoneProperty('_vs_props')

    ## Don't allow Visual Studio targets files
    vs_targets = NoneProperty('_vs_targets')

    ## Don't allow Visual Studio rules files
    vs_rules = NoneProperty('_vs_rules')

    def __init__(self, *args, **kargs):
        """
        Init defaults.

        Args:
            args: name and setting_name for get_configuration_settings(_
            kargs: List of defaults.
        """

        # Were there nameless parameters?
        if args:
            # Too many parameters?
            if len(args) >= 3:
                raise ValueError(
                    'Only one or two nameless parameters are allowed')

            # Get the default settings
            setting_name = None
            if len(args) == 2:
                setting_name = args[1]
            new_args = get_configuration_settings(args[0], setting_name)
            if new_args is None:
                new_args = {'name': args[0]}

            # Were there defaults found?
            for item in new_args:
                # Only add, never override
                if item not in kargs:
                    kargs[item] = new_args[item]

        # Check the default name
        if not is_string(kargs.get('name', None)):
            raise TypeError(
                "string parameter 'name' is required")

        # Init the base class
        Attributes.__init__(self, **kargs)

        ## Project this Configuration is attached to.
        self.project = None

    ########################################

    # Attribute defined outside __init__
    # pylint: disable=W0201

    @property
    def ide(self):
        """
        Return the preferred IDE
        """
        if self.parent is not None:
            return self.parent.ide
        return None

    @property
    def short_code(self):
        """
        Return the short code
        """

        short_code = getattr(self, '_short_code', None)
        if short_code is None:
            return self.name
        return short_code

    @short_code.setter
    def short_code(self, value):
        """
        Set the filename suffix
        Args:
            self: The 'this' reference.
            value: New short code
        """
        self._short_code = validate_string(value)

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

    def get_suffix(self, force_short=False):
        """
        Return the proposed suffix.

        Each configuration can generate a seperate binary and
        if they are stored in the same folder, a suffix
        is appened to make the filename unique.

        Args:
            force_short: True to force the platform code to 3 characters
        Returns:
            A suffix of the IDE, Platform and Configuration short codes.
        """

        # It's possible to not have a platform for
        # projects that consist of platform neutral data
        platform = self.platform
        if platform is not None:
            platform_text = platform.get_short_code()
            if force_short:
                platform_text = platform_text[:3]
        else:
            platform_text = ''

        return '{}{}{}'.format(
            self.ide.get_short_code(),
            platform_text,
            self.short_code)

    ########################################

    def __repr__(self):
        """
        Convert the configuration record into a human readable description.

        Returns:
            Human readable string.
        """

        result_list = []
        for item in self.__dict__:
            if item == 'parent':
                continue
            if item == 'project':
                result_list.append(
                    'Project: "{}"'.format(
                        self.__dict__[item].name))
                continue
            item_name = item[1:] if item.startswith('_') else item
            result_list.append(
                '{0}: {1!s}'.format(
                    item_name,
                    self.__dict__[item]))
        return 'Configuration: ' + ', '.join(result_list)

    ## Allow str() to work.
    __str__ = __repr__


########################################


class Project(Attributes):
    """
    Object for processing a project file.

    This object contains all of the items needed to generate a project.

    @note On most IDEs, this is merged into one file, but Visual Studio
    generates a project file for each project.
    """

    # Too many instance attributes
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=attribute-defined-outside-init

    ## List of directories to scan for source code
    source_folders_list = StringListProperty('_source_folders_list')

    ## List of generated source files to include in the project
    source_files_list = StringListProperty('_source_files_list')

    ## List of props files for Visual Studio
    vs_props = StringListProperty('_vs_props')

    ## List of targets file for Visual Studio
    vs_targets = StringListProperty('_vs_targets')

    ## List of rules file for Visual Studio 2005-2008
    vs_rules = StringListProperty('_vs_rules')

    def __init__(self, name=None, **kargs):
        """
        Set defaults.

        Args:
            name: Name of the project
            kargs: dict of arguments.
        """

        ## Project name
        self.name = name

        ## Working directory for the project
        self.working_directory = None

        ## List of folders to scan for source code
        self.source_folders_list = ['.', 'source', 'src']

        ## List of files to add to the project
        self.source_files_list = []

        ## List of props files for Visual Studio
        self.vs_props = []

        ## List of targets file for Visual Studio
        self.vs_targets = []

        ## List of rules file for Visual Studio 2005-2008
        self.vs_rules = []

        # Init the base class
        Attributes.__init__(self, **kargs)

        working_directory = os.getcwd()

        # Set a default project name
        if self.name is None:
            self.name = os.path.basename(working_directory)

        # Default directory
        if self.working_directory is None:
            self.working_directory = working_directory

        ## No parent solution yet
        self.solution = None

        ## Generate the default configurations
        self.configuration_list = []

        ## Initial array of Project records that need to be built first
        self.project_list = []

        ## Initial array of SourceFile in the solution
        self.codefiles = []

        ## Used by scan_directory
        self.file_list = None

        ## Used by scan_directory
        self.include_list = None

        ## Platform code for generation
        self.platform_code = ''

    ########################################

    @property
    def ide(self):
        """
        Return the preferred IDE
        """
        if self.parent is not None:
            return self.parent.ide
        return None

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

        if configuration is None or is_string(configuration):
            configuration = Configuration(configuration)

        # Singular
        if not isinstance(configuration, Configuration):
            raise TypeError(("parameter 'configuration' "
                             "must be of type Configuration"))
            # Set the configuration's parent

        if configuration.platform is None:
            configuration.platform = PlatformTypes.default()

        if configuration.platform.is_expandable():
            for platform in configuration.platform.get_expanded():
                config = deepcopy(configuration)
                config.platform = platform
                config.project = self
                config.parent = self
                self.configuration_list.append(config)
        else:
            configuration.project = self
            configuration.parent = self
            self.configuration_list.append(configuration)

    ########################################

    def add_project(self, project):
        """
        Add a dependent project.

        Args:
            project: Project to depend on.
        Exception:
            TypeError if project is not a Project
        """

        if project is None or is_string(project):
            project = Project(project)

        # Sanity check
        if not isinstance(project, Project):
            raise TypeError(
                "parameter 'project' must be of type Project or name")

        project.solution = self.solution
        project.parent = self.solution
        self.project_list.append(project)
        return project

    ########################################

    def get_project_list(self):
        """
        Return the project list for all projects.

        Iterate over every project and sub project and return
        a flattened list.

        Returns:
            list of every project in the solution.
        """

        # Make a copy of the current list
        project_list = list(self.project_list)

        # Scan the sub projects and add their projects to the
        # generated list.
        for project in self.project_list:
            project_list.extend(project.get_project_list())
        return project_list

    ########################################

    def set_platforms(self, platform):
        """
        Update all configurations to a new platform.

        If there are no configurations, Debug and Release will be
        created.

        Args:
            platform: Platform to change the configurations to.
        """

        if not self.configuration_list:
            for item in ('Debug', 'Release'):
                self.add_configuration(Configuration(item, platform=platform))
        else:

            # Create a set of configurations by name
            config_list = []
            name_list = []
            for configuration in self.configuration_list:
                if configuration.name in name_list:
                    continue
                name_list.append(configuration.name)
                config_list.append(configuration)

            # Expand platform groups
            self.configuration_list = []
            for item in platform.get_expanded():
                for configuration in config_list:
                    configuration.platform = item
                    self.add_configuration(deepcopy(configuration))

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
                os.path.join(self.working_directory,
                             working_directory))

        # Is this a valid directory?
        if not os.path.isdir(working_directory):
            return

        # Scan the directory
        for base_name in os.listdir(working_directory):

            # Is this file in the exclusion list?
            for item in self.exclude_list_regex:
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
                                self.working_directory),
                            working_directory,
                            file_type))

                        # Add the directory the file was found for header search
                        self.include_list.add(
                            os.path.relpath(
                                working_directory, self.working_directory))

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
        - ``source_files_list`` list of files to add
        Args:
            acceptable_list: List of acceptable FileTypes
        """

        # pylint: disable=attribute-defined-outside-init

        # Get the files to exclude in this
        self.exclude_list_regex = translate_to_regex_match(
            self.get_unique_chained_list('exclude_list'))

        self.file_list = []
        self.include_list = set()

        working_directory = self.working_directory

        for item in self.get_unique_chained_list('source_files_list'):
            if not os.path.isabs(item):
                abs_path = os.path.abspath(
                    os.path.join(working_directory, item))
            else:
                abs_path = item

            # Check against the extension list (Skip if not
            # supported)
            file_type = FileTypes.lookup(os.path.basename(abs_path))
            if file_type is None:
                continue

            # Found a match, test if the type is in
            # the acceptable list

            if file_type in acceptable_list:
                # Create a new entry (Using windows style slashes
                # for consistency)
                self.file_list.append(SourceFile(
                    os.path.relpath(
                        abs_path,
                        working_directory),
                    os.path.dirname(abs_path),
                    file_type))

                # Add the directory the file was found for header search
                self.include_list.add(
                    os.path.relpath(
                        os.path.dirname(abs_path), working_directory))

        # Pull in all the source folders and scan them
        for item in self.get_unique_chained_list('source_folders_list'):

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
        self._source_include_list = sorted(self.include_list)

        # Cleanup
        self.file_list = None
        self.include_list = None
        del self.exclude_list_regex

    ########################################

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        result_list = []
        for item in self.__dict__:
            if item == 'parent':
                continue
            if item == 'solution':
                result_list.append(
                    'Solution: "{}"'.format(
                        self.__dict__[item].name))
                continue
            item_name = item[1:] if item.startswith('_') else item
            result_list.append(
                '{0}: {1!s}'.format(
                    item_name,
                    self.__dict__[item]))
        return 'Project: ' + ', '.join(result_list)

    ## Allow str() to work.
    __str__ = __repr__

########################################


class Solution(Attributes):
    """
    Object for processing a solution file.

    This object contains all of the items needed to create a solution.
    """

    # Too many instance attributes
    # pylint: disable=R0902

    ## List of directories to scan for source code
    source_folders_list = StringListProperty('_source_folders_list')

    ## List of generated source files to include in the project
    source_files_list = StringListProperty('_source_files_list')

    ## Don't allow Visual Studio props files
    vs_props = NoneProperty('_vs_props')

    ## Don't allow Visual Studio targets files
    vs_targets = NoneProperty('_vs_targets')

    ## Don't allow Visual Studio rules files
    vs_rules = NoneProperty('_vs_rules')

    ## Use perforce
    perforce = BooleanProperty('_perforce')

    ## Verbosity
    verbose = BooleanProperty('_verbose')

    ## Enable the use of suffixes in creating filenames
    suffix_enable = BooleanProperty('_suffix_enable')

    def __init__(self, name=None, **kargs):
        """
        Init defaults.

        Args:
            name: Name of the Solution
            kargs: dict of arguments.
        """

        ## Private instance of enums.IDETypes
        self._ide = None

        ## Solution name
        self.name = name

        ## Working directory for the solution
        self.working_directory = None

        ## List of folders to scan for source code
        self.source_folders_list = []

        ## List of files to add to the projects
        self.source_files_list = []

        ## Enable perforce support
        self.perforce = True

        ## Enable output verbosity
        self.verbose = False

        ## Enable appending suffixes to project names
        self.suffix_enable = True

        # Init the base class
        Attributes.__init__(self, **kargs)

        working_directory = os.getcwd()

        # Use a default solution name
        if self.name is None:
            self.name = os.path.basename(working_directory)

        # Default directory
        if self.working_directory is None:
            self.working_directory = working_directory

        # Set a default project type
        if self.project_type is None:
            self.project_type = ProjectTypes.default()

        ## Initial array of Project records for projects
        self.project_list = []

        ## IDE code for generation
        self.ide_code = ''

        ## Platform code for generation
        self.platform_code = ''

    ########################################

    @property
    def ide(self):
        """
        Return the ide type
        """
        return self._ide

    @ide.setter
    def ide(self, value):
        """
        Set the IDE type with validation
        Args:
            self: The 'this' reference.
            value: None or new IDE type
        """
        self._ide = validate_enum_type(value, IDETypes)

    ########################################

    def add_project(self, project=None, project_type=None):
        """
        Add a project to the list of projects found in this solution.
        @details
        Given a new Project class instance, append it to the list of
        projects that this solution is managing.

        Args:
            self: The 'this' reference.
            project: Reference to an instance of a Project.
            project_type: Type of project to create.
        """

        if project is None or is_string(project):
            project = Project(project, project_type=project_type)

        # Sanity check
        if not isinstance(project, Project):
            raise TypeError(
                "parameter 'project' must be of type Project or name")

        project.solution = self
        project.parent = self
        self.project_list.append(project)
        return project

    ########################################

    def add_tool(self, project=None):
        """
        Add a project to build a command line tool.

        See Also:
            add_project
        """
        return self.add_project(project, ProjectTypes.tool)

    def add_app(self, project=None):
        """
        Add a project to build an application.

        See Also:
            add_project
        """
        return self.add_project(project, ProjectTypes.app)

    def add_library(self, project=None):
        """
        Add a project to build a static library.

        See Also:
            add_project
        """
        return self.add_project(project, ProjectTypes.library)

    def add_shared_library(self, project=None):
        """
        Add a project to build a dynamic library.

        See Also:
            add_project
        """
        return self.add_project(project, ProjectTypes.sharedlibrary)

    ########################################

    def get_project_list(self):
        """
        Return the project list for all sub projects.

        Iterate over every sub project and return
        a flattened list.

        Returns:
            list of every project in the project.
        """

        # Make a copy of the current list
        project_list = list(self.project_list)

        # Scan the sub projects and add their projects to the
        # generated list.
        for project in self.project_list:
            project_list.extend(project.get_project_list())
        return project_list

    ########################################

    def set_platforms(self, platform):
        """
        Update all configurations to a new platform.

        If there are no configurations, Debug and Release will be
        created.

        Args:
            platform: Platform to change the configurations to.
        """

        for project in self.get_project_list():
            project.set_platforms(platform)

    ########################################

    def generate(self, ide=None):
        """
        Generate a project file and write it out to disk.
        """

        # pylint: disable=import-outside-toplevel

        # Work from a copy to ensure the original is not touched.
        solution = deepcopy(self)

        # If an ide was passed, check it, otherwise assume
        # solution.ide is valid
        if ide is not None:
            # Note, this will throw if IDE is not an IDE value
            solution.ide = ide

            # Grab the value back if there was conversion
            ide = solution.ide

        # Set the default IDE to whatever the system uses
        if ide is None:
            ide = IDETypes.default()
            solution.ide = ide

        # Determine which generator to use based on the selected IDE

        import makeprojects.watcom
        import makeprojects.makefile
        import makeprojects.visual_studio
        import makeprojects.visual_studio_2010
        import makeprojects.codewarrior
        import makeprojects.xcode
        import makeprojects.codeblocks

        generator_list = (
            makeprojects.visual_studio,
            makeprojects.visual_studio_2010,
            makeprojects.watcom,
            makeprojects.makefile,
            makeprojects.codewarrior,
            makeprojects.xcode,
            makeprojects.codeblocks)
        for generator in generator_list:
            if ide in generator.SUPPORTED_IDES:
                break
        else:
            print('IDE {} is not supported.'.format(ide))
            return 10

        # Convert keys that need to be regexes from *.cpp to regex
        solution.custom_rules = regex_dict(solution.custom_rules)

        all_configurations_list = []

        # Process all the projects and configurations
        for project in solution.get_project_list():

            # Handle projects
            project.custom_rules = regex_dict(project.custom_rules)

            # Purge unsupported configurations
            configuration_list = []
            if not project.configuration_list:
                for item in ('Debug', 'Release'):
                    project.add_configuration(item)

            for configuration in project.configuration_list:
                if generator.test(ide, configuration.platform):
                    configuration_list.append(configuration)

            # Sort the configurations to ensure consistency
            configuration_list = sorted(
                configuration_list, key=lambda x: (
                    x.name, x.platform))
            project.configuration_list = configuration_list

            all_configurations_list.extend(configuration_list)
            project.platform_code = platformtype_short_code(configuration_list)

            # Handle regexes for configurations that will be used
            for configuration in configuration_list:
                configuration.custom_rules = regex_dict(
                    configuration.custom_rules)
                configuration.exclude_list_regex = translate_to_regex_match(
                    configuration.exclude_list)

        # Get the platform code
        solution.platform_code = platformtype_short_code(
            all_configurations_list)

        # Set the IDE code
        solution.ide_code = ide.get_short_code()

        # Create project files
        return generator.generate(solution)

    def __repr__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """
        result_list = []
        for item in self.__dict__:
            if item == 'parent':
                continue
            item_name = item[1:] if item.startswith('_') else item
            result_list.append(
                '{0}: {1!s}'.format(
                    item_name,
                    self.__dict__[item]))
        return 'Solution: ' + ', '.join(result_list)

    ## Allow str() to work.
    __str__ = __repr__
