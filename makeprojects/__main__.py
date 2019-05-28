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
"""

## \package makeprojects.__main__

from __future__ import absolute_import, print_function, unicode_literals

import sys
import os
import argparse
import json
from funcsigs import signature
import burger

from .core import Solution, Project, Configuration
from .config import BUILD_RULES, DEFAULT_BUILD_RULES
from .__pkginfo__ import VERSION
from .defaults import get_project_name, get_ide_list, get_platform_list, fixup_ide_platform
from. defaults import get_project_type, get_configuration_list

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

    if args.verbose:
        print('Using configuration file {}'.format(file_name))

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
    return True

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
            add_build_rules(build_rules_list, os.path.join(temp_dir, BUILD_RULES), args)
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
    project_type = get_project_type(build_rules_list, working_directory, args)

    # Determine the list of IDEs to generate projects for.
    ide_list = get_ide_list(build_rules_list, working_directory, args)

    # Determine the list of platforms to generate projects for.
    platform_list = get_platform_list(build_rules_list, working_directory, args)

    fixup_ide_platform(ide_list, platform_list)

    # For every IDE, generate the requested project.
    for ide in ide_list:

        # Start with the solution
        solution = Solution(
            project_name,
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

            # Create the configurations for this platform
            configuration_list = get_configuration_list(
                build_rules_list, working_directory, args, platform, ide)
            for item in platform.get_expanded():
                for config_name in configuration_list:
                    configuration = Configuration(config_name, platform=item)
                    project.add_configuration(configuration)
                    configuration.get_attributes(build_rules_list, working_directory)

        print(solution)


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
        print('Fatal error, no build_rules.py exist anywhere.')
        return 10

    #get_project_list(args, build_rules_list, working_directory)
    #return 0
    # Create a blank solution

    solution = Solution(
        os.path.basename(working_directory),
        working_directory=working_directory,
        verbose=args.verbose)
    project = Project()
    solution.add_project(project)

    #return 0
    # Process it
    #if args.test:
    #    return process(solution, args)
    #return process(solution, args)
    #
    # No input file?
    #

    if args.jsonfiles is None:
        if args.args:
            args.jsonfiles = args.args
        else:
            projectpathname = os.path.join(working_directory, 'projects.json')
            if os.path.isfile(projectpathname) is True:
                args.jsonfiles = ['projects.json']
            else:
                return solution.processcommandline(args)

    #
    # Read in the json file
    #

    for jsonarg in args.jsonfiles:
        projectpathname = os.path.join(working_directory, jsonarg)
        if not os.path.isfile(projectpathname):
            print(jsonarg + ' was not found')
            return 2

        #
        # To allow '#' and '//' comments, the file has to be pre-processed
        #

        fileref = open(projectpathname, 'r')
        jsonlines = fileref.readlines()
        fileref.close()

        #
        # Remove all lines that have a leading '#' or '//'
        #

        pure = ''
        for item in jsonlines:
            cleanitem = item.lstrip()
            if cleanitem.startswith('#') or cleanitem.startswith('//'):
                # Insert an empty line so that line numbers still match on error
                pure = pure + '\n'
            else:
                pure = pure + item

        #
        # Parse the json file (Handle errors)
        #

        try:
            myjson = json.loads(pure)
        except (ValueError, TypeError) as error:
            print('{} in parsing {}'.format(error, projectpathname))
            return 2

        #
        # Process the list of commands
        #

        if isinstance(myjson, list):
            error = solution.process(myjson)
        else:
            print('Invalid json input file!')
            error = 2
        if error != 0:
            break
    return error

########################################


def main(working_directory=None, args=None):
    """
    Main entry point when invoked as a tool.

    When makeprojects is invoked as a tool, this main() function
    is called with the current working directory. Arguments will
    be obtained using the argparse class.

    Args:
        working_directory: Directory to operate on, or ``None`` for ``os.getcwd()``.
        args: Command line to use instead of ``sys.argv``.
    Returns:
        Zero if no error, non-zero on error

    """

    # Make sure working_directory is properly set
    if working_directory is None:
        working_directory = os.getcwd()

    # Parse the command line
    parser = argparse.ArgumentParser(
        prog='makeprojects',
        description='Make project files. Copyright by Rebecca Ann Heineman. '
        'Creates files for XCode, Visual Studio, CodeBlocks, Watcom, make, Codewarrior...')

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + VERSION)
    parser.add_argument('-v', '-verbose', dest='verbose', action='store_true',
                        default=False, help='Verbose output.')
    parser.add_argument('--generate-rules', dest='generate_build_rules',
                        action='store_true', default=False,
                        help='Generate a sample configuration file and exit.')
    parser.add_argument('--rules-file', dest='rules_file',
                        metavar='<file>', default=None, help='Specify a configuration file.')
    parser.add_argument('-d', dest='directories', action='append',
                        metavar='<directory>',
                        help='Directorie(s) to create projects in.')
    parser.add_argument('-c', dest='configurations', action='append',
                        metavar='<configuration>',
                        help='Configuration(s) to create.')
    parser.add_argument('-i', dest='ides', action='append',
                        metavar='<IDE>', default=[],
                        help='IDE(s) to generate for.')
    parser.add_argument('-p', dest='platforms', action='append',
                        metavar='<platform>', default=[],
                        help='Platform(s) to create.')

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

    parser.add_argument('-codeblocks', dest='codeblocks', action='store_true',
                        default=False, help='Build for CodeBlocks 16.01')
    parser.add_argument('-codewarrior', dest='codewarrior', action='store_true',
                        default=False, help='Build for Metrowerks / Freescale CodeWarrior')
    parser.add_argument('-watcom', dest='watcom', action='store_true',
                        default=False, help='Build for Watcom WMAKE')
    parser.add_argument('-linux', dest='linux', action='store_true',
                        default=False, help='Build for Linux make')
    parser.add_argument('-ios', dest='ios', action='store_true',
                        default=False, help='Build for iOS with XCode 5 or higher.')
    parser.add_argument('-vita', dest='vita', action='store_true',
                        default=False, help='Build for PS Vita with Visual Studio 2010.')
    parser.add_argument('-360', dest='xbox360', action='store_true',
                        default=False, help='Build for XBox 360 with Visual Studio 2010.')
    parser.add_argument('-wiiu', dest='wiiu', action='store_true',
                        default=False, help='Build for WiiU with Visual Studio 2013.')
    parser.add_argument('-dsi', dest='dsi', action='store_true',
                        default=False, help='Build for Nintendo DSI with Visual Studio 2015.')

    parser.add_argument('-finalfolder', dest='deploy_folder', action='store_true',
                        default=False,
                        help='Add a script to copy a release build to a '
                        'folder and check in with Perforce')
    parser.add_argument('-app', dest='app', action='store_true',
                        default=False, help='Build an application instead of a tool')
    parser.add_argument('-lib', dest='library', action='store_true',
                        default=False, help='Build a library instead of a tool')

    parser.add_argument('-f', dest='jsonfiles',
                        action='append', help='Input file to process')
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help='project filenames')

    # Parse everything
    args = parser.parse_args()

    # Output default configuration
    if args.generate_build_rules:
        from .config import savedefault
        if args.verbose:
            print('Saving {}'.format(os.path.join(working_directory, 'build_rules.py')))
        savedefault(working_directory)
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
