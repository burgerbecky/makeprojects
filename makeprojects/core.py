#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module contains the core classes for makeproject.

@package makeprojects.core
"""

# pylint: disable=consider-using-f-string
# pylint: disable=useless-object-inheritance
# pylint: disable=super-with-arguments
# pylint: disable=too-many-lines

from __future__ import absolute_import, print_function, unicode_literals

import os
from operator import attrgetter
from copy import deepcopy
from burger import get_windows_host_type, convert_to_windows_slashes, \
    convert_to_linux_slashes, is_string, translate_to_regex_match, \
    StringListProperty, BooleanProperty, NoneProperty, StringProperty

from .enums import FileTypes, ProjectTypes, IDETypes, PlatformTypes, \
    platformtype_short_code
from .defaults import settings_from_name, configuration_presets, \
    project_presets
from .util import validate_enum_type, regex_dict, validate_boolean, \
    validate_string

########################################


class Attributes(object):
    """
    Base class for Solution parts to unify common code

    Attributes:
        parent: Reference to parent object for chained attribute lookups
        define_list: List of defines for the compiler
        include_folders_list: List of folders to add to compiler include list
        library_folders_list: List of folders to add to linker include list
        libraries_list: List of libraries to link
        library_rules_list: List of build_rules.py with libraries
        frameworks_list: Darwin frameworks list
        env_variable_list: List of required environment variables
        exclude_from_build_list: List of patterns to exclude from this config
        exclude_list: List of files to exclude from directory scanning
        cw_environment_variables: List of CodeWarrior environment variables
        custom_rules: Custom build rules
        platform: @ref makeprojects.enums.PlatformTypes enum for target platform
        project_type: @ref makeprojects.enums.ProjectTypes enum for target output
        debug: Boolean for debug information generation
        link_time_code_generation: Boolean for LTCG
        optimization: Boolean for optimization enable
        exceptions: Boolean for enabling C++ exceptions
        analyze: Boolean for code analysis
        use_mfc: String for Microsoft Foundation Classes usage
        use_atl: String for Active Template Library usage
        clr_support: C# CLR support usage
        name: Name of the project or configuration
        working_directory: Base directory for relative paths
        deploy_folder: Directory to deploy binaries
        fastcall: Boolean, True if fastcall is requested
        _source_include_list: Generated file folder list
        _platform: platform value
        _project_type: True @ref makeprojects.core.Attributes.project_type
        _debug: True @ref makeprojects.core.Attributes.debug
        _link_time_code_generation: True @ref makeprojects.core.Attributes.link_time_code_generation
        _optimization: True @ref makeprojects.core.Attributes.optimization
        _exceptions: False @ref makeprojects.code.Attributes.exceptions
        _analyze: True @ref makeprojects.core.Attributes.analyze
        _use_mfc: @ref makeprojects.core.Attributes.use_mfc
        _use_atl: @ref makeprojects.core.Attributes.use_atl
        _clr_support: @ref makeprojects.core.Attributes.clr_support
        _name: True @ref makeprojects.core.Attributes.name
        _working_directory: True @ref makeprojects.core.Attributes.working_directory
        _deploy_folder: True @ref makeprojects.core.Attributes.deploy_folder
        _fastcall: None @ref makeprojects.core.Attributes.fastcall
    """

    # pylint: disable=too-many-instance-attributes

    define_list = StringListProperty("_define_list")
    include_folders_list = StringListProperty("_include_folders_list")
    library_folders_list = StringListProperty("_library_folders_list")
    libraries_list = StringListProperty("_libraries_list")
    library_rules_list = StringListProperty("_library_rules_list")
    frameworks_list = StringListProperty("_frameworks_list")
    env_variable_list = StringListProperty("_env_variable_list")
    exclude_from_build_list = StringListProperty("_exclude_from_build_list")
    exclude_list = StringListProperty("_exclude_list")
    cw_environment_variables = StringListProperty("_cw_environment_variables")

    def __init__(self):
        """
        Perform initialization off all attributes.
        """

        self.parent = None
        self.define_list = []
        self.include_folders_list = []
        self.library_folders_list = []
        self.libraries_list = []
        self.library_rules_list = []
        self.frameworks_list = []
        self.env_variable_list = []
        self.exclude_from_build_list = []
        self.exclude_list = []
        self.cw_environment_variables = []
        self.custom_rules = {}

        # These are internal values
        self._source_include_list = []
        self._platform = None
        self._project_type = None
        self._debug = None
        self._link_time_code_generation = None
        self._optimization = None
        self._exceptions = None
        self._analyze = None
        self._use_mfc = None
        self._use_atl = None
        self._clr_support = None
        self._name = None
        self._working_directory = None
        self._deploy_folder = None
        self._fastcall = None

    ########################################

    def get_chained_value(self, name):
        """
        Follow the chain to find a value.

        Args:
            self: The "this" reference.
            name: Name of the attribute
        Returns:
            None or the value.
        """

        # Get the value
        value = getattr(self, name, None)

        # If not found, follow the chain, if any
        if value is None and self.parent is not None:
            value = self.parent.get_chained_value(name)
        return value

    ########################################

    def get_chained_list(self, name):
        """
        Return an chained attribute list.
        @details
        Obtain the list from the named attribute and append it with the same
        attribute in parent and return the entire list. This function does not
        modify the original lists.

        Args:
            name: Name of the attribute key
        Returns:
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
        Obtain the list from the named attribute and append it with the same
        attribute in parent and return the entire list. This function does not
        modify the original lists. All duplicates are removed.

        Args:
            name: Name of the attribute key
        Returns:
            A list of all items found. The list can be empty.
        See Also:
            get_chained_list
        """

        return list(dict.fromkeys(self.get_chained_list(name)))

    ########################################

    def _getplatform(self):
        """
        Get the enums.PlatformTypes
        """

        return self.get_chained_value("_platform")

    def _setplatform(self, value):
        """
        Set the enums.PlatformTypes with validation
        Args:
            self: The "this" reference.
            value: None or enums.PlatformTypes
        """

        self._platform = validate_enum_type(value, PlatformTypes)

    platform = property(_getplatform, _setplatform)

    ########################################

    def _getproject_type(self):
        """
        Get the enums.ProjectTypes
        """

        return self.get_chained_value("_project_type")

    def _setproject_type(self, value):
        """
        Set the enums.ProjectTypes with validation
        Args:
            self: The "this" reference.
            value: None or enums.ProjectTypes
        """

        self._project_type = validate_enum_type(value, ProjectTypes)

    project_type = property(_getproject_type, _setproject_type)

    ########################################

    def _getdebug(self):
        """
        Get debug boolean
        """

        return self.get_chained_value("_debug")

    def _setdebug(self, value):
        """
        Set the boolean with validation
        Args:
            self: The "this" reference.
            value: None, True or False
        """

        self._debug = validate_boolean(value)

    debug = property(_getdebug, _setdebug)

    ########################################

    def _getlink_time_code_generation(self):
        """
        Get link time code generation boolean
        """

        return self.get_chained_value("_link_time_code_generation")

    def _setlink_time_code_generation(self, value):
        """
        Set the boolean with validation
        Args:
            self: The "this" reference.
            value: None, True or False
        """

        self._link_time_code_generation = validate_boolean(value)

    link_time_code_generation = property(
        _getlink_time_code_generation,
        _setlink_time_code_generation)

    ########################################

    def _getoptimization(self):
        """
        Get optimization boolean
        """

        return self.get_chained_value("_optimization")

    def _setoptimization(self, value):
        """
        Set the boolean with validation
        Args:
            self: The "this" reference.
            value: None, True or False
        """

        self._optimization = validate_boolean(value)

    optimization = property(_getoptimization, _setoptimization)

    ########################################

    def _getexceptions(self):
        """
        Get exceptions boolean
        """

        return self.get_chained_value("_exceptions")

    def _setexceptions(self, value):
        """
        Set the boolean with validation
        Args:
            self: The "this" reference.
            value: None, True or False
        """

        self._exceptions = validate_boolean(value)

    exceptions = property(_getexceptions, _setexceptions)

    ########################################

    def _getanalyze(self):
        """
        Get code analysis boolean
        """

        return self.get_chained_value("_analyze")

    def _setanalyze(self, value):
        """
        Set the boolean with validation
        Args:
            self: The "this" reference.
            value: None, True or False
        """

        self._analyze = validate_boolean(value)

    analyze = property(_getanalyze, _setanalyze)

    ########################################

    def _getuse_mfc(self):
        """
        Get use of Microsoft Foundation class string
        """

        return self.get_chained_value("_use_mfc")

    def _setuse_mfc(self, value):
        """
        Set the string with validation
        Args:
            self: The "this" reference.
            value: None, "DLL", "Static"
        """

        self._use_mfc = validate_string(value)

    use_mfc = property(_getuse_mfc, _setuse_mfc)

    ########################################

    def _getuse_atl(self):
        """
        Get Microsoft Active Template Library string
        """

        return self.get_chained_value("_use_atl")

    def _setuse_atl(self, value):
        """
        Set the string with validation
        Args:
            self: The "this" reference.
            value: None, "DLL", "Static"
        """

        self._use_atl = validate_string(value)

    use_atl = property(_getuse_atl, _setuse_atl)

    ########################################

    def _getclr_support(self):
        """
        Get Common Language Runtime boolean
        """

        return self.get_chained_value("_clr_support")

    def _setclr_support(self, value):
        """
        Set the string with validation
        Args:
            self: The "this" reference.
            value: None, True or False
        """

        self._clr_support = validate_string(value)

    clr_support = property(_getclr_support, _setclr_support)

    ########################################

    def _getname(self):
        """
        Get name string
        """

        return self.get_chained_value("_name")

    def _setname(self, value):
        """
        Set the string with validation
        Args:
            self: The "this" reference.
            value: None, string
        """

        self._name = validate_string(value)

    name = property(_getname, _setname)

    ########################################

    def _getworking_directory(self):
        """
        Get working directory string
        """

        return self.get_chained_value("_working_directory")

    def _setworking_directory(self, value):
        """
        Set the string with validation
        Args:
            self: The "this" reference.
            value: None, string
        """

        self._working_directory = validate_string(value)

    working_directory = property(_getworking_directory, _setworking_directory)

    ########################################

    def _getdeploy_folder(self):
        """
        Get deployment folder string
        """

        return self.get_chained_value("_deploy_folder")

    def _setdeploy_folder(self, value):
        """
        Set the string with validation
        Args:
            self: The "this" reference.
            value: None, string
        """

        self._deploy_folder = validate_string(value)

    deploy_folder = property(_getdeploy_folder, _setdeploy_folder)

    ########################################

    def _getfastcall(self):
        """
        Get Common Language Runtime boolean
        """

        return self.get_chained_value("_fastcall")

    def _setfastcall(self, value):
        """
        Set the boolean with validation
        Args:
            self: The "this" reference.
            value: None, True or False
        """

        self._fastcall = validate_boolean(value)

    fastcall = property(_getfastcall, _setfastcall)

########################################


class SourceFile(object):
    """
    Object for each input file to insert to a solution.

    For every file that could be included into a project file
    one of these objects is created and attached to a Project object
    for processing.

    @note
    For hash consistency, @ref makeprojects.core.SourceFile.relative_pathname has all directory
    slashes in Windows format "\" instead of Linux/BSD format on all platforms.

    Attributes:
        relative_pathname: File base name with extension
        working_directory: Directory the file is relative to
        type: File type enumeration, @ref makeprojects.enums.FileTypes
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
            raise TypeError("parameter \"filetype\" must be of type FileTypes")

        self.relative_pathname = convert_to_windows_slashes(relative_pathname)
        self.working_directory = working_directory
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
        slash = "\\"
        index = self.relative_pathname.rfind(slash)
        if index == -1:
            slash = "/"
            index = self.relative_pathname.rfind(slash)
            if index == -1:
                # It's at the root
                return ""

        # Remove the basename
        group_name = self.relative_pathname[:index]

        # If there are ..\\ at the beginning, remove them

        while group_name.startswith(".." + slash):
            group_name = group_name[3:]

        # If there is a .\\, remove the single prefix
        while group_name.startswith("." + slash):
            group_name = group_name[2:]

        return group_name

    ########################################

    def get_abspath(self):
        """
        Return the full pathname of the file entry.

        Directory slashes will be set to the type that matches the host
        platform.

        Returns:
            Absolute pathname for the file.
        """

        if get_windows_host_type():
            file_name = self.relative_pathname
        else:
            file_name = convert_to_linux_slashes(self.relative_pathname)
        return os.path.abspath(os.path.join(self.working_directory, file_name))

    ########################################

    def __repr__(self):
        """
        Convert the file record into a human readable file description.

        Returns:
            Human readable string.
        """

        return "FileType: {} Pathname: \"{}\"".format(str(self.type),
                                                    self.get_abspath())

    def __str__(self):
        """
        Convert the file record into a human readable file description.

        Returns:
            Human readable string.
        """

        return self.__repr__()


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
    - ``library_rules_list`` List of build_rules.py with libraries
    - ``frameworks_list`` List of frameworks to include (macOS/iOS)
    - ``env_variable_list`` List of required environment variables
    - ``define_list`` List of defines for compilation
    - ``debug`` True if debugging defaults are enabled
    - ``optimization`` 0-4 level of optimization
    - ``exceptions`` True if C++ exceptions are enabled
    - ``link_time_code_generation`` Enable link time code genration

    If any of these attributes are read, they will always return None.
    To modify them, use the parent @ref makeprojects.core.Project
    - ``source_folders_list`` See Project.source_folders_list
    - ``vs_props`` See Project.vs_props
    - ``vs_targets`` See Project.vs_targets
    - ``vs_rules`` See Project.vs_rules
    - ``vs_platform_version`` See Project.vs_platform_version

    Attributes:
        name: Name of the configuration
        platform: Platform to build
        source_folders_list: Don't allow source folders
        vs_props: Don't allow Visual Studio props files
        vs_targets: Don't allow Visual Studio targets files
        vs_rules: Don't allow Visual Studio rules files
        vs_platform_version: Visual Studio platform SDK version
        project: Project this Configuration is attached to.
        ide: Get the @ref makeprojects.enums.IDETypes of the parent (Read only)
        short_code: Short config string for file name suffix
        _short_code: True @ref makeprojects.core.Configuration.short_code

    See Also:
        Project, Solution
    """

    # Disable these attributes that are present in the parent Project
    source_folders_list = NoneProperty("_source_folders_list")
    vs_props = NoneProperty("_vs_props")
    vs_targets = NoneProperty("_vs_targets")
    vs_rules = NoneProperty("_vs_rules")
    vs_platform_version = NoneProperty("_vs_platform_version")

    def __init__(self, name, platform):
        """
        Init defaults.

        Args:
            name: Name of the configuration
            platform: Platform for the configuration
        """

        # Init the base class
        super(Configuration, self).__init__()

        self._short_code = None

        self.name = name
        self.platform = platform
        self.project = None

        settings_from_name(configuration=self)

    ########################################

    def _getide(self):
        """
        Return the preferred IDE
        """
        if self.parent is not None:
            return self.parent.ide
        return None

    ide = property(_getide)

    ########################################

    def _getshort_code(self):
        """
        Return the short code
        """

        short_code = getattr(self, "_short_code", None)
        if short_code is None:
            return self.name
        return short_code

    def _setshort_code(self, value):
        """
        Set the filename suffix
        Args:
            self: The "this" reference.
            value: New short code
        """
        self._short_code = validate_string(value)

    short_code = property(_getshort_code, _setshort_code)

    ########################################

    def parse_attributes(self, build_rules_list):
        """
        Initialize the default attributes.

        Args:
            build_rules_list: List to append a valid build_rules file instance.
        """

        # Set up the default entries
        configuration_presets(configuration=self)

        for build_rules in build_rules_list:
            settings = getattr(build_rules, "configuration_settings", None)
            if callable(settings):
                result = settings(configuration=self)
                # Must test for zero, since None is continue.
                if result is not None:
                    break

        return result

    ########################################

    def get_suffix(self, force_short=False):
        """
        Return the proposed suffix.
        @details
        Each configuration can generate a seperate binary and
        if they are stored in the same folder, a suffix
        is appended to make the filename unique.

        Args:
            force_short: True to force the platform code to 3 characters
        Returns:
            A suffix of the IDE, Platform and Configuration short codes.
        """

        # It's possible to have a platform for
        # projects that consist of platform neutral data
        platform = self.platform
        if platform is not None:
            platform_text = platform.get_short_code()
            if force_short:
                platform_text = platform_text[:3]
        else:
            # Platform neutral
            platform_text = ""

        return "{}{}{}".format(
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
        for item in self.__dict__.items():
            if item[0] == "parent":
                continue
            if item[0] == "project":
                result_list.append(
                    "Project: \"{}\"".format(
                        item[1].name))
                continue
            item_name = item[0][1:] if item[0].startswith("_") else item[0]
            result_list.append(
                "{0}: {1!s}".format(
                    item_name,
                    item[1]))
        return "Configuration: " + ", ".join(result_list)

    ########################################

    def __str__(self):
        """
        Convert the configuration record into a human readable description.

        Returns:
            Human readable string.
        """
        return self.__repr__()


########################################


class Project(Attributes):
    """
    Object for processing a project file.

    This object contains all of the items needed to generate a project.

    @note On most IDEs, this is merged into one file, but Visual Studio
    generates a project file for each project.

    Attributes:
        ide: IDETypes for this project
        source_folders_list: List of directories to scan for source code
        source_files_list: Generated source file list to include in the project
        vs_props: List of props files for Visual Studio
        vs_targets: List of targets file for Visual Studio
        vs_rules: List of rules file for Visual Studio 2005-2008
        vs_platform_version: Visual Studio platform SDK version
        name: Project name
        working_directory: Working directory for the project
        solution: No parent solution yet
        configuration_list: Generate the default configurations
        project_list: Project records that need to be built first
        codefiles: Initial array of SourceFile in the solution
        file_list: Used by scan_directory
        include_list: Used by scan_directory
        platform_code: Platform code for generation
        exclude_list_regex: Regex iterable of files to exclude
        _source_include_list: Generated file folder list
    """

    # pylint: disable=too-many-instance-attributes

    source_folders_list = StringListProperty("_source_folders_list")
    source_files_list = StringListProperty("_source_files_list")
    vs_props = StringListProperty("_vs_props")
    vs_targets = StringListProperty("_vs_targets")
    vs_rules = StringListProperty("_vs_rules")
    vs_platform_version = StringProperty("_vs_platform_version")

    def __init__(self, name=None, **kargs):
        """
        Set defaults.

        Args:
            name: Name of the project
            kargs: dict of arguments.
        """

        # Init the base class
        super(Project, self).__init__()

        self.source_folders_list = [".", "source", "src"]
        self.source_files_list = []
        self.vs_props = []
        self.vs_targets = []
        self.vs_rules = []
        self.vs_platform_version = None

        working_directory = os.getcwd()

        # Set a default project name
        if name is None:
            self.name = os.path.basename(working_directory)
        else:
            self.name = name

        # Default directory
        self.working_directory = working_directory

        # Init the rest
        self.solution = None
        self.configuration_list = []
        self.project_list = []
        self.codefiles = []
        self.file_list = None
        self.include_list = None
        self.platform_code = ""

        # Set all the variables
        for key in kargs.items():
            setattr(self, key[0], key[1])

    ########################################

    def _getide(self):
        """
        Return the preferred IDE
        """
        if self.parent is not None:
            return self.parent.ide
        return None

    ide = property(_getide)

    ########################################

    def add_configuration(self, configuration):
        """
        Add a configuration to the list of configurations found in this project.
        @details
        Given a new Configuration class instance, append it to the list of
        configurations that this project is managing.

        Args:
            self: The "this" reference.
            configuration: Reference to an instance of a Configuration.
        Raises:
            TypeError
        """

        if configuration is None or is_string(configuration):
            configuration = Configuration(
                configuration, PlatformTypes.default())

        # Singular
        if not isinstance(configuration, Configuration):
            raise TypeError(("parameter \"configuration\" "
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
        Raises:
            TypeError
        """

        if project is None or is_string(project):
            project = Project(project)

        # Sanity check
        if not isinstance(project, Project):
            raise TypeError(
                "parameter \"project\" must be of type Project or name")

        project.solution = self.solution
        project.parent = self.solution
        self.project_list.append(project)
        return project

    ########################################

    def get_project_list(self):
        """
        Return the project list for all projects.
        @details
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
        @details
        If there are no configurations, Debug and Release will be
        created.

        Args:
            platform: Platform to change the configurations to.
        """

        if not self.configuration_list:
            for item in ("Debug", "Release"):
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

    def parse_attributes(self, build_rules_list):
        """
        Initialize the default attributes.

        Args:
            build_rules_list: List to append a valid build_rules file instance.
        """

        # Set up the default entries
        project_presets(project=self)

        for build_rules in build_rules_list:
            settings = getattr(build_rules, "project_settings", None)
            if callable(settings):
                result = settings(project=self)
                # Must test for zero, since None is continue.
                if result is not None:
                    break
        return result

    ########################################

    def _scan_directory(self, working_directory, recurse, acceptable_list):
        """
        Given a base directory and a relative directory
        scan for all the files that are to be included in the project

        Args:
            working_directory: Directory to scan
            recurse: Enable recursion
            acceptable_list: list to store SourceFile records
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
        @details
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
            self.get_unique_chained_list("exclude_list"))

        self.file_list = []
        self.include_list = set()

        working_directory = self.working_directory

        for item in self.get_unique_chained_list("source_files_list"):
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
        for item in self.get_unique_chained_list("source_folders_list"):

            # Is it a recursive test?
            recurse = False
            if item.endswith("/*.*"):
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
            self.file_list, key=attrgetter("relative_pathname"))
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
        for item in self.__dict__.items():
            if item[0] == "parent":
                continue
            if item[0] == "solution":
                if item[1] is None:
                    continue
                result_list.append(
                    "Solution: \"{}\"".format(
                        item[1].name))
                continue
            item_name = item[0][1:] if item[0].startswith("_") else item[0]
            result_list.append(
                "{0}: {1!s}".format(
                    item_name,
                    item[1]))
        return "Project: " + ", ".join(result_list)

    def __str__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return self.__repr__()


########################################


class Solution(Attributes):
    """
    Object for processing a solution file.

    This object contains all of the items needed to create a solution.

    Attributes:
        source_folders_list: List of directories to scan for source code
        source_files_list: List of source files to include in the project
        vs_props: Don't allow Visual Studio props files
        vs_targets: Don't allow Visual Studio targets files
        vs_rules: Don't allow Visual Studio rules files
        vs_platform_version: Visual Studio platform SDK version
        perforce: Boolean for using perforce
        verbose: Boolean for verbose output
        suffix_enable: Boolean for enabling unique suffixes
        name: Solution name
        working_directory: Working directory for the solution
        ide: @ref makeprojects.enums.IDETypes of the IDE being generated for
        ide_code: IDE code for generation
        platform_code: Platform code for generation
        project_list: List of dependent projects
        project_type: @ref makeprojects.enums.ProjectTypes enum for target output
        post_process: Python function to handle post processing
        _ide: Private instance of @ref makeprojects.enums.IDETypes
    """

    # pylint: disable=too-many-instance-attributes

    source_folders_list = StringListProperty("_source_folders_list")
    source_files_list = StringListProperty("_source_files_list")
    vs_props = NoneProperty("_vs_props")
    vs_targets = NoneProperty("_vs_targets")
    vs_rules = NoneProperty("_vs_rules")
    vs_platform_version = NoneProperty("_vs_platform_version")
    perforce = BooleanProperty("_perforce")
    verbose = BooleanProperty("_verbose")
    suffix_enable = BooleanProperty("_suffix_enable")

    def __init__(self, name=None, **kargs):
        """
        Init defaults.

        Args:
            name: Name of the Solution
            kargs: dict of arguments.
        """

        # Init the base class
        super(Solution, self).__init__()

        self._ide = None
        self.source_folders_list = []
        self.source_files_list = []
        self.perforce = True
        self.verbose = False
        self.suffix_enable = True
        self.post_process = lambda a: a

        working_directory = os.getcwd()

        # Use a default solution name
        if name is None:
            self.name = os.path.basename(working_directory)
        else:
            self.name = name

        # Default directory
        self.working_directory = working_directory

        # Set a default project type
        if self.project_type is None:
            self.project_type = ProjectTypes.default()

        self.project_list = []
        self.ide_code = ""
        self.platform_code = ""

        # Set all the variables
        for key in kargs.items():
            setattr(self, key[0], key[1])

    ########################################

    def _getide(self):
        """
        Return the ide type
        """
        return self._ide

    def _setide(self, value):
        """
        Set the IDE type with validation
        Args:
            self: The "this" reference.
            value: None or new IDE type
        """
        self._ide = validate_enum_type(value, IDETypes)

    ide = property(_getide, _setide)

    ########################################

    def add_project(self, project=None, project_type=None):
        """
        Add a project to the list of projects found in this solution.
        @details
        Given a new Project class instance, append it to the list of
        projects that this solution is managing.

        Args:
            self: The "this" reference.
            project: Reference to an instance of a Project.
            project_type: Type of project to create.
        """

        if project is None or is_string(project):
            project = Project(project, project_type=project_type)

        # Sanity check
        if not isinstance(project, Project):
            raise TypeError(
                "parameter \"project\" must be of type Project or name")

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
        @details
        Create a flattened list by iterating over every sub project.

        Returns:
            List of every project in the project.
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
        # pylint: disable=too-many-branches

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
        import makeprojects.codewarrior
        import makeprojects.xcode
        import makeprojects.codeblocks

        generator_list = (
            makeprojects.visual_studio,
            makeprojects.watcom,
            makeprojects.makefile,
            makeprojects.codewarrior,
            makeprojects.xcode,
            makeprojects.codeblocks)
        for generator in generator_list:
            if ide in generator.SUPPORTED_IDES:
                break
        else:
            print("IDE {} is not supported.".format(ide))
            return 10

        # Convert keys that need to be regexes from *.cpp to regex
        solution.custom_rules = regex_dict(solution.custom_rules)

        all_configurations_list = []

        last_failed = None
        # Process all the projects and configurations
        for project in solution.get_project_list():

            # Handle projects
            project.custom_rules = regex_dict(project.custom_rules)

            # Purge unsupported configurations
            configuration_list = []
            if not project.configuration_list:
                for item in ("Debug", "Release"):
                    project.add_configuration(item, project.platform)

            for configuration in project.configuration_list:
                if generator.test(ide, configuration.platform):
                    configuration_list.append(configuration)
                else:
                    last_failed = configuration.platform

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

        # No configurations passed? Abort
        if not configuration_list:
            print(
                "Generator for IDE \"{}\" is incompatible with platform \"{}\"".format(
                    ide, last_failed))
            return 10

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
        for item in self.__dict__.items():
            if item[0] == "parent":
                continue
            item_name = item[0][1:] if item[0].startswith("_") else item[0]
            result_list.append(
                "{0}: {1!s}".format(
                    item_name,
                    item[1]))
        return "Solution: " + ", ".join(result_list)

    def __str__(self):
        """
        Convert the solultion record into a human readable description

        Returns:
            Human readable string or None if the solution is invalid
        """

        return self.__repr__()
