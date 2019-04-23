#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Remove all temporary files in a project's folder.

Scan the current directory for the file build_rules.py and look for
the function ``clean_rules`` and call it.

This is the default function prototype for directory cleaning. It will
only be called in the directory that the file build_rules.py resides.
@code
def clean_rules(working_directory):
    return 0
@endcode

This version will be called from any directory, it's preferred for generic
cleaning functions that check for specific files for removal.
@code
def clean_rules(working_directory=None):
    return 0
@endcode

This version will be called from a specific directory. It's useful for generic
cleaning functions that are limited to a specific folder.
@code
def clean_rules(working_directory='C:\\projects\\mygreatapplication'):
    return 0
@endcode

If the parameter ``root`` exists, the default parameter will be checked for ``True`` to determine
if this cleaning function is the last one to execute and no more build_rules.py files will
be searched for. The value ``root`` is not set by cleanme and is not expected to be used by
``clean_rules``.
@code
def clean_rules(working_directory, root=True):
    return 0
@endcode

See:
    main(), makeprojects.buildme, makeprojects.rebuildme

"""

## \package makeprojects.cleanme

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import argparse
import re
from funcsigs import signature, Parameter
import burger
from .config import BUILD_RULES, DEFAULT_BUILD_RULES
from .__pkginfo__ import VERSION

## Match *.xcodeproj
_XCODEPROJ_MATCH = re.compile('(?ms).*\\.xcodeproj\\Z')

########################################


def dispatch(file_name, working_dir, args):
    """
    Dispatch to ``clean_rules``.

    Dispatch to the build_rules.py file to the cleanme
    function of ``clean_rules`` and return the error code
    if found. If the parameter ``root`` was found in the
    parameter list, check if the default argument is ``True`` to abort after execution.

    Args:
        file_name: full path of the build_rules.py file
        working_dir: path of the directory to pass to the ``clean_rules`` function
        args: Args for determining verbosity for output

    Returns:
        Zero on no error, non zero integer on error

    """

    # pylint: disable=R0912

    build_rules = burger.import_py_script(file_name)
    if build_rules:
        if args.verbose:
            print('Using configuration file {}'.format(file_name))

        # Perform the clean on this folder, if there's a clean function
        clean_rules = getattr(build_rules, 'clean_rules', None)
        if clean_rules:

            # Get the function signature
            sig = signature(clean_rules)

            parm_root = sig.parameters.get('root')
            if parm_root:
                if parm_root.default is True:
                    args.version = True

            # Test for working directory
            parm_working_directory = sig.parameters.get('working_directory')
            if not parm_working_directory:
                if args.verbose:
                    print('function clean_rules() doesn\'t have a parameter for '
                          'working_directory ')
                return 10

            if parm_working_directory.default is Parameter.empty:
                temp_dir = os.path.dirname(file_name)
            else:
                temp_dir = parm_working_directory.default
            if temp_dir:
                if working_dir != temp_dir:
                    if args.verbose:
                        print(
                            'function clean_rules() not called due to directory mismatch. '
                            'Expected {}, found {}'.format(
                                temp_dir, working_dir))
                    return 0

            # pylint: disable=E1102
            return clean_rules(working_directory=working_dir)
    return 0

########################################


def process(working_dir, args):
    """
    Clean a specific directory.

    Args:
        working_dir: path of the directory to pass to the ``clean_rules`` function
        args: Args for determining verbosity for output
    Returns:
        Zero on no error, non zero integer on error
    """

    # pylint: disable=R0912

    if args.verbose:
        print('Cleaning "{}".'.format(working_dir))

    # Simplest method, a hard coded rules file
    if args.rules_file:
        error = dispatch(os.path.abspath(args.rules_file), working_dir, args)
    else:

        # No files aborted
        args.version = False
        # Load the configuration file at the current directory
        temp_dir = working_dir
        while True:
            error = dispatch(os.path.join(temp_dir, BUILD_RULES), working_dir, args)
            # Abort on error
            if error:
                break
            # Abort on ROOT = True
            if args.version:
                break

            # Pop a folder to check for higher level build_rules.py
            temp_dir2 = os.path.dirname(temp_dir)
            # Already at the top of the directory?
            if temp_dir2 is None or temp_dir2 == temp_dir:
                error = dispatch(DEFAULT_BUILD_RULES, working_dir, args)
                if error:
                    return error
                break
            # Use the new folder
            temp_dir = temp_dir2

    # If recursive, process all the sub folders
    if args.recursive and not error:
        # Iterate over the directory
        for item in os.listdir(working_dir):

            # Ignore xcode project directories
            if _XCODEPROJ_MATCH.match(item):
                continue

            path_name = os.path.join(working_dir, item)
            if os.path.isdir(path_name):
                error = process(path_name, args)
                if error:
                    break

    return error

########################################


def main(working_dir=None, args=None):
    """
    Command line shell for ``cleanme``.

    Entry point for the program ``cleanme``, this function
    will either get the parameters from sys.argv or the paramater ``args``.

    - ``--version``, show version.
    - ``-r``, Perform a recursive clean.
    - ``-v``, Verbose output.
    - ``--generate-rules``, Create build_rules.py in the working directory and exit.
    - ``--rules-file``, Override the configruration file.
    - ``-d``, List of directories to clean.

    Args:
        working_dir: Directory to operate on, or None for os.getcwd()
        args: Command line to use instead of sys.argv
    Returns:
        Zero on no error, non-zero on error
    """

    # Make sure working_dir is properly set
    if working_dir is None:
        working_dir = os.getcwd()

    # Parse the command line
    parser = argparse.ArgumentParser(
        description='Remove project output files. '
        'Copyright by Rebecca Ann Heineman')

    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + VERSION)
    parser.add_argument('-r', '-all', dest='recursive', action='store_true',
                        default=False, help='Perform a recursive clean')
    parser.add_argument('-v', '-verbose', dest='verbose', action='store_true',
                        default=False, help='Verbose output.')
    parser.add_argument('--generate-rules', dest='generate_build_rules',
                        action='store_true', default=False,
                        help='Generate a sample configuration file and exit.')
    parser.add_argument('--rules-file', dest='rules_file',
                        metavar='<file>', default=None, help='Specify a configuration file.')
    parser.add_argument('-d', dest='directories', action='append',
                        metavar='<directory>', default=[],
                        help='List of directories to clean.')

    # Parse everything
    args = parser.parse_args(args=args)

    # Output default configuration
    if args.generate_build_rules:
        from .config import savedefault
        if args.verbose:
            print('Saving {}'.format(os.path.join(working_dir, 'build_rules.py')))
        savedefault(working_dir)
        return 0

    # Make a list of directories to process
    if not args.directories:
        args.directories = [working_dir]

    # Clean the directories
    for item in args.directories:
        error = process(os.path.abspath(item), args)
        if error:
            break

    # Wrap up!
    if args.verbose:
        print('cleanme is complete.')
    return error


# If called as a function and not a class,
# call my main

if __name__ == "__main__":
    sys.exit(main())
