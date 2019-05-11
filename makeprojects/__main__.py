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

from .core import Solution
from .config import BUILD_RULES, DEFAULT_BUILD_RULES
from .__pkginfo__ import VERSION


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

    # Perform the clean on this folder, if there's a clean function
    project_rules = getattr(build_rules, 'project_rules', None)
    if project_rules:

        # Get the function signature
        sig = signature(project_rules)

        parm_root = sig.parameters.get('root')
        if parm_root:
            if parm_root.default is True:
                args.version = True
    build_rules_list.append(build_rules)
    return True

########################################


def get_build_rules(solution, args):
    """
    Process a solution.

    Args:
        solution: Solution instance to build from.
        args: Args for determining verbosity for output
    Returns:
        List of loaded build_rules.py files.
    """

    # Test if there is a specific build rule
    build_rules_list = []
    if args.rules_file:
        add_build_rules(build_rules_list, args.rules_file, args)
    else:
        working_dir = solution.working_dir
        # No files aborted
        args.version = False
        # Load the configuration file at the current directory
        temp_dir = working_dir
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


def process(solution, args):
    """
    Process a solution.

    Args:
        solution: Solution instance to build from.
        args: Args for determining verbosity for output
    Returns:
        Zero on no error, non zero integer on error
    """

    if args.verbose:
        print('Building "{}".'.format(solution.working_dir))

    build_rules = get_build_rules(solution, args)
    if not build_rules:
        print('Fatal error, no build_rules.py exists anywhere.')
        return 10

    # Build rules was found.
    for item in build_rules:
        print(item.__file__)
        print(str(dir(item)))

    return 0

########################################


def main(working_dir=None, args=None):
    """
    Main entry point when invoked as a tool.

    When makeprojects is invoked as a tool, this main() function
    is called with the current working directory. Arguments will
    be obtained using the argparse class.

    Args:
        working_dir: Directory to operate on, or ``None`` for ``os.getcwd()``.
        args: Command line to use instead of ``sys.argv``.
    Returns:
        Zero if no error, non-zero on error

    """

    # Make sure working_dir is properly set
    if working_dir is None:
        working_dir = os.getcwd()

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

    parser.add_argument('-release', dest='release', action='store_true',
                        default=False,
                        help='Create a release target (Default is release/debug/internal)')
    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Create a debug target')
    parser.add_argument('-internal', dest='internal', action='store_true',
                        default=False, help='Create an internal target')
    parser.add_argument('-finalfolder', dest='finalfolder', action='store_true',
                        default=False,
                        help='Add a script to copy a release build to a '
                        'folder and check in with Perforce')
    parser.add_argument('-app', dest='app', action='store_true',
                        default=False, help='Build an application instead of a tool')
    parser.add_argument('-lib', dest='library', action='store_true',
                        default=False, help='Build a library instead of a tool')

    parser.add_argument('-f', dest='jsonfiles',
                        action='append', help='Input file to process')

    parser.add_argument('-t', dest='test', action='store_true',
                        default=False,
                        help='Run new code')
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help='project filenames')

    # Parse everything
    args = parser.parse_args()

    # Output default configuration
    if args.generate_build_rules:
        from .config import savedefault
        if args.verbose:
            print('Saving {}'.format(os.path.join(working_dir, 'build_rules.py')))
        savedefault(working_dir)
        return 0

    # Create a blank solution
    solution = Solution()
    solution.verbose = args.verbose
    solution.workingDir = working_dir

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
            projectpathname = os.path.join(working_dir, 'projects.json')
            if os.path.isfile(projectpathname) is True:
                args.jsonfiles = ['projects.json']
            else:
                return solution.processcommandline(args)

    #
    # Read in the json file
    #

    for jsonarg in args.jsonfiles:
        projectpathname = os.path.join(working_dir, jsonarg)
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


# If called as a function and not a class, call my main
if __name__ == '__main__':
    sys.exit(main())
