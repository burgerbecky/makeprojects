#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains the code to generate defaults.
"""

## \package makeprojects.defaults
# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

from burger import convert_to_array

from .enums import IDETypes, PlatformTypes, ProjectTypes
from .build_rules import rules as default_rules

## Default settings for each configuration type
# Each key must be lower case
_CONFIGURATION_DEFAULTS = {
    'debug': {
        'short_code': 'dbg',
        'debug': True},
    'internal': {
        'short_code': 'int',
        'optimization': 4,
        'debug': True},
    'release': {
        'short_code': 'rel',
        'optimization': 4},
    'release_ltcg': {
        'short_code': 'ltc',
        'optimization': 4,
        'link_time_code_generation': True},
    'profile': {
        'short_code': 'pro',
        'optimization': 4,
        'profile': True},
    'profile_fastcap': {
        'short_code': 'fas',
        'optimization': 4,
        'profile': 'fast'},
    'codeanalysis': {
        'short_code': 'cod',
        'analyze': True}
}

########################################


def get_configuration_settings(name, setting_name=None):
    """
    Given a configuration name, return default settings.

    Default names are Debug, Internal, Release, Release_LTCG,
    Profile, Profile_FastCap and CodeAnalysis.

    Args:
        name: Name of the configuration
        setting_name: Default settings name override.
    Return:

    """

    # No override?
    if setting_name is None:
        setting_name = name

    # Case insensitive test
    test_lower = setting_name.lower()
    settings = _CONFIGURATION_DEFAULTS.get(test_lower, None)

    # Set up the configuration name
    if settings:

        # Use a copy
        settings = settings.copy()

        # Override the name
        settings['name'] = name
    return settings


########################################


def get_project_name(build_rules_list, working_directory, args):
    """
    Determine the project name.

    Scan the build_rules.py file for the command 'default_project_name'
    and if found, use that string for the project name. Otherwise,
    use the name of the working folder.

    Args:
        build_rules_list: List to append a valid build_rules file instance.
        working_directory: Full path name of the build_rules.py to load.
        args: Args for determining verbosity for output.

    Returns:
        Name of the project.
    """

    project_name = args.name
    if not project_name:
        # Check build_rules.py
        for rules in build_rules_list:
            project_name = rules(
                'default_project_name',
                working_directory=working_directory)
            if project_name:
                break
        else:
            # Use the default
            project_name = default_rules(
                'default_project_name', working_directory)

    # Print if needed.
    if args.verbose:
        print("Project name is {}".format(project_name))
    return project_name

########################################


def get_project_type(build_rules_list, working_directory, args, project_name):
    """
    Determine the project type.

    Scan the build_rules.py file for the command 'default_project_type'
    and if found, use that string for the project type. Otherwise,
    assume it's a command line tool.

    Args:
        build_rules_list: List to append a valid build_rules file instance.
        working_directory: Full path name of the build_rules.py to load.
        args: Args for determining verbosity for output.
        project_name: Name of the project being built.

    Returns:
        ProjectTypes enumeration.
    """

    project_type = args.project_type
    if project_type:
        project_type = ProjectTypes.lookup(project_type)

    if not isinstance(project_type, ProjectTypes):
        # Check build_rules.py
        for rules in build_rules_list:
            item = rules(
                'default_project_type',
                working_directory=working_directory,
                project_name=project_name)

            # Is it a ProjectTypes?
            if isinstance(item, ProjectTypes):
                project_type = item
                break

            # Try string lookup
            if item != 0:
                project_type = ProjectTypes.lookup(item)
                if project_type is not None:
                    break
                print('Project Type {} is not supported.'.format(item))
        else:
            # Use the default
            project_type = default_rules(
                'default_project_type', working_directory)

    # Print if needed.
    if args.verbose:
        print("Project type is {}".format(str(project_type)))
    return project_type

########################################


def get_ide_list(build_rules_list, working_directory, args):
    """
    Determine the IDEs to generate projects for.

    Scan the build_rules.py file for the command 'default_ide'
    and if found, use that list of IDETypes or strings to lookup with
    IDETypes.lookup().

    Args:
        build_rules_list: List to append a valid build_rules file instance.
        working_directory: Full path name of the build_rules.py to load.
        args: Args for determining verbosity for output.

    Returns:
        List of IDEs to generate projects for.
    """

    # Get the IDE list from the command line
    temp_list = args.ides
    if not temp_list:
        for rules in build_rules_list:
            default = rules('default_ide', working_directory=working_directory)
            # Check if it's a single IDETypes enum
            if isinstance(default, IDETypes):
                # Convert to a list
                temp_list = [default]
                break

            if default != 0:
                # Assume it's a single string or a list of strings.
                temp_list = convert_to_array(default)
                break

    # Convert strings to IDETypes.
    ide_list = []
    for item in temp_list:
        ide_type = IDETypes.lookup(item)
        if ide_type is None:
            print('IDE {} is not supported.'.format(item))
        else:
            ide_list.append(ide_type)

    # Print if needed.
    if args.verbose:
        if ide_list:
            print("IDE name {}".format(ide_list))
        else:
            print("Using default IDE")

    return ide_list

########################################


def get_platform_list(build_rules_list, working_directory, args):
    """
    Determine the platforms to generate projects for.

    Scan the build_rules.py file for the command 'default_platform'
    and if found, use that list of PlatformTypes or strings to lookup with
    PlatformTypes.lookup().

    Args:
        build_rules_list: List to append a valid build_rules file instance.
        working_directory: Full path name of the build_rules.py to load.
        args: Args for determining verbosity for output.

    Returns:
        List of platforms to generate projects for.
    """

    # Add the build platforms
    temp_list = args.platforms
    if not temp_list:
        for rules in build_rules_list:
            default = rules(
                'default_platform',
                working_directory=working_directory)
            # Check if it's a single PlatformTypes enum
            if isinstance(default, PlatformTypes):
                # Convert to a list
                temp_list = [default]
                break

            if default != 0:
                # Assume it's a single string or a list of strings.
                temp_list = convert_to_array(default)
                break

    # Convert strings to PlatformTypes.
    platform_list = []
    for item in temp_list:
        platform_type = PlatformTypes.lookup(item)
        if platform_type is None:
            print('Platform {} is not supported.'.format(item))
        else:
            platform_list.append(platform_type)

    # Print if needed.
    if args.verbose:
        if platform_list:
            print("Platform name {}".format(platform_list))
        else:
            print("Using default platform")

    return platform_list

########################################


def get_configuration_list(
        build_rules_list, working_directory, args, platform, ide):
    """
    Determine the configurations to generate projects for.

    Scan the build_rules.py file for the command 'configuration_list'
    and if found, use that list of strings to create configurations.

    Args:
        build_rules_list: List to append a valid build_rules file instance.
        working_directory: Full path name of the build_rules.py to load.
        args: Args for determining verbosity for output.
        platform: Platform building.
        ide: IDETypes for the ide generating for.

    Returns:
        List of configuration strings to generate projects for.
    """

    # Too many branches
    # pylint: disable=R0912

    # Create the configurations for this platform
    if args.configurations:
        configuration_list = []
        for configuration in args.configurations:
            item = get_configuration_settings(configuration)
            if item:
                configuration_list.append(item)
                break
            else:
                print(('configuration {} is not found in the '
                       'acceptable name list.').format(
                           configuration))
    else:
        for rules in build_rules_list:
            configuration_list = rules('configuration_list',
                                       working_directory=working_directory,
                                       platform=platform,
                                       ide=ide)
            if configuration_list != 0:
                break
        else:
            configuration_list = default_rules(
                'configuration_list',
                working_directory=working_directory,
                platform=platform,
                ide=ide)

    return configuration_list

########################################


def fixup_ide_platform(ide_list, platform_list):
    """
    Fix empty IDE/Platform lists.

    Given a list of IDEs and Platforms, determine what should be the defaults
    in case one or both of the lists are empty.

    Args:
        ide_list: List of IDEs to generate for.
        platform_list: List of platforms to build for.
    """

    # Too many branches
    # pylint: disable=R0912

    # If no platform and IDE were selected, use the system defaults
    if not platform_list and not ide_list:
        platform_list.append(PlatformTypes.default())
        ide_list.append(IDETypes.default())

    # If no platform was selected, but and IDE was, choose
    # the host machine as the platform.
    elif not platform_list:
        platform_list.append(PlatformTypes.default())

    # No IDE selected?
    elif not ide_list:
        # Platform without an IDE is tricky, because video game platforms
        # are picky.
        if PlatformTypes.xbox in platform_list:
            ide_list.append(IDETypes.vs2003)

        elif PlatformTypes.xbox360 in platform_list:
            ide_list.append(IDETypes.vs2010)

        elif PlatformTypes.xboxone in platform_list:
            ide_list.append(IDETypes.vs2017)

        elif PlatformTypes.ps3 in platform_list:
            ide_list.append(IDETypes.vs2015)

        elif PlatformTypes.ps4 in platform_list:
            ide_list.append(IDETypes.vs2015)

        elif PlatformTypes.vita in platform_list:
            ide_list.append(IDETypes.vs2015)

        elif PlatformTypes.shield in platform_list:
            ide_list.append(IDETypes.vs2015)

        elif PlatformTypes.wiiu in platform_list:
            ide_list.append(IDETypes.vs2015)

        elif PlatformTypes.switch in platform_list:
            ide_list.append(IDETypes.vs2017)

        elif PlatformTypes.android in platform_list:
            ide_list.append(IDETypes.vs2022)

        # Unknown, punt on the IDE
        else:
            ide_list.append(IDETypes.default())
