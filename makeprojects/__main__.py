#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains the code for the command line "makeprojects".

Scan the current directory and generate one or more project files
based on the source code found.

If build_rules.py is found, it will be scanned for information on how
to generate the IDE for different platforms and configurations if needed.

See Also:
    makeprojects.cleanme, makeprojects.buildme, makeprojects.rebuildme

@package makeprojects.__main__
"""

# pylint: disable=consider-using-f-string

from __future__ import absolute_import, print_function, unicode_literals

import sys
import os
import argparse
from funcsigs import signature
import burger

from .core import Solution, Project, Configuration
from .config import BUILD_RULES_PY, DEFAULT_BUILD_RULES
from .__init__ import __version__
from .defaults import get_project_name, get_ide_list, get_platform_list, \
    fixup_ide_platform, get_project_type, get_configuration_list

########################################


def add_build_rules(build_rules_list, file_name, args):
    """
    Load in the file build_rules.py

    Load the build_rules.py file. If the parameter ``root`` was found in the
    parameter list of the function project_rules, check if the default argument
    is ``True`` to abort after execution.

    Args:
        build_rules_list: List to append a valid build_rules file instance.
        file_name: Full path name of the build_rules.py to load.
        args: Args for determining verbosity for output.
    Returns:
        Zero on no error, non zero integer on error
    """

    # Test if there is a specific build rule
    file_name = os.path.abspath(file_name)
    build_rules = burger.import_py_script(file_name)
    if not build_rules:
        return False

    # Find the entry point
    rules = getattr(build_rules, 'rules', None)
    if rules:

        # Get the function signature
        sig = signature(rules)

        parm_root = sig.parameters.get('root')
        if parm_root:
            if parm_root.default is True:
                args.version = True
        build_rules_list.append(rules)
        if args.verbose:
            print('Using configuration file {}'.format(file_name))
        return True
    return False

########################################


def get_build_rules(working_directory, args):
    """
    Process a solution.

    Args:
        working_directory: Directory to scan for build_rules.py
        args: Args for determining verbosity for output
    Returns:
        List of loaded build_rules.py files.
    """

    # Test if there is a specific build rule
    build_rules_list = []
    if args.rules_file:
        add_build_rules(build_rules_list, args.rules_file, args)
    else:
        # No files aborted
        args.version = False
        # Load the configuration file at the current directory
        temp_dir = working_directory
        while True:
            add_build_rules(
                build_rules_list, os.path.join(
                    temp_dir, BUILD_RULES_PY), args)
            # Abort on ROOT = True
            if args.version:
                break

            # Pop a folder to check for higher level build_rules.py
            temp_dir2 = os.path.dirname(temp_dir)
            # Already at the top of the directory?
            if temp_dir2 is None or temp_dir2 == temp_dir:
                add_build_rules(build_rules_list, DEFAULT_BUILD_RULES, args)
                break
            # Use the new folder
            temp_dir = temp_dir2
    return build_rules_list


########################################

def get_project_list(args, build_rules_list, working_directory):
    """
    From the command line or the build rules, determine the project target list.
    """

    # Start with determining the project name
    project_name = get_project_name(build_rules_list, working_directory, args)

    # Determine the project type
    project_type = get_project_type(
        build_rules_list,
        working_directory,
        args,
        project_name)

    # Determine the list of IDEs to generate projects for.
    ide_list = get_ide_list(build_rules_list, working_directory, args)

    # Determine the list of platforms to generate projects for.
    platform_list = get_platform_list(build_rules_list, working_directory, args)

    # If a platform was chosen, but not an IDE, choose the proper IDE for
    # that platform
    fixup_ide_platform(ide_list, platform_list)

    # For every IDE, generate the requested project.
    for ide in ide_list:

        # Start with the solution
        solution = Solution(
            name=project_name,
            verbose=args.verbose,
            working_directory=working_directory,
            ide=ide)

        for platform in platform_list:
            project = Project(
                name=project_name,
                project_type=project_type,
                working_directory=working_directory,
                platform=platform)

            solution.add_project(project)
            project.parse_attributes(build_rules_list, working_directory)

            # Add all the configurations
            for platform_item in platform.get_expanded():
                # Create the configurations for this platform
                for config_item in get_configuration_list(
                        build_rules_list, working_directory, args,
                        platform_item, ide):

                    # Set the platform
                    config_item['platform'] = platform_item
                    configuration = Configuration(**config_item)
                    project.add_configuration(configuration)
                    configuration.parse_attributes(
                        build_rules_list, working_directory)

            # Perform the generation
            solution.generate(ide)
            # Reset the solution
            solution.project_list = []
    return 0


########################################


def process(working_directory, args):
    """
    Process a solution.

    Args:
        working_directory: Directory to process.
        args: Args for determining verbosity for output
    Returns:
        Zero on no error, non zero integer on error
    """

    if args.verbose:
        print('Making "{}".'.format(working_directory))

    # Find the build_rules.py file
    build_rules_list = get_build_rules(working_directory, args)
    if not build_rules_list:
        print('Fatal error, no ' + BUILD_RULES_PY + ' exist anywhere.')
        return 10

    return get_project_list(args, build_rules_list, working_directory)

########################################


def main(working_directory=None, args=None):
    """
    Main entry point when invoked as a tool.

    When makeprojects is invoked as a tool, this main() function
    is called with the current working directory. Arguments will
    be obtained using the argparse class.

    Args:
        working_directory: Directory to operate on or None.
        args: Command line to use instead of ``sys.argv``.
    Returns:
        Zero if no error, non-zero on error

    """

    # Too many statements
    # pylint: disable=R0915

    # Make sure working_directory is properly set
    if working_directory is None:
        working_directory = os.getcwd()

    # Parse the command line
    parser = argparse.ArgumentParser(
        prog='makeprojects', description=(
            'Make project files. Copyright by Rebecca Ann Heineman. '
            'Creates files for XCode, Visual Studio, '
            'CodeBlocks, Watcom, make, Codewarrior...'))

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)
    parser.add_argument('-v', '-verbose', dest='verbose', action='store_true',
                        default=False, help='Verbose output.')
    parser.add_argument('--generate-rules', dest='generate_build_rules',
                        action='store_true', default=False,
                        help='Generate a sample configuration file and exit.')
    parser.add_argument(
        '--rules-file',
        dest='rules_file',
        metavar='<file>',
        default=None,
        help='Specify a configuration file.')
    parser.add_argument('-d', dest='directories', action='append',
                        metavar='<directory>',
                        help='Directorie(s) to create projects in.')
    parser.add_argument('-c', dest='configurations', action='append',
                        metavar='<configuration>',
                        help='Configuration(s) to create.')
    parser.add_argument('-g', dest='ides', action='append',
                        metavar='<IDE>', default=[],
                        help='IDE(s) to generate for.')
    parser.add_argument('-p', dest='platforms', action='append',
                        metavar='<platform>', default=[],
                        help='Platform(s) to create.')
    parser.add_argument('-n', dest='name', action='store',
                        metavar='<name>', default=[],
                        help='Name of the project create.')
    parser.add_argument('-t', dest='project_type', action='store',
                        metavar='<project type>', default=[],
                        help='Type of project to create.')

    parser.add_argument('-xcode3', dest='xcode3', action='store_true',
                        default=False, help='Build for Xcode 3.')
    parser.add_argument('-xcode4', dest='xcode4', action='store_true',
                        default=False, help='Build for Xcode 4.')
    parser.add_argument('-xcode5', dest='xcode5', action='store_true',
                        default=False, help='Build for Xcode 5.')
    parser.add_argument('-xcode6', dest='xcode6', action='store_true',
                        default=False, help='Build for Xcode 6.')
    parser.add_argument('-xcode7', dest='xcode7', action='store_true',
                        default=False, help='Build for Xcode 7.')
    parser.add_argument('-xcode8', dest='xcode8', action='store_true',
                        default=False, help='Build for Xcode 8.')
    parser.add_argument('-xcode9', dest='xcode9', action='store_true',
                        default=False, help='Build for Xcode 9.')
    parser.add_argument('-xcode10', dest='xcode10', action='store_true',
                        default=False, help='Build for Xcode 10.')

    parser.add_argument('-vs2005', dest='vs2005', action='store_true',
                        default=False, help='Build for Visual Studio 2005.')
    parser.add_argument('-vs2008', dest='vs2008', action='store_true',
                        default=False, help='Build for Visual Studio 2008.')
    parser.add_argument('-vs2010', dest='vs2010', action='store_true',
                        default=False, help='Build for Visual Studio 2010.')
    parser.add_argument('-vs2012', dest='vs2012', action='store_true',
                        default=False, help='Build for Visual Studio 2012.')
    parser.add_argument('-vs2013', dest='vs2013', action='store_true',
                        default=False, help='Build for Visual Studio 2013.')
    parser.add_argument('-vs2015', dest='vs2015', action='store_true',
                        default=False, help='Build for Visual Studio 2015.')
    parser.add_argument('-vs2017', dest='vs2017', action='store_true',
                        default=False, help='Build for Visual Studio 2017.')
    parser.add_argument('-vs2019', dest='vs2019', action='store_true',
                        default=False, help='Build for Visual Studio 2019.')
    parser.add_argument('-vs2022', dest='vs2022', action='store_true',
                        default=False, help='Build for Visual Studio 2022.')

    parser.add_argument('-codeblocks', dest='codeblocks', action='store_true',
                        default=False, help='Build for CodeBlocks 16.01')
    parser.add_argument(
        '-codewarrior',
        dest='codewarrior',
        action='store_true',
        default=False,
        help='Build for Metrowerks / Freescale CodeWarrior')
    parser.add_argument('-watcom', dest='watcom', action='store_true',
                        default=False, help='Build for Watcom WMAKE')
    parser.add_argument('-linux', dest='linux', action='store_true',
                        default=False, help='Build for Linux make')
    parser.add_argument(
        '-ios',
        dest='ios',
        action='store_true',
        default=False,
        help='Build for iOS with XCode 5 or higher.')
    parser.add_argument(
        '-vita',
        dest='vita',
        action='store_true',
        default=False,
        help='Build for PS Vita with Visual Studio 2010.')
    parser.add_argument(
        '-360',
        dest='xbox360',
        action='store_true',
        default=False,
        help='Build for XBox 360 with Visual Studio 2010.')
    parser.add_argument(
        '-wiiu',
        dest='wiiu',
        action='store_true',
        default=False,
        help='Build for WiiU with Visual Studio 2013.')
    parser.add_argument(
        '-dsi',
        dest='dsi',
        action='store_true',
        default=False,
        help='Build for Nintendo DSI with Visual Studio 2015.')

    parser.add_argument(
        '-finalfolder',
        dest='deploy_folder',
        action='store_true',
        default=False,
        help='Add a script to copy a release build to a '
        'folder and check in with Perforce')
    parser.add_argument(
        '-app',
        dest='app',
        action='store_true',
        default=False,
        help='Build an application instead of a tool')
    parser.add_argument('-lib', dest='library', action='store_true',
                        default=False, help='Build a library instead of a tool')


    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help='project filenames')

    # Parse everything
    args = parser.parse_args(args=args)

    # Output default configuration
    if args.generate_build_rules:
        from .config import save_default
        if args.verbose:
            print(
                'Saving {}'.format(
                    os.path.join(
                        working_directory,
                        BUILD_RULES_PY)))
        save_default(working_directory)
        return 0

    # Make a list of directories to process
    if not args.directories:
        args.directories = (working_directory,)

    # Process the directories
    for item in args.directories:
        error = process(os.path.abspath(item), args)
        if error:
            break
    else:
        if args.verbose:
            print('Makeprojects successful!')
        error = 0

    return error


# If called as a function and not a class, call my main
if __name__ == '__main__':
    sys.exit(main())
