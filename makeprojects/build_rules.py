#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration file on how to build and clean projects in a specific folder.

This file is parsed by the cleanme, buildme, rebuildme and makeprojects
command line tools to clean, build and generate project files.
"""

from __future__ import absolute_import, print_function, unicode_literals

import sys
import os

from makeprojects.enums import PlatformTypes, IDETypes

########################################


def rules(command, working_directory, root=True, **kargs):
    """
    Main entry point for build_rules.py.

    When makeprojects, cleanme, or buildme is executed, they will call this
    function to perform the actions required for build customization.

    The parameter working_directory is required, and if it has no default
    parameter, this function will only be called with the folder that this
    file resides in. If there is a default parameter of None, it will be called with
    any folder that it is invoked on. If the default parameter is a directory, this
    function will only be called if that directory is desired.

    The optional parameter of root alerts the tool if subsequent processing of other
    build_rules.py files are needed or if set to have a default parameter of True, processing
    will end once the calls to this rules() function are completed.

    Commands are 'build', 'clean', 'prebuild', 'postbuild', 'project', 'configurations'

    Arg:
        command: Command to execute.
        working_directory: Directory for this function to clean
        root: If set to True, exit cleaning upon completion of this function
    Return:
        Zero on success, non-zero on failure, and a list for 'configurations'

    """

    # The command clean will clean the current directory of any
    # files that aren't cleaned by IDE project files.
    if command == 'clean':
        # Call functions to delete files and / or folders
        pass

    elif command == 'prebuild':
        # Perform actions before building any IDE based projects
        pass

    elif command == 'build':
        # Perform actions to build
        pass

    elif command == 'postbuild':
        # Perform actions after all IDE based projects
        pass

    elif command == 'generate':
        # Perform project generation instead of the automatic system
        pass

    elif command == 'default_platform_ide':
        pass

    elif command == 'configuration_list':
        # Return the list of default configurations
        results = [
            'Debug',
            'Internal',
            'Release'
        ]
        if kargs.get('platform', None) == PlatformTypes.xbox360:
            results.extend([
                'Profile',
                'Release_LTCG',
                'CodeAnalysis',
                'Profile_FastCap'
            ])
        return results

    elif command == 'configuration_settings':
        # Return the settings for a specific project
        pass

    return 0


# If called as a command line and not a class, perform the build
if __name__ == "__main__":
    sys.exit(rules('build', os.path.dirname(os.path.abspath(__file__))))
